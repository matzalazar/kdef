---
title: "14 — orquestador"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 14. Feature: orquestador del pipeline

## Objetivo

Ejecutar el flujo completo de actualización:

1. cargar config,
2. descargar materiales,
3. resumir y extraer fechas,
4. escribir `content/notas-automaticas/`,
5. regenerar páginas de fechas importantes por materia,
6. actualizar manifest,
7. fallar el job si hubo errores (para visibilidad en CI).

## Entry point

- Script: `scripts/pipeline.py`
- Se ejecuta en GH Actions con: `python scripts/pipeline.py`

## Configuración

Función: `load_config()`.

- Carga `.env` (desarrollo local) y luego entorno real.
- Flags:
  - `DRY_RUN=true` → no escribe archivos ni manifest.
  - `FORCE_REPROCESS=true` → ignora manifest para decidir `needs_processing`.
- Selección de materias: lee `TRACKED_SUBJECTS` y carga `config/campus.yml`.

En modo **no dry-run**, faltantes en `MOODLE_URL|MOODLE_USER|MOODLE_PASS` → exit(1).

## Selección de modelo LLM

- Si hay `MODELS_API_KEY` → `github/gpt-4o-mini`.
- Else si hay `OPENROUTER_API_KEY` → `openrouter/openai/gpt-oss-20b:free`.
- Else si hay `GEMINI_API_KEY` → `gemini/gemini-1.5-flash`.
- Else: en dry-run → `dry-run/mock`; fuera de dry-run → exit(1).

## Descarga (scraper)

- Llama `download_course_materials(...)` solo si no es dry-run.
- En dry-run se setea `downloaded_files = []` y se skipea la descarga.

## Decisión de procesamiento (manifest)

Para cada `source_path` descargado:

- Se calcula `source_key` estable con `get_relative_source_path(source_path).as_posix()`.
- Si `FORCE_REPROCESS=false` y `needs_processing(...)==false` → saltea.
- Si procesa:
  - llama `summarize_document(path=source_path, model=model)`
  - escribe `.md` con `write_summary_file(...)`
  - calcula SHA-256 y actualiza manifest en memoria usando `source_key` estable.

Errores:
- `DocumentTooLargeError` → warning y se saltea el archivo.
- Otros `Exception` → log error, incrementa `error_count` y continúa.

## Escritura de outputs

### Resúmenes

`write_summary_file()`:
- arma frontmatter con `important_dates`,
- agrega nota estándar,
- agrega resumen del LLM,
- agrega sección de "Fechas importantes".

### Calendario agregado

Solo en modo no dry-run: llama `write_calendar_outputs(CONTENT_AUTO_DIR, generated_at)`.

### Manifest

Solo en modo no dry-run: escribe `data/manifest.json` con `save_manifest()`.

## Exit codes (contrato con CI)

| Condición | Exit code |
|---|---|
| Variables obligatorias faltantes (no dry-run) | 1 |
| Sin LLM configurado (no dry-run) | 1 |
| `error_count > 0` (errores de documentos) | 1 |
| Ejecución exitosa | 0 |

Esto permite que GH Actions marque el workflow como fallido aunque haya procesado parcialmente.
