"""
diagnose_tiles.py — Diagnóstico del scraping de tiles en el campus Moodle

Uso:
    python scripts/diagnose_tiles.py [course_id]

    Si no se pasa course_id, usa el primero habilitado en config/campus.yml.

Reporta:
  - Qué selectores CSS matchean en la página del curso
  - Cuántos tiles se encuentran (o no) con cada variante de selector
  - La estructura HTML de los primeros tiles encontrados
  - Los parámetros de URL de los hrefs de los tiles
  - Guarda el HTML crudo de la portada del curso en /tmp/kdef-course-debug.html
"""

import sys
import os
from pathlib import Path

# Permitir ejecución directa desde la raíz del repo
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import yaml
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

try:
    from scripts.auth import create_moodle_session
except ImportError:
    from auth import create_moodle_session

MOODLE_URL = os.getenv("MOODLE_URL", "").rstrip("/")
USER = os.getenv("MOODLE_USER", "")
PASS = os.getenv("MOODLE_PASS", "")


def load_first_course_id() -> str | None:
    catalog_path = Path(__file__).parent.parent / "config" / "campus.yml"
    with open(catalog_path) as f:
        data = yaml.safe_load(f)
    for subject in data.get("subjects", []):
        if subject.get("enabled"):
            return str(subject["moodle_course_id"])
    return None


def check_selector(soup: BeautifulSoup, selector: str) -> list:
    results = soup.select(selector)
    print(f"  [{len(results):3d}] {selector!r}")
    return results


def show_html_snippet(element, max_chars: int = 400) -> None:
    raw = str(element)
    if len(raw) > max_chars:
        raw = raw[:max_chars] + "..."
    print(f"    HTML: {raw}")


def analyze_href(href: str) -> None:
    parsed = urlparse(href)
    params = parse_qs(parsed.query)
    print(f"    href: {href}")
    print(f"    params: {dict(params)}")
    print(f"    fragment: {parsed.fragment!r}")


def main() -> None:
    if not MOODLE_URL or not USER or not PASS:
        print("ERROR: faltan variables MOODLE_URL / MOODLE_USER / MOODLE_PASS en .env")
        sys.exit(1)

    course_id = sys.argv[1] if len(sys.argv) > 1 else load_first_course_id()
    if not course_id:
        print("ERROR: no se encontró course_id")
        sys.exit(1)

    print(f"\n=== Diagnóstico de tiles — curso {course_id} ===\n")
    print("Autenticando...")
    session = create_moodle_session(MOODLE_URL, USER, PASS)

    course_url = f"{MOODLE_URL}/course/view.php?id={course_id}"
    print(f"Descargando: {course_url}")
    response = session.get(course_url, timeout=30)
    response.raise_for_status()

    debug_path = Path("/tmp/kdef-course-debug.html")
    debug_path.write_text(response.text, encoding="utf-8")
    print(f"HTML guardado en: {debug_path}\n")

    soup = BeautifulSoup(response.text, "lxml")

    print("--- Selectores de tiles (variantes) ---")
    # Variante original (la que usa el scraper actualmente)
    original = check_selector(soup, 'li[id^="tile-"]')
    # Variantes alternativas del plugin Format Tiles en versiones recientes
    check_selector(soup, 'li[id^="section-"]')
    check_selector(soup, 'li.tile')
    check_selector(soup, 'li.section.tile')
    check_selector(soup, 'div[id^="tile-"]')
    check_selector(soup, 'div.tile-content')
    check_selector(soup, 'a.tile-link')
    check_selector(soup, 'a[data-section]')
    check_selector(soup, 'a[data-tileid]')
    check_selector(soup, 'li[data-section]')

    print("\n--- Análisis de los primeros tiles (selector original) ---")
    if original:
        for tile in original[:3]:
            print(f"\n  tile id={tile.get('id')!r} class={tile.get('class')!r}")
            show_html_snippet(tile)
            # Buscar el link dentro
            for link_sel in ['a.tile-link[href]', 'a[href][class*="tile"]', 'a.stretched-link', 'a[href]']:
                link = tile.select_one(link_sel)
                if link:
                    print(f"  link encontrado con: {link_sel!r}")
                    analyze_href(link.get("href", ""))
                    break
            else:
                print("  sin link")
    else:
        print("  *** No se encontraron tiles con el selector original ***")

    print("\n--- Análisis de links con 'section' en el href ---")
    section_links = soup.select('a[href*="section="]')
    print(f"  Links con section=: {len(section_links)}")
    for a in section_links[:5]:
        analyze_href(a.get("href", ""))

    print("\n--- Análisis de links con 'tileid' en el href ---")
    tile_links = soup.select('a[href*="tileid="]')
    print(f"  Links con tileid=: {len(tile_links)}")
    for a in tile_links[:5]:
        analyze_href(a.get("href", ""))

    print("\n--- Análisis de links con 'sectionid' en el href ---")
    sectionid_links = soup.select('a[href*="sectionid="]')
    print(f"  Links con sectionid=: {len(sectionid_links)}")
    for a in sectionid_links[:5]:
        analyze_href(a.get("href", ""))

    print("\n--- IDs de <li> en el body (primeros 20) ---")
    li_ids = [li.get("id") for li in soup.select("li[id]")][:20]
    for lid in li_ids:
        print(f"  {lid!r}")

    print("\n=== Fin diagnóstico ===")
    print(f"Revisá el HTML completo en: {debug_path}")


if __name__ == "__main__":
    main()
