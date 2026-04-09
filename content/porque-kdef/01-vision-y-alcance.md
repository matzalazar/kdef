---
title: "01 — visión y alcance"
date: 2026-04-08
tags: [meta, docs]
---

# 01. Visión y alcance

## Visión

`kdef` es un jardín de conocimiento automatizado para estudiantes de la Licenciatura en Ciberdefensa (UNDEF, Argentina). El sistema:

- descarga materiales desde Moodle,
- genera resúmenes estructurados en Markdown con LLMs,
- detecta fechas académicas relevantes,
- publica el resultado como un sitio estático navegable y buscable,
- permite notas colaborativas escritas por los propios estudiantes.

## Principios de diseño

- **Simple y replicable**: configuración por variables de entorno + un catálogo declarativo (`config/campus.yml`).
- **Bajo costo**: procesamiento incremental (manifest SHA-256) para minimizar llamadas a LLM.
- **Separación de ownership**:
  - `content/notas-automaticas/` lo escribe el pipeline.
  - `content/notas-colaborativas/` lo escriben humanos vía PRs.
- **Tolerancia a fallos por documento**: si un documento falla, el pipeline **continúa** con el resto (ver `scripts/pipeline.py`).

## Usuarios y actores

- **Estudiantes**: navegan el sitio, buscan contenidos y consultan fechas importantes por materia.
- **Contribuidores**: agregan y mantienen notas en `content/notas-colaborativas/`.
- **Mantenedor/a**: administra secrets, controla el workflow, ajusta prompts y pipeline.

## Alcance funcional

- Actualización automática periódica (cron) desde GitHub Actions.
- Generación de resúmenes Markdown por documento descargado (cuando el tipo esté soportado).
- Extracción estructurada de fechas por documento y agregación en:
  - página de fechas por materia (`content/notas-automaticas/{slug}/fechas-importantes.md`)
- Publicación como sitio estático con Quartz + deploy en Cloudflare Pages.

## Fuera de alcance

- Reemplazar a Moodle o a la comunicación institucional.
- Garantizar corrección absoluta de interpretaciones del LLM (se señala explícitamente **no inventar** y declarar incertidumbre).
- Procesamiento de formatos no soportados (ej. imágenes escaneadas sin OCR; ver limitaciones en `./12-summarizer-llm.md`).

## Importante

No se permite ni se aceptarán PRs con modelos de exámenes o contenido que fomente cualquier tipo de fraude académico.

---

Siguiente recomendado:
- Tour end-to-end: `./02-como-funciona.md`
- Detalle técnico: `./04-arquitectura-y-flujo.md`
