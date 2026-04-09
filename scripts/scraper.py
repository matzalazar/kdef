"""
scraper.py — Descarga de materiales desde el Moodle de la UNDEF

Responsabilidad única: autenticarse en Moodle y descargar los archivos
de los cursos a un directorio temporal local.

Decisiones de diseño:
  - Session de requests persistente para manejar cookies de sesión de Moodle.
  - Moodle usa autenticación por formulario (logintoken + sesskey), no OAuth.
  - Los archivos se descargan a /tmp para no contaminar el repositorio con
    binarios — solo los .md generados entran al repo.
  - El scraper no sabe nada de LLMs ni de markdown — su única tarea es
    entregar Paths a archivos descargados.

La autenticación vive en auth.py para separar login/sesión del scraping.

Referencia: https://docs.moodle.org/dev/Web_service_API_functions
"""

import json
import logging
import tempfile
import mimetypes
import unicodedata
from urllib.parse import urlparse, unquote
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

try:
    from scripts.auth import create_moodle_session
except ImportError:  # pragma: no cover - fallback for direct script execution
    from auth import create_moodle_session

log = logging.getLogger(__name__)

# Timeout para requests HTTP — evita colgar el pipeline si Moodle no responde
HTTP_TIMEOUT_SECONDS = 30

# Extensiones de archivo que el pipeline sabe procesar
# Agregar más a medida que summarizer.py soporte más formatos
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md"}


def _base_url(moodle_url: str) -> str:
    """Strip trailing slash to avoid double-slash in constructed URLs."""
    return moodle_url.rstrip("/")


def _slugify(value: str) -> str:
    """Normalize a string to a URL-safe slug, stripping accents and special chars."""
    # Normalizar Unicode → ASCII para eliminar tildes y caracteres especiales
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned: list[str] = []
    for char in ascii_value.strip().lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_", "/", "\\"}:
            cleaned.append("-")
    slug = "".join(cleaned)
    while "--" in slug:
        slug = slug.replace("--", "-")
    # Trailing hyphens can appear from filenames that start/end with separators
    return slug.strip("-") or "item"


def _section_dirname(title: str) -> str:
    """
    Convertir el título de un tile/sección en nombre de directorio.

    Si el título contiene un rango de fechas (ej: "Semana 1 - 06/04 al 10/04"),
    extrae solo el rango en formato "dd-mm-a-dd-mm".
    Si no, aplica slugify normal.
    """
    import re
    match = re.search(r"(\d{1,2})[/\-](\d{1,2})\s+al\s+(\d{1,2})[/\-](\d{1,2})", title)
    if match:
        d1, m1, d2, m2 = match.groups()
        return f"{int(d1):02d}-{int(m1):02d}-a-{int(d2):02d}-{int(m2):02d}"
    return _slugify(title)


def _safe_name(value: str) -> str:
    """Collapse internal whitespace and return a non-empty string."""
    return " ".join(value.split()).strip() or "item"


def _extension_from_url(url: str) -> str:
    """Extract the file extension from a URL path, ignoring query strings."""
    parsed = urlparse(url)
    suffix = Path(unquote(parsed.path)).suffix.lower()
    return suffix


def _decode_mojibake(text: str) -> str:
    """Corregir nombres con encoding Latin-1 interpretado como UTF-8 (mojibake de Moodle).

    Moodle a veces envía el header Content-Disposition con bytes Latin-1
    sin encodear correctamente. Por ejemplo, "Presentación" llega como
    "PresentaciÃ³n". Este helper intenta revertirlo.
    """
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _filename_from_response(response: requests.Response, url: str) -> str:
    """Determine the filename for a downloaded file.

    Priority: Content-Disposition header → URL path → Content-Type guess.
    Applies mojibake correction in all cases.
    """
    disposition = response.headers.get("Content-Disposition", "")
    if "filename=" in disposition:
        raw = disposition.split("filename=", 1)[1].strip().strip('"').strip("'")
        return _decode_mojibake(unquote(raw))

    # response.url reflects the final URL after redirects, which is more reliable
    parsed = urlparse(response.url or url)
    name = Path(unquote(parsed.path)).name
    if name:
        return _decode_mojibake(name)

    guessed = mimetypes.guess_extension(response.headers.get("Content-Type", "").split(";", 1)[0].strip())
    return f"download{guessed or ''}"


def _resource_from_anchor(href: str, text: str) -> dict[str, str] | None:
    """Parse an anchor href into a resource dict, or None if not a downloadable activity."""
    if "/mod/resource/view.php" not in href and "/mod/folder/view.php" not in href:
        return None

    return {
        "name": _safe_name(text or "recurso"),
        "url": href,
        "extension": _extension_from_url(href),
        "kind": "activity",
    }


def _extract_section_number(url: str) -> str | None:
    """Extract the 'section' query param from a Moodle course URL."""
    parsed = urlparse(url)
    query = parsed.query
    for chunk in query.split("&"):
        if chunk.startswith("section="):
            value = chunk.split("=", 1)[1].strip()
            return value or None
    return None


def _is_restricted_tile(tile: BeautifulSoup) -> bool:
    """Return True if a Moodle tile element is access-restricted for the current user."""
    classes = tile.get("class", []) or []
    return "tile-restricted" in classes


def _tile_section_links(course_soup: BeautifulSoup) -> list[dict[str, str]]:
    """Return clickable section tiles from a Moodle Tiles course page."""
    tiles: list[dict[str, str]] = []
    seen_sections: set[str] = set()

    for tile in course_soup.select('li[id^="tile-"]'):
        if _is_restricted_tile(tile):
            continue

        link = tile.select_one('a.tile-link[href]')
        if link is None:
            continue

        href = link.get("href", "")
        section = _extract_section_number(href)
        if not section or section in seen_sections:
            continue

        seen_sections.add(section)
        title = " ".join(link.get_text(" ", strip=True).split())
        tiles.append({"section": section, "url": href, "title": title or f"sección {section}"})

    return tiles


def _extract_activity_links_from_soup(soup: BeautifulSoup, base_url: str) -> list[dict[str, str]]:
    """Collect candidate activity links and external links from a Moodle page."""
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    base_host = urlparse(base_url).netloc

    for a in soup.select('a[href]'):
        href = a.get("href", "")
        if not href or href.startswith(("#", "javascript:")):
            continue

        text = " ".join(a.get_text(" ", strip=True).split())
        final_name = _safe_name(text or Path(unquote(urlparse(href).path)).name or "recurso")
        ext = _extension_from_url(href)

        if href in seen:
            continue
        seen.add(href)

        if "/mod/" not in href and "/pluginfile.php" not in href and "/draftfile.php" not in href:
            parsed = urlparse(href)
            if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.netloc != base_host:
                links.append({"name": final_name, "url": href, "extension": ext, "kind": "link"})
            continue

        links.append({"name": final_name, "url": href, "extension": ext, "kind": "activity"})

    return links


def _course_title_from_page(soup: BeautifulSoup, course_id: str) -> str:
    """Extract the course title from a Moodle course page, falling back to the course ID."""
    heading = soup.select_one(".page-header-headings h1, h1")
    if heading:
        return _safe_name(heading.get_text(" ", strip=True))
    return f"curso-{course_id}"


def _section_title_from_page(soup: BeautifulSoup, section_number: str) -> str:
    """Extract a section title from its DOM container, falling back to section number."""
    heading = soup.select_one(f'#section-{section_number} .sectionname, #section-{section_number} .name, #section-{section_number} .contenttitle')
    if heading:
        return _safe_name(heading.get_text(" ", strip=True))
    return f"semana-{section_number}"


def _is_youtube_url(url: str) -> bool:
    """Return True if the URL points to YouTube or the youtu.be shortener."""
    host = urlparse(url).netloc.lower()
    return "youtube.com" in host or "youtu.be" in host


def _write_link_placeholder(
    dest_path: Path,
    *,
    title: str,
    url: str,
    course_title: str,
    section_title: str,
) -> Path:
    """Create a markdown note that preserves an external link in the tree."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    is_youtube = _is_youtube_url(url)
    content = f'''---
title: "{title}"
source_type: "link"
source_url: "{url}"
course_title: "{course_title}"
section_title: "{section_title}"
kdef_skip: true
kdef_kind: "{'youtube' if is_youtube else 'link'}"
---

- [{title}]({url})
'''
    dest_path.write_text(content, encoding="utf-8")
    return dest_path


def _resources_from_section_page(session: requests.Session, section_url: str, base_url: str) -> list[dict[str, str]]:
    """Fetch a section page and collect downloadable resources from it."""
    response = session.get(section_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    resources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    section_number = _extract_section_number(section_url)
    section_container = None
    if section_number:
        section_container = soup.select_one(f'li#section-{section_number}') or soup.select_one(f'div#section-{section_number}')
    if section_container is None:
        section_container = soup

    for candidate in _extract_activity_links_from_soup(section_container, base_url):
        href = candidate["url"]

        # Skip clearly unsupported file types early, but keep mod links that may redirect.
        if candidate["extension"] and candidate["extension"] not in SUPPORTED_EXTENSIONS:
            if "/mod/" not in href:
                continue

        if candidate.get("kind") == "link":
            if href in seen_urls:
                continue
            seen_urls.add(href)
            resources.append(candidate)
            continue

        if "/mod/folder/view.php" in href:
            resolved = session.get(href, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            resolved.raise_for_status()
            folder_url = resolved.url
            for file_link in _extract_file_links_from_folder_page(session, folder_url):
                if file_link["url"] in seen_urls:
                    continue
                if file_link["extension"] and file_link["extension"] not in SUPPORTED_EXTENSIONS:
                    continue
                seen_urls.add(file_link["url"])
                resources.append(file_link)
            continue

        if "/mod/resource/view.php" in href or "/mod/url/view.php" in href or "/mod/page/view.php" in href:
            resolved = session.get(href, timeout=HTTP_TIMEOUT_SECONDS, allow_redirects=True)
            resolved.raise_for_status()
            final_url = resolved.url
            content_type = resolved.headers.get("Content-Type", "").lower()

            final_host = urlparse(final_url).netloc
            base_host = urlparse(base_url).netloc
            if final_host and final_host != base_host:
                if final_url in seen_urls:
                    continue
                seen_urls.add(final_url)
                resources.append(
                    {
                        "name": candidate["name"],
                        "url": final_url,
                        "extension": "",
                        "kind": "link",
                    }
                )
                continue

            # If Moodle redirects to a real file, keep it.
            if content_type and "text/html" not in content_type:
                ext = _extension_from_url(final_url)
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                if final_url in seen_urls:
                    continue
                seen_urls.add(final_url)
                resources.append(
                    {
                        "name": _filename_from_response(resolved, final_url),
                        "url": final_url,
                        "extension": ext,
                    }
                )
                continue

            # Otherwise, inspect the landing page for attached files.
            inner_soup = BeautifulSoup(resolved.text, "html.parser")
            for file_candidate in _extract_activity_links_from_soup(inner_soup, base_url):
                file_ext = file_candidate["extension"]
                if file_ext and file_ext not in SUPPORTED_EXTENSIONS:
                    continue
                if file_candidate["url"] in seen_urls:
                    continue
                seen_urls.add(file_candidate["url"])
                resources.append(file_candidate)

    return resources


def _extract_file_links_from_folder_page(
    session: requests.Session,
    folder_url: str,
) -> list[dict[str, str]]:
    """Collect direct file download links from a Moodle folder resource page."""
    response = session.get(folder_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    files: list[dict[str, str]] = []

    # pluginfile.php and draftfile.php are the two Moodle paths for user-uploaded files
    for a in soup.select('a[href*="/pluginfile.php"], a[href*="/draftfile.php"], a[href*="/file.php"]'):
        href = a.get("href", "")
        text = " ".join(a.get_text(" ", strip=True).split())
        ext = _extension_from_url(href)
        if ext and ext not in SUPPORTED_EXTENSIONS:
            continue
        files.append(
            {
                "name": text or Path(unquote(urlparse(href).path)).name or "archivo",
                "url": href,
                "extension": ext,
            }
        )

    return files


def list_course_resources(
    session: requests.Session,
    moodle_url: str,
    course_id: str,
) -> list[dict]:
    """
    Listar todos los recursos descargables de un curso de Moodle.

    Args:
        session: Sesión autenticada de requests.
        moodle_url: URL base de Moodle.
        course_id: ID numérico del curso en Moodle.

    Returns:
        Lista de dicts con keys: 'name', 'url', 'extension'.

    TODO: Implementar. La URL de recursos es generalmente:
          {moodle_url}/course/view.php?id={course_id}
          Los links a archivos tienen clase "resourcelinkdetails" o similar
          dependiendo del tema de Moodle instalado.
    """
    course_url = f"{_base_url(moodle_url)}/course/view.php?id={course_id}"
    response = session.get(course_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    resources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    # Primero, capturar recursos visibles en la portada del curso.
    for candidate in _extract_activity_links_from_soup(soup, moodle_url):
        href = candidate["url"]
        if "/mod/resource/view.php" in href or "/mod/folder/view.php" in href or "/mod/page/view.php" in href or "/mod/url/view.php" in href:
            for resource in _resources_from_section_page(session, href, moodle_url):
                if resource["url"] not in seen_urls:
                    seen_urls.add(resource["url"])
                    resources.append(resource)

    # Después, recorrer todos los tiles clickeables y bajar a cada semana/sección.
    for tile in _tile_section_links(soup):
        section_url = tile["url"]
        section_number = tile["section"]
        log.info("Explorando tile/sección %s: %s", section_number, tile["title"])

        section_resources = _resources_from_section_page(session, section_url, moodle_url)
        if not section_resources:
            continue

        for resource in section_resources:
            if resource["url"] in seen_urls:
                continue
            seen_urls.add(resource["url"])
            resource["section_title"] = tile["title"]
            resources.append(resource)

    return resources


def download_file(
    session: requests.Session,
    url: str,
    dest_dir: Path,
    filename: Optional[str] = None,
) -> Path:
    """
    Descargar un archivo desde Moodle a un directorio local.

    Args:
        session: Sesión autenticada de requests.
        url: URL del archivo a descargar.
        dest_dir: Directorio de destino donde guardar el archivo.
        filename: Nombre de archivo opcional. Si None, se infiere de la URL.

    Returns:
        Path al archivo descargado.

    Raises:
        requests.HTTPError: Si la descarga falla (404, 403, etc.)

    TODO: Implementar. Usar streaming=True para archivos grandes.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)

    response = session.get(url, timeout=HTTP_TIMEOUT_SECONDS, stream=True, allow_redirects=True)
    response.raise_for_status()

    final_filename = filename or _filename_from_response(response, url)
    output_path = dest_dir / final_filename

    with output_path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 64):
            if chunk:
                handle.write(chunk)

    # Sidecar con URL de origen — permite al pipeline referenciar el documento en Moodle
    sidecar = output_path.with_suffix(output_path.suffix + ".kdef")
    sidecar.write_text(json.dumps({"source_url": url}), encoding="utf-8")

    return output_path


def download_course_materials(
    moodle_url: str,
    username: str,
    password: str,
    course_ids: Optional[list[str]] = None,
    course_slug_map: Optional[dict[str, str]] = None,
) -> list[Path]:
    """
    Punto de entrada principal del scraper.

    Descarga todos los materiales descargables de los cursos especificados
    (o de todos los cursos disponibles si course_ids es None) a un
    directorio temporal.

    Args:
        moodle_url: URL base de Moodle (ej: "https://moodle.undef.edu.ar")
        username: Usuario de Moodle.
        password: Contraseña de Moodle.
        course_ids: Lista de IDs de cursos a descargar. Si None, descarga
                    todos los cursos en los que está inscripto el usuario.
        course_slug_map: Mapeo opcional de course_id → slug. Cuando está
                         presente, se usa el slug como nombre de directorio
                         del curso en vez del título de Moodle.

    Returns:
        Lista de Paths a los archivos descargados en un directorio temporal.
        Los archivos son temporales — el pipeline los procesa y luego puede
        limpiarlos. NO se guardan en el repositorio.

    Raises:
        RuntimeError: Si la autenticación falla o Moodle no está disponible.
    """
    log.info("Iniciando scraping de Moodle: %s", moodle_url)

    session = create_moodle_session(moodle_url, username, password)

    if course_ids:
        log.info("Materias seleccionadas para tracking: %s", ", ".join(course_ids))

    temp_dir = Path(tempfile.mkdtemp(prefix="kdef-moodle-"))
    downloaded_files: list[Path] = []

    if not course_ids:
        log.warning("No se proporcionaron course_ids; por ahora el scraper requiere cursos explícitos")
        return downloaded_files

    for course_id in course_ids:
        log.info("Leyendo curso %s", course_id)
        course_url = f"{_base_url(moodle_url)}/course/view.php?id={course_id}"
        course_response = session.get(course_url, timeout=HTTP_TIMEOUT_SECONDS)
        course_response.raise_for_status()
        course_soup = BeautifulSoup(course_response.text, "html.parser")
        course_title = _course_title_from_page(course_soup, course_id)
        course_dir_name = (course_slug_map or {}).get(course_id) or _slugify(course_title)
        course_dir = temp_dir / course_dir_name
        course_dir.mkdir(parents=True, exist_ok=True)

        for resource in list_course_resources(session, moodle_url, course_id):
            extension = resource.get("extension", "")
            if extension and extension not in SUPPORTED_EXTENSIONS:
                continue

            resource_name = resource.get("name") or f"course-{course_id}-resource"
            section_title = resource.get("section_title") or "seccion"
            section_dir = course_dir / _section_dirname(section_title)
            section_dir.mkdir(parents=True, exist_ok=True)

            if resource.get("kind") == "link":
                url = resource["url"]
                if _is_youtube_url(url):
                    placeholder = section_dir / f"{_slugify(resource_name)}.md"
                    downloaded_files.append(
                        _write_link_placeholder(
                            placeholder,
                            title=resource_name,
                            url=url,
                            course_title=course_title,
                            section_title=section_title,
                        )
                    )
                    log.info("Video YouTube registrado: %s", resource_name)
                else:
                    log.debug("Link externo ignorado: %s", url)
                continue

            filename = Path(resource_name).name
            if _extension_from_url(filename) == "" and extension:
                filename = f"{filename}{extension}"

            downloaded = download_file(session, resource["url"], section_dir, filename=filename)
            downloaded_files.append(downloaded)
            log.info("Descargado %s -> %s", resource_name, downloaded.name)

    log.info("Scraping completado — %d archivo(s) descargado(s) en %s", len(downloaded_files), temp_dir)
    return downloaded_files
