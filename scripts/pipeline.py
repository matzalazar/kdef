"""
pipeline.py — Orquestador del pipeline de actualización de kdef

Flujo completo:
  1. Leer configuración desde variables de entorno
  2. Cargar el manifest de archivos ya procesados
  3. Descargar materiales nuevos/modificados de Moodle (via scraper.py)
  4. Para cada documento no procesado (según manifest), generar resumen con LLM
     y extraer fechas importantes
    5. Escribir los archivos .md en content/notas-automaticas/
    6. Regenerar el calendario agregado + feed .ics en content/notas-automaticas/calendario/
  7. Actualizar el manifest con los nuevos hashes
  8. En modo dry-run: mostrar qué se haría pero no escribir nada

Configuración (todas desde variables de entorno):
  MOODLE_URL          URL base del Moodle
  MOODLE_USER         Usuario de Moodle
  MOODLE_PASS         Contraseña de Moodle
  GITHUB_MODELS_KEY   API key para GitHub Models (LLM primario)
  OPENROUTER_API_KEY  API key para OpenRouter (LLM secundario)
  GEMINI_API_KEY      API key para Google Gemini (LLM terciario / fallback)
  DRY_RUN             'true' para modo simulación, no escribe archivos
  FORCE_REPROCESS     'true' para ignorar el manifest y reprocesar todo

Decisiones de diseño:
  - Todo config viene de env vars: el script es 12-factor friendly y
    se puede ejecutar localmente con un .env sin tocar el código.
  - DryRunMode como flag explícito, no como argumento de CLI, para que
    sea fácil activarlo desde GitHub Actions inputs.
  - El manifest se escribe al final, no por documento, para evitar
    estados inconsistentes si el pipeline se interrumpe a la mitad.
"""

import hashlib
import os
import re
import sys
import logging
import unicodedata
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

try:
    from scripts.catalog import get_course_ids, load_campus_catalog, parse_tracked_subjects, select_tracked_subjects
    from scripts.academic_calendar import dump_frontmatter, load_markdown_frontmatter, render_important_dates_section, write_calendar_outputs
    from scripts.scraper import download_course_materials
    from scripts.summarizer import summarize_document, DocumentTooLargeError, DocumentTruncatedError, DocumentUnreadableError
    from scripts.manifest import load_manifest, save_manifest, needs_processing
except ImportError:  # pragma: no cover - fallback for direct script execution
    from catalog import get_course_ids, load_campus_catalog, parse_tracked_subjects, select_tracked_subjects
    from academic_calendar import dump_frontmatter, load_markdown_frontmatter, render_important_dates_section, write_calendar_outputs
    from scraper import download_course_materials
    from summarizer import summarize_document, DocumentTooLargeError, DocumentTruncatedError, DocumentUnreadableError
    from manifest import load_manifest, save_manifest, needs_processing

# ---------------------------------------------------------------------------
# Configuración de logging — formato de una línea para que sea legible en GH Actions
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths del proyecto — relativos a la raíz del repositorio
# El pipeline se ejecuta desde la raíz del repo en GitHub Actions
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
CONTENT_AUTO_DIR = REPO_ROOT / "content" / "notas-automaticas"
MANIFEST_PATH = REPO_ROOT / "data" / "manifest.json"
CATALOG_PATH = REPO_ROOT / "config" / "campus.yml"


def load_config() -> dict:
    """
    Cargar configuración desde variables de entorno.

    Carga primero desde .env (desarrollo local) y luego desde el entorno
    real (GitHub Actions secrets). El entorno real tiene precedencia.

    Returns:
        dict con todas las variables de configuración necesarias.

    Raises:
        SystemExit: si faltan variables obligatorias en modo no dry-run.
    """
    # Cargar .env si existe (solo útil en desarrollo local)
    load_dotenv()

    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    force_reprocess = os.getenv("FORCE_REPROCESS", "false").lower() == "true"
    tracked_subjects = parse_tracked_subjects(os.getenv("TRACKED_SUBJECTS", "all"))

    config = {
        "moodle_url": os.getenv("MOODLE_URL", ""),
        "moodle_user": os.getenv("MOODLE_USER", ""),
        "moodle_pass": os.getenv("MOODLE_PASS", ""),
        "github_models_key": os.getenv("GITHUB_MODELS_KEY", ""),
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", ""),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
        "tracked_subjects": tracked_subjects,
        "dry_run": dry_run,
        "force_reprocess": force_reprocess,
    }

    # Validar que las variables obligatorias estén presentes cuando no es dry-run
    # En dry-run se puede ejecutar sin credenciales para probar la lógica
    if not dry_run:
        required = ["moodle_url", "moodle_user", "moodle_pass"]
        missing = [k for k in required if not config[k]]
        if missing:
            log.error("Variables de entorno faltantes: %s", ", ".join(missing))
            sys.exit(1)

    return config


def build_output_path(source_path: Path, processed_at: datetime) -> Path:
    """
    Construir la ruta de salida del archivo .md en content/notas-automaticas/.

    El nombre del archivo incluye la fecha de procesamiento para hacer
    el histórico de cambios legible en el árbol de archivos.

    Args:
        source_path: Path del documento fuente descargado de Moodle.
        processed_at: Fecha y hora del procesamiento.

    Returns:
        Path absoluto del archivo .md de salida.
    """
    date_prefix = processed_at.strftime("%Y-%m-%d")
    relative_source = get_relative_source_path(source_path)
    slug = _slugify_source_name(relative_source.name)
    return CONTENT_AUTO_DIR / relative_source.parent / f"{date_prefix}-{slug}.md"


# Extensiones a quitar en cascada (incluye formatos intermedios y de Office)
_STRIPPABLE_EXTS = {".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".txt", ".md", ".kdef"}


def _first_word(filename: str) -> str:
    """Extraer la primera palabra del nombre de archivo, en minúsculas y ASCII."""
    name = filename
    while Path(name).suffix.lower() in _STRIPPABLE_EXTS:
        name = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    words = re.split(r"[\s\-_]+", ascii_name.strip())
    return words[0].lower() if words and words[0] else "doc"


def _slugify_source_name(filename: str) -> str:
    """Derive a short, filesystem-safe slug from a source filename."""
    return _first_word(filename)


def get_relative_source_path(source_path: Path) -> Path:
    """Obtener la ruta relativa del recurso descargado dentro del árbol temporal."""
    for index, part in enumerate(source_path.parts):
        if part.startswith("kdef-moodle-"):
            relative_source = Path(*source_path.parts[index + 1 :])
            if relative_source.parts:
                return relative_source
            break

    return Path(source_path.name)


def _build_summary_frontmatter(
    *,
    source_path: Path,
    processed_at: datetime,
    important_dates: list[dict[str, str]],
    summary_markdown: str = "",
) -> dict:
    """Build the YAML frontmatter dict for a generated summary file.

    Args:
        source_path: Path of the original downloaded file.
        processed_at: UTC timestamp of this processing run.
        important_dates: Structured events extracted by the LLM.
        summary_markdown: Raw markdown output from the LLM (used to derive title).

    Returns:
        Dict ready to be serialized with dump_frontmatter().
    """
    relative_source = get_relative_source_path(source_path)
    title = _extract_title(summary_markdown, source_path)

    # source_path stores the stable relative key, not the /tmp path,
    # so Quartz can render it as metadata without leaking the temp dir
    return {
        "title": title,
        "date": processed_at.strftime("%Y-%m-%d"),
        "tags": ["auto-generado"],
        "source": source_path.name,
        "source_path": relative_source.as_posix(),
        "generated_at": processed_at.isoformat(),
        "important_dates": important_dates,
    }


def _extract_title(markdown: str, source_path: Path) -> str:
    """Título para el explorador: primera palabra del nombre del archivo, en minúsculas."""
    return _first_word(source_path.name)


def write_summary_file(
    output_path: Path,
    summary: str,
    source_path: Path,
    important_dates: list[dict[str, str]],
) -> None:
    """
    Escribir el archivo .md con el resumen generado.

    Agrega el frontmatter estándar requerido por Quartz antes del contenido
    generado por el LLM.

    Args:
        output_path: Path donde escribir el archivo .md.
        summary: Contenido markdown generado por el LLM.
        source_path: Path del documento fuente (para metadatos).
    """
    processed_at = datetime.now(timezone.utc)
    frontmatter = dump_frontmatter(
        _build_summary_frontmatter(
            source_path=source_path,
            processed_at=processed_at,
            important_dates=important_dates,
            summary_markdown=summary,
        )
    )

    dates_section = render_important_dates_section(important_dates).strip()
    body_parts = [
        frontmatter.strip(),
        "",
        "> **Nota:** Este archivo fue generado automáticamente por el pipeline de kdef.",
        "> El contenido proviene de materiales del aula virtual de la UNDEF.",
        "> Para correcciones, abrí un issue en el repositorio.",
        "",
        summary.strip(),
        "",
    ]
    if dates_section:
        body_parts += [dates_section, ""]

    body = "\n".join(
        [
            *body_parts,
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")


def _section_title_from_slug(slug: str) -> str:
    """Convertir un slug de sección a título para el explorador.
    '06-04-a-10-04' → '06/04 al 10/04'. Cualquier otra cosa → primera palabra."""
    m = re.match(r"^(\d{2})-(\d{2})-a-(\d{2})-(\d{2})$", slug)
    if m:
        d1, m1, d2, m2 = m.groups()
        return f"{d1}/{m1} al {d2}/{m2}"
    return slug.split("-")[0]


def _ensure_index(directory: Path, title: str, tags: list[str]) -> None:
    """Crear index.md en el directorio si no existe, con el título dado."""
    index = directory / "index.md"
    if index.exists():
        return
    directory.mkdir(parents=True, exist_ok=True)
    content = dump_frontmatter({
        "title": title,
        "tags": tags,
    })
    index.write_text(content, encoding="utf-8")


def _read_sidecar_url(source_path: Path) -> str:
    """Leer la URL de origen del sidecar .kdef si existe."""
    import json
    sidecar = source_path.with_suffix(source_path.suffix + ".kdef")
    if sidecar.exists():
        try:
            return json.loads(sidecar.read_text(encoding="utf-8")).get("source_url", "")
        except Exception:
            pass
    return ""


def write_placeholder_output(
    output_path: Path,
    source_path: Path,
    kind: str,
    source_url: str,
    title: str = "",
    partial_markdown: str = "",
) -> None:
    """
    Escribir un .md de referencia sin pasar por el LLM (o con contenido parcial).

    Usado para PDFs sin texto extraíble, videos de YouTube, links externos,
    y documentos cuyo resumen fue truncado por el límite de tokens del LLM.
    """
    processed_at = datetime.now(timezone.utc)
    tag_map = {
        "unreadable": ["auto-generado", "sin-texto"],
        "youtube": ["auto-generado", "video"],
        "link": ["auto-generado", "enlace"],
        "truncated": ["auto-generado", "truncado"],
    }
    frontmatter = dump_frontmatter({
        "title": _first_word(source_path.name),
        "date": processed_at.strftime("%Y-%m-%d"),
        "tags": tag_map.get(kind, ["auto-generado"]),
        "source": source_path.name,
        "generated_at": processed_at.isoformat(),
        "important_dates": [],
    })

    if kind == "unreadable":
        body_lines = [
            "> Este documento no pudo procesarse automáticamente: el PDF no contiene texto extraíble",
            "> (posiblemente escaneado o generado desde una imagen).",
        ]
        if source_url:
            body_lines.append(f">\n> [Acceder al documento en el aula virtual →]({source_url})")
    elif kind == "truncated":
        body_lines = [
            "> **Nota:** Este resumen está incompleto — el documento excedió el límite de tokens del LLM.",
            "> El contenido a continuación es el texto generado antes del corte.",
        ]
        if source_url:
            body_lines.append(f">\n> [Acceder al documento completo en el aula virtual →]({source_url})")
        if partial_markdown:
            body_lines += ["", partial_markdown.strip()]
    elif kind == "youtube":
        body_lines = [
            "> Este recurso es un video de YouTube.",
            f">\n> [Ver video →]({source_url})" if source_url else "",
        ]
    else:
        body_lines = [
            f"> Enlace externo: [{source_url}]({source_url})" if source_url else "> Enlace externo.",
        ]

    body = "\n".join([frontmatter.strip(), "", *filter(None, body_lines), ""])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")


def _update_home_last_run(generated_at: datetime) -> None:
    """Actualizar el marcador de última ejecución en content/index.md."""
    index_path = REPO_ROOT / "content" / "index.md"
    if not index_path.exists():
        return
    text = index_path.read_text(encoding="utf-8")
    timestamp = generated_at.strftime("%Y-%m-%d %H:%M UTC")
    updated = re.sub(
        r"<!-- kdef:last-run:start -->.*?<!-- kdef:last-run:end -->",
        f"<!-- kdef:last-run:start -->\n> *última actualización automática: {timestamp}*\n<!-- kdef:last-run:end -->",
        text,
        flags=re.DOTALL,
    )
    if updated != text:
        index_path.write_text(updated, encoding="utf-8")
        log.info("Home actualizado con última ejecución: %s", timestamp)


def run_pipeline(config: dict) -> None:
    """
    Ejecutar el pipeline completo de actualización de contenido.

    Args:
        config: Diccionario de configuración cargado por load_config().
    """
    dry_run = config["dry_run"]
    force_reprocess = config["force_reprocess"]
    catalog = load_campus_catalog(CATALOG_PATH)
    selected_subjects = select_tracked_subjects(catalog, config["tracked_subjects"])
    course_ids = get_course_ids(selected_subjects)

    if dry_run:
        log.info("MODO DRY-RUN activo — no se escribirán archivos ni se actualizará el manifest")

    if selected_subjects:
        log.info(
            "Materias activas (%d): %s",
            len(selected_subjects),
            ", ".join(str(subject.get("slug")) for subject in selected_subjects),
        )
        if not dry_run:
            for subject in selected_subjects:
                slug = subject.get("slug", "")
                if slug:
                    _ensure_index(CONTENT_AUTO_DIR / slug, slug, ["auto-generado", "materia"])
    else:
        log.warning("No hay materias activas seleccionadas en config/campus.yml + TRACKED_SUBJECTS")

    # Determinar el modelo LLM a usar
    # Orden de preferencia: GitHub Models → OpenRouter → Gemini
    if config["github_models_key"]:
        model = "github/gpt-4o-mini"
        log.info("LLM: GitHub Models (primario)")
    elif config["openrouter_api_key"]:
        model = "openrouter/openai/gpt-oss-20b:free"
        log.info("LLM: OpenRouter (secundario)")
    elif config["gemini_api_key"]:
        model = "gemini/gemini-1.5-flash"
        log.info("LLM: Gemini (terciario / fallback)")
    else:
        if dry_run:
            model = "dry-run/mock"
            log.info("Dry-run sin LLM keys — usando modelo mock")
        else:
            log.error("No hay LLM configurado (GITHUB_MODELS_KEY, OPENROUTER_API_KEY o GEMINI_API_KEY)")
            sys.exit(1)

    # Cargar manifest para saber qué ya fue procesado
    manifest = load_manifest(MANIFEST_PATH)
    log.info("Manifest cargado: %d archivos registrados", len(manifest.get("files", {})))

    # Descargar materiales de Moodle
    log.info("Descargando materiales de Moodle: %s", config["moodle_url"])
    if dry_run:
        downloaded_files: list[Path] = []
        log.info("Dry-run: skip descarga de Moodle")
    else:
        course_slug_map = {
            str(subject["moodle_course_id"]): subject["slug"]
            for subject in selected_subjects
            if subject.get("moodle_course_id") and subject.get("slug")
        }
        downloaded_files = download_course_materials(
            moodle_url=config["moodle_url"],
            username=config["moodle_user"],
            password=config["moodle_pass"],
            course_ids=course_ids or None,
            course_slug_map=course_slug_map,
        )
    log.info("Descargados %d archivos de Moodle", len(downloaded_files))

    # Año académico en curso — se pasa al LLM para que pueda completar fechas parciales
    # como "21-may" o "10-jul" con el año correcto en date_iso
    academic_year = str(datetime.now(timezone.utc).year)

    # Procesar archivos no registrados en el manifest
    processed_count = 0
    skipped_count = 0
    error_count = 0
    updated_manifest = dict(manifest)

    for source_path in downloaded_files:
        source_key = get_relative_source_path(source_path).as_posix()

        # Verificar si necesita procesamiento según el manifest
        if not force_reprocess and not needs_processing(source_path, manifest, source_key=source_key):
            log.debug("Saltando %s (no modificado según manifest)", source_path.name)
            skipped_count += 1
            continue

        log.info("Procesando: %s", source_path.name)

        # Crear index.md de sección si no existe (da título legible al explorador)
        if not dry_run:
            relative = get_relative_source_path(source_path)
            if len(relative.parts) >= 2:
                section_slug = relative.parts[1]
                section_dir = CONTENT_AUTO_DIR / relative.parts[0] / section_slug
                section_title = _section_title_from_slug(section_slug)
                _ensure_index(section_dir, section_title, ["auto-generado", "semana"])

        # Detectar placeholders de links/YouTube — no pasan por el LLM
        if source_path.suffix == ".md":
            meta = load_markdown_frontmatter(source_path)
            if meta.get("kdef_skip"):
                kind = meta.get("kdef_kind", "link")
                source_url = meta.get("source_url", "")
                title = meta.get("title", source_path.stem)
                now = datetime.now(timezone.utc)
                output_path = build_output_path(source_path, now)
                if dry_run:
                    log.info("Dry-run: placeholder %s → %s", kind, output_path)
                else:
                    write_placeholder_output(output_path, source_path, kind, source_url, title)
                    log.info("Placeholder %s: %s", kind, output_path.relative_to(REPO_ROOT))
                    # Registrar en manifest para no re-procesar en próximas corridas
                    file_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                    if "files" not in updated_manifest:
                        updated_manifest["files"] = {}
                    updated_manifest["files"][source_key] = {
                        "sha256": file_hash,
                        "processed_at": now.isoformat(),
                        "output": str(output_path.relative_to(REPO_ROOT)),
                    }
                processed_count += 1
                continue

        try:
            summary = summarize_document(path=source_path, model=model, academic_year=academic_year)

            now = datetime.now(timezone.utc)
            output_path = build_output_path(source_path, now)

            if dry_run:
                log.info("Dry-run: se escribiría %s", output_path)
            else:
                CONTENT_AUTO_DIR.mkdir(parents=True, exist_ok=True)
                write_summary_file(
                    output_path,
                    summary.markdown,
                    source_path,
                    summary.important_dates,
                )
                log.info("Escrito: %s", output_path.relative_to(REPO_ROOT))

            file_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
            if "files" not in updated_manifest:
                updated_manifest["files"] = {}
            updated_manifest["files"][source_key] = {
                "sha256": file_hash,
                "processed_at": now.isoformat(),
                "output": str(output_path.relative_to(REPO_ROOT)),
            }

            processed_count += 1

        except DocumentTruncatedError as exc:
            log.warning("Resumen truncado por LLM: %s", source_path.name)
            source_url = _read_sidecar_url(source_path)
            now = datetime.now(timezone.utc)
            output_path = build_output_path(source_path, now)
            if not dry_run:
                write_placeholder_output(
                    output_path, source_path, "truncated", source_url,
                    partial_markdown=exc.partial_markdown,
                )
                log.info("Placeholder truncado: %s", output_path.relative_to(REPO_ROOT))
                file_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if "files" not in updated_manifest:
                    updated_manifest["files"] = {}
                updated_manifest["files"][source_key] = {
                    "sha256": file_hash,
                    "processed_at": now.isoformat(),
                    "output": str(output_path.relative_to(REPO_ROOT)),
                }
            processed_count += 1

        except DocumentUnreadableError as exc:
            log.warning("PDF sin texto: %s", source_path.name)
            source_url = _read_sidecar_url(source_path)
            now = datetime.now(timezone.utc)
            output_path = build_output_path(source_path, now)
            if not dry_run:
                write_placeholder_output(output_path, source_path, "unreadable", source_url)
                log.info("Placeholder sin-texto: %s", output_path.relative_to(REPO_ROOT))
                file_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
                if "files" not in updated_manifest:
                    updated_manifest["files"] = {}
                updated_manifest["files"][source_key] = {
                    "sha256": file_hash,
                    "processed_at": now.isoformat(),
                    "output": str(output_path.relative_to(REPO_ROOT)),
                }
            processed_count += 1

        except DocumentTooLargeError as exc:
            log.warning("Saltando %s: %s", source_path.name, exc)
            skipped_count += 1

        except Exception as exc:
            log.error("Error procesando %s: %s", source_path.name, exc)
            error_count += 1

    # Guardar manifest actualizado
    updated_manifest["last_run"] = datetime.now(timezone.utc).isoformat()
    if not dry_run:
        generated_at = datetime.now(timezone.utc)
        calendar_entries = write_calendar_outputs(CONTENT_AUTO_DIR, generated_at)
        log.info("Fechas importantes actualizadas: %d evento(s)", len(calendar_entries))
        save_manifest(MANIFEST_PATH, updated_manifest)
        _update_home_last_run(generated_at)

    # Resumen final
    log.info(
        "Pipeline completado — procesados: %d, saltados: %d, errores: %d",
        processed_count,
        skipped_count,
        error_count,
    )

    # Salir con error si hubo errores de procesamiento
    # Esto hace que el step de GitHub Actions muestre fallo
    if error_count > 0:
        log.warning("Hubo %d errores durante el procesamiento", error_count)
        sys.exit(1)


if __name__ == "__main__":
    config = load_config()
    run_pipeline(config)
