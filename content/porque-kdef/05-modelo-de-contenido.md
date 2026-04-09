---
title: "05 — modelo de contenido"
date: 2026-04-08
tags: [meta, docs]
---

# 05. Modelo de contenido (content/)

## Directorios y ownership

- `content/notas-automaticas/` (**restringido al pipeline**):
  - Resúmenes automáticos por materia/sección.
  - Páginas agregadas por materia: `content/notas-automaticas/{slug}/fechas-importantes.md`.
  - **Regla**: no editar a mano; se sobreescribe en ejecuciones futuras.
- `content/notas-colaborativas/` (**abierto al aporte humano**):
  - Notas colaborativas creadas por estudiantes vía PR.
- `content/porque-kdef/`:
  - Documentación del proyecto (arquitectura, cómo contribuir, replicación).

## Convenciones de nombres

### Path de salida de un resumen

El pipeline construye el path de salida replicando el árbol relativo del recurso descargado y prefijando el nombre del archivo con la fecha de procesamiento (`YYYY-MM-DD-...`).

- Código: `scripts/pipeline.py` → `build_output_path()` + `get_relative_source_path()`.

### Naming del archivo

- Se toma el `stem` del recurso fuente (sin extensión).
- Se convierte a minúsculas y se reemplazan espacios/guiones bajos por `-`.

## Contratos de frontmatter

### 1) Resumen generado (página individual)

Las páginas en `content/notas-automaticas/**/**/*.md` incluyen frontmatter YAML (ver `scripts/pipeline.py` → `_build_summary_frontmatter()`):

- `title` (string): título visible.
- `date` (string `YYYY-MM-DD`): fecha de procesamiento.
- `tags` (list[string]): incluye `auto-generado`.
- `source` (string): nombre del archivo fuente descargado.
- `source_path` (string): path relativo del recurso en el árbol temporal de Moodle (ej: `analisis-i/semana-1/archivo.pdf`).
- `generated_at` (string ISO-8601): timestamp en UTC.
- `important_dates` (list[object]): eventos detectados (ver schema en `./13-calendario-y-fechas.md`).

El body del `.md` incluye:

- un bloque de nota estándar ("archivo generado automáticamente..."),
- el resumen Markdown del LLM,
- una sección "Fechas importantes" renderizada desde `important_dates`.

### 2) Placeholder de enlace externo

Cuando el scraper detecta un link externo fuera del host de Moodle, puede crear un `.md` "placeholder" en el árbol temporal para preservar la referencia.

**Comportamiento actual**: solo se generan placeholders para YouTube; el resto se ignora (ver `./10-links-externos.md`).

- Código: `scripts/scraper.py` → `_write_link_placeholder()`.
- Frontmatter esperado:
  - `title` (string)
  - `source_type: "link"`
  - `source_url` (string URL)
  - `course_title` (string)
  - `section_title` (string)
  - `kdef_skip: true` (bool)
  - `kdef_kind: "youtube"|"link"` (string)

El pipeline detecta `kdef_skip: true` y escribe una nota de salida sin pasar por el LLM (ver `scripts/pipeline.py` → `write_placeholder_output`).

### 3) Calendario agregado

- Archivo: `content/notas-automaticas/{slug}/fechas-importantes.md` (generado).
- Código: `scripts/academic_calendar.py` → `render_subject_calendar_page()`.
- Frontmatter esperado:
  - `title: "fechas importantes"`
  - `date` (YYYY-MM-DD)
  - `tags`: incluye `auto-generado`, `calendario`, `{slug}`
  - `generated_at` (ISO)
  - `calendar_generated: true`
  - `calendar_event_count` (int)

### 4) Feed iCalendar (.ics)

El módulo mantiene `render_calendar_ics()`, pero `write_calendar_outputs()` no publica un `.ics` en la implementación actual.
