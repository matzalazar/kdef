---
title: "06 — configuración y secrets"
date: 2026-04-08
tags: [meta, docs]
---

# 06. Configuración y secrets

## Variables de entorno

Fuente:

- Desarrollo local: `.env` (cargado por `python-dotenv`).
- Producción/CI: variables del entorno (secrets de GitHub Actions).

Archivo de referencia: `.env.example`.

| Variable | Requerida | Uso | Notas |
|---|---:|---|---|
| `MOODLE_URL` | Sí (no dry-run) | Base URL de Moodle | Sin slash final recomendado |
| `MOODLE_USER` | Sí (no dry-run) | Usuario Moodle | Sensible |
| `MOODLE_PASS` | Sí (no dry-run) | Password Moodle | Sensible |
| `TRACKED_SUBJECTS` | No | Filtra materias por `slug` | `all`/vacío = todas habilitadas |
| `MODELS_API_KEY` | Sí (si se usa GitHub Models) | LLM primario | Usa OpenAI SDK con `base_url` de GitHub Models |
| `OPENROUTER_API_KEY` | Sí (si se usa OpenRouter) | LLM secundario | Usa OpenAI SDK con `base_url` de OpenRouter |
| `GEMINI_API_KEY` | Sí (si se usa Gemini) | LLM terciario/fallback | Solo si no hay `MODELS_API_KEY` ni `OPENROUTER_API_KEY` |
| `DRY_RUN` | No | Simulación | En dry-run no se escriben archivos ni manifest |
| `FORCE_REPROCESS` | No | Ignora manifest | Reprocesa todo (si hay archivos descargados) |

### Selección de LLM

- Si existe `MODELS_API_KEY` → modelo `github/gpt-4o-mini`.
- Else si existe `OPENROUTER_API_KEY` → modelo `openrouter/openai/gpt-oss-20b:free`.
- Else si existe `GEMINI_API_KEY` → modelo `gemini/gemini-1.5-flash`.
- Else:
  - en `DRY_RUN=true` se declara modelo `dry-run/mock`,
  - fuera de dry-run el pipeline termina con error.

## Catálogo del campus

Archivo: `config/campus.yml`.

### Schema

- `campus` (mapping):
  - `name` (string)
  - `url` (string URL)
- `subjects` (list[mapping]):
  - `slug` (string): identificador estable (usado en `TRACKED_SUBJECTS`).
  - `name` (string): nombre humano.
  - `moodle_course_id` (int|string): id numérico del curso en Moodle.
  - `enabled` (bool, default `true`): permite desactivar sin borrar.

El pipeline ignora materias `enabled: false` (ver `scripts/catalog.py`).

## Node/Quartz

Fuente: `package.json`.

- Requiere Node `>=22` y npm `>=10.9.2`.
- Comandos principales:
  - `npm run serve`: build + servidor local (Quartz).
  - `npm run build`: build estático a `public/`.
  - `npm run check`: `tsc --noEmit` + `prettier --check`.
