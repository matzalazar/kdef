---
title: "19 — copiar este modelo"
date: 2026-04-08
tags: [meta, replicacion, guia]
---

# 19. Copiar el modelo para otras carreras

Esta guía explica cómo reutilizar `kdef` para otra carrera (ej: Derecho, Ingeniería, Medicina) con el mismo esquema:

- `notas-automaticas/` → resúmenes automáticos del aula virtual
- `notas-colaborativas/` → notas de estudiantes
- `porque-kdef/` → documentación mínima del proyecto

## 1) Duplicar base del proyecto

1. Hacé un fork o copia de este repositorio.
2. Renombrá el branding y los textos visibles (`README.md`, `content/index.md`, `quartz.config.ts`).
3. Mantené la estructura base:

```
content/
  notas-automaticas/
  notas-colaborativas/
  porque-kdef/
scripts/
.github/workflows/update-garden.yml
```

## 2) Configurar fuente de materiales

En `config/campus.yml` definí tus materias:

```yaml
subjects:
  - slug: materia-uno
    name: "Nombre completo"
    moodle_course_id: 123
    enabled: true
```

En `scripts/scraper.py` ajustá la URL del aula virtual si es distinta a Moodle, o reemplazá el scraper por el conector de tu plataforma.

Variables de entorno necesarias: `MOODLE_URL`, `MOODLE_USER`, `MOODLE_PASS`.

## 3) Configurar el LLM

El pipeline intenta en orden: GitHub Models → OpenRouter → Gemini. Configurá al menos uno en `.env`:

- `GITHUB_MODELS_KEY`
- `OPENROUTER_API_KEY`
- `GEMINI_API_KEY`

El prompt está en español rioplatense porque el contenido es de la UNDEF. Ajustalo en `scripts/summarizer.py` si tu carrera es en otro idioma o contexto.

## 4) Activar la automatización

Usá `.github/workflows/update-garden.yml` con cron (recomendado: dos veces por semana) y `workflow_dispatch` para ejecución manual.

Checklist mínimo antes de lanzar:

- [ ] secrets cargados en GitHub
- [ ] pipeline corre sin errores (`DRY_RUN=true` para probar)
- [ ] se generan `.md` en `content/notas-automaticas/`
- [ ] deploy exitoso a Cloudflare Pages (o donde elijas)

## 5) Ajustar identidad del sitio

Editá:

- `content/index.md` — presentación
- `quartz.layout.ts` — componentes y footer
- `quartz/styles/custom.scss` — estética

## MVP mínimo viable

Para una primera versión, alcanza con:

- home breve
- `porque-kdef/04-arquitectura-y-flujo` y `porque-kdef/18-como-contribuir`
- 1-3 resúmenes en `notas-automaticas/`
- 1-3 notas en `notas-colaborativas/`

---

Si lo implementás para tu carrera, querés hacerlo, o tenés preguntas, [escribime](mailto:matias.zalazar@icloud.com).
