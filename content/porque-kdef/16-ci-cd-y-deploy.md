---
title: "16 — ci/cd y deploy"
date: 2026-04-08
tags: [meta, docs, ci-cd]
---

# 16. Feature: CI/CD y deploy

## Objetivo

Automatizar:

1. actualización de contenido (pipeline),
2. commit/push del contenido generado,
3. build del sitio,
4. deploy a Cloudflare Pages.

## Workflow

Archivo: `.github/workflows/update-garden.yml`

**Triggers:**
- Cron: lunes y jueves 03:00 UTC.
- Manual: `workflow_dispatch` con inputs:
  - `dry_run` (boolean)
  - `force_reprocess` (boolean)

## Job 1 — `update-content`

Responsabilidad: correr pipeline y commitear si hay cambios.

Pasos clave:

1. Checkout con permisos de escritura.
2. Setup Python 3.12 + cache pip.
3. `pip install -r scripts/requirements.txt`
4. Tests: `python -m unittest discover -s tests`
5. Ejecutar: `python scripts/pipeline.py` con env desde secrets.
6. Commit/push:
   - `git add content/notas-automaticas/ data/manifest.json content/index.md`
   - si no hay cambios: no commitea
   - si hay cambios: commit con fecha UTC y push a `main`

## Job 2 — `build-and-deploy`

Responsabilidad: construir Quartz y desplegar.

Pasos clave:

1. Checkout fresh.
2. Setup Node.js 22 + cache npm.
3. `npm ci`
4. Build: `npx quartz build` (output a `public/`)
5. Deploy: `cloudflare/wrangler-action@v3`
   - comando: `pages deploy public/ --project-name=kdef --branch=main`

## Secrets requeridos

| Secret | Uso |
|---|---|
| `MOODLE_URL` | URL base del Moodle |
| `MOODLE_USER` | Usuario Moodle |
| `MOODLE_PASS` | Contraseña Moodle |
| `GITHUB_MODELS_KEY` | LLM primario |
| `OPENROUTER_API_KEY` | LLM secundario |
| `GEMINI_API_KEY` | LLM terciario |
| `CF_API_TOKEN` | Deploy Cloudflare Pages |
| `CF_ACCOUNT_ID` | Cuenta Cloudflare |

## Cloudflare Pages: headers y redirects

Archivos:

- `_headers`: headers de seguridad (CSP, HSTS, X-Frame-Options, etc.)
- `_redirects`: reglas de redirect (ej. www → apex)

Estos archivos DEBEN mantenerse compatibles con Quartz (en particular CSP con `unsafe-eval` para el grafo).
