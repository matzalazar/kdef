---
title: "11 — manifest incremental"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 11. Feature: manifest incremental (SHA-256)

## Objetivo

Evitar reprocesar documentos que no cambiaron desde la última ejecución, reduciendo:

- llamadas a LLM,
- tiempo total del workflow,
- costo operacional.

## Archivo y ownership

- Archivo: `data/manifest.json`
- Es **generado/actualizado** por el pipeline y se commitea por GitHub Actions.

## Schema (v1)

Definido por `scripts/manifest.py`:

- `version` (int): `1`
- `last_run` (string ISO o null)
- `files` (mapping): key → metadata

Cada entrada en `files`:

- key (string): identificador estable del archivo fuente (`source_path` relativo)
- value:
  - `sha256` (string hex)
  - `processed_at` (string ISO)
  - `output` (string): path relativo del `.md` generado en el repo

## API de módulo

Código: `scripts/manifest.py`

- `load_manifest(path) -> dict` (robusto: no debe crashear por JSON corrupto)
- `save_manifest(path, manifest) -> None` (escritura atómica con `.tmp` + rename)
- `compute_file_hash(path) -> str` (lectura en chunks)
- `needs_processing(path, manifest, source_key=None) -> bool`

## Reglas de procesamiento incremental

Para un archivo `path`:

1. Si no aparece en `manifest["files"]` → **procesar**.
2. Si aparece pero no tiene `sha256` → **procesar**.
3. Si el hash actual difiere del registrado → **procesar**.
4. Si el hash coincide → **saltear**.

`FORCE_REPROCESS=true` fuerza el procesamiento aunque el manifest diga "sin cambios".

## Estado actual

La key de cada archivo se guarda como `source_path` relativo (por ejemplo `analisis-i/06-04-a-10-04/cronograma.pdf`) en vez de usar la ruta temporal absoluta.

Esto hace que el incremental sea estable entre ejecuciones aunque el directorio `/tmp/kdef-moodle-<random>/...` cambie en cada run.

`needs_processing(..., source_key=...)` conserva compatibilidad de lectura con manifests viejos basados en rutas absolutas temporales.
