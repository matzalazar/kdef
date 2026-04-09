---
title: "09 — scraper de moodle"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 09. Feature: scraper/descarga de materiales desde Moodle

## Objetivo

Descubrir y descargar recursos relevantes de cursos de Moodle a un directorio temporal local (en `/tmp`) para su posterior procesamiento por el pipeline.

## Entradas

- `moodle_url` (string)
- `username` / `password` (strings)
- `course_ids` (list[string]) — **actualmente requerido**
- `course_slug_map` (dict opcional `course_id -> slug`) para forzar nombres de directorio estables.

## Salidas

- `list[pathlib.Path]` apuntando a archivos descargados en un árbol temporal:
  - `/tmp/kdef-moodle-<random>/<curso>/<seccion>/<archivo>`

## API de módulo

Código: `scripts/scraper.py`

- `download_course_materials(...) -> list[Path]` (entrypoint)
- `list_course_resources(session, moodle_url, course_id) -> list[dict]`
- `download_file(session, url, dest_dir, filename=None) -> Path`

## Tipos soportados

El scraper filtra por extensión (ver `SUPPORTED_EXTENSIONS`):

- `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`

Los demás tipos pueden descartarse temprano, salvo links de actividades Moodle que luego redirijan a un tipo soportado.

## Descubrimiento de recursos (alto nivel)

Para cada `course_id`:

1. GET `.../course/view.php?id=<course_id>`
2. Determina `course_title` desde el `h1` de la página.
3. Determina `course_dir_name`:
   - si existe `course_slug_map[course_id]` → usarlo,
   - si no → slugify del `course_title`.
4. Construye lista de recursos:
   - recursos visibles en la portada,
   - y recursos dentro de tiles/secciones del curso (Moodle Tiles).
5. Para cada recurso:
   - si es un link externo:
     - si es YouTube → crea un placeholder `.md`,
     - si no → se ignora (ver [10 — links externos](./10-links-externos)).
   - si es un archivo soportado → lo descarga con streaming a disco.

## Estructura del árbol temporal

- Directorio base: `tempfile.mkdtemp(prefix="kdef-moodle-")`.
- Directorio de sección: `_section_dirname(section_title)`:
  - si detecta rango "dd/mm al dd/mm" devuelve `dd-mm-a-dd-mm`,
  - si no, aplica slugify.

## Placeholders para links externos

Si un recurso es un link externo, **solo** se generan placeholders para YouTube (comportamiento actual). El resto se ignora para no poblar el garden con links irrelevantes.

- Código: `_write_link_placeholder()` + `_is_youtube_url()`.
- Se agrega ese `.md` a la lista de archivos "descargados" y el pipeline lo copia como salida sin pasar por el LLM (usa `kdef_skip: true`).

Para el criterio/razón de esta decisión, ver [10 — links externos](./10-links-externos).

## Limitaciones actuales

- Si `course_ids` es `None` o vacío, el scraper loguea warning y **retorna lista vacía** (no implementa aún el "descubrimiento de cursos inscriptos").
- Esto impacta el modo dry-run del pipeline (ver [14 — orquestador del pipeline](./14-orquestador-pipeline)).
