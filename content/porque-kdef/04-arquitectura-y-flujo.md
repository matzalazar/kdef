---
title: "04 — arquitectura y flujo"
date: 2026-04-08
tags: [meta, docs, arquitectura, pipeline]
---

# 04. Arquitectura y flujo end-to-end

Tour narrativo: [02 — cómo funciona](./02-como-funciona)

## Vista rápida

`kdef` es un pipeline batch + un sitio estático. No hay servidor ni base de datos: el estado vive en archivos (`data/manifest.json` + `.md` en `content/`).

**Mapa end-to-end:**

```
Moodle → scraper → /tmp → pipeline (manifest → LLM → calendario)
       → content/notas-automaticas/ + data/manifest.json
       → Quartz build → deploy (Cloudflare Pages)
```

## Componentes

### Pipeline (Python)

| Script | Responsabilidad |
|---|---|
| `scripts/pipeline.py` | orquesta el flujo completo |
| `scripts/catalog.py` | carga `config/campus.yml` y selecciona materias |
| `scripts/auth.py` | login en Moodle (logintoken + sesión) |
| `scripts/scraper.py` | descubre y descarga materiales (a `/tmp`) |
| `scripts/summarizer.py` | extrae texto + llama a LLM + parsea eventos |
| `scripts/academic_calendar.py` | normaliza eventos y genera páginas `fechas-importantes.md` |
| `scripts/manifest.py` | tracking incremental por SHA-256 |

### Sitio (Quartz / Node)

- `quartz.config.ts`: configuración del sitio, plugins, tema, locale.
- `quartz.layout.ts`: layout de componentes (búsqueda, grafo, TOC, etc.).
- `content/`: fuente de contenido (notas-automaticas + notas-colaborativas + porque-kdef).

### CI/CD

- `.github/workflows/update-garden.yml`: ejecuta pipeline + build + deploy.
- `_headers` y `_redirects`: configuración para Cloudflare Pages (headers de seguridad y redirects).

## Flujo end-to-end (detalle)

1. GitHub Actions corre `scripts/pipeline.py` (cron o manual).
2. El pipeline:
   1. carga config y catálogo (`config/campus.yml`),
   2. autentica en Moodle,
   3. descarga recursos a un directorio temporal (`/tmp/kdef-moodle-*/...`),
   4. decide qué procesar según `data/manifest.json`,
   5. para cada archivo nuevo/modificado:
      - genera un resumen Markdown con LLM,
      - extrae fechas importantes como JSON machine-readable,
      - escribe un `.md` en `content/notas-automaticas/...` con frontmatter + contenido,
      - actualiza el manifest (`data/manifest.json`).
   6. regenera `content/notas-automaticas/{slug}/fechas-importantes.md` por materia.
3. Si hubo cambios, el workflow commitea `content/notas-automaticas/` + `data/manifest.json`.
4. Un segundo job construye el sitio (`npx quartz build`) y despliega `public/` a Cloudflare Pages.

## Invariantes del sistema

- `content/notas-automaticas/` se genera únicamente a través del pipeline.
- El calendario agregado se deriva **solo** del frontmatter de páginas generadas (no del body).
- El pipeline es "best-effort": errores por documento no bloquean el resto, pero el proceso finaliza con exit code != 0 si hubo errores (para que GH Actions marque fallo).
