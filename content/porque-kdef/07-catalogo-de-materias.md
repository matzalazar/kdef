---
title: "07 — catálogo de materias"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 07. Feature: catálogo y selección de materias

## Objetivo

Mantener un catálogo declarativo de materias (campus) y decidir cuáles cursos de Moodle procesar en cada ejecución del pipeline.

## Entradas

- Archivo `config/campus.yml`.
- Variable de entorno `TRACKED_SUBJECTS` (opcional).

## Salidas

- Lista de materias activas (dicts) a trackear.
- Lista de `moodle_course_id` (strings) para pasar al scraper.

## API de módulo

Código: `scripts/catalog.py`

- `load_campus_catalog(catalog_path=...) -> dict`
- `parse_tracked_subjects(value) -> set[str] | None`
- `select_tracked_subjects(catalog, tracked_subjects) -> list[dict]`
- `get_course_ids(subjects) -> list[str]`

## Reglas de selección

1. El catálogo se carga desde YAML.
2. Se consideran solo subjects con `enabled != false`.
3. Si `TRACKED_SUBJECTS` es:
   - `all`, vacío o no definido → se procesan todas las habilitadas.
   - lista CSV (ej: `analisis-i, algebra`) → se filtra por `slug` (case-insensitive).
4. Para cada materia seleccionada, si `moodle_course_id` está presente → se agrega a `course_ids`.

## Manejo de errores y edge cases

- Si `config/campus.yml` no existe → el catálogo se considera vacío y el pipeline continúa (warning en `load_campus_catalog`).
- Si el YAML no es un mapping o `subjects` no es lista → se lanza `ValueError` (error de configuración).
- Materias sin `moodle_course_id`:
  - se mantienen en la lista de subjects (para UI / futuro),
  - pero no generan `course_ids` (no se descargan materiales).

## Razones de diseño

- `slug` permite estabilidad incluso si el nombre humano cambia.
- `enabled` permite desactivar temporalmente sin borrar historial.
