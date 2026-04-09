---
title: "03 — decisiones de diseño"
date: 2026-04-08
tags: [meta, docs]
---

# 03. Decisiones de diseño

Estas son las decisiones que definieron cómo está hecho kdef. Algunas son obvias en retrospectiva; otras costaron varias iteraciones.

Contexto recomendado:
- Visión/alcance: [01 — visión y alcance](./01-vision-y-alcance)
- Flujo end-to-end: [02 — cómo funciona](./02-como-funciona)
- Arquitectura/contratos: [04 — arquitectura y flujo end-to-end](./04-arquitectura-y-flujo)

---

## Sin base de datos

Todo el estado del sistema vive en archivos. El manifest es un JSON en `data/`. Los resúmenes son `.md`. La configuración es YAML.

Esto hace que el proyecto sea trivial de clonar, de auditar y de portear a otro entorno. No hay nada que levantar antes de correr el pipeline.

## Markdown como formato central

Quartz consume markdown con frontmatter YAML. Eso define el formato de salida del pipeline. El LLM recibe instrucciones explícitas de generar markdown limpio compatible con Quartz.

El frontmatter tiene dos funciones: metadatos para el sitio (título, fecha, tags) y datos estructurados para el pipeline (fechas importantes, source path). El mismo archivo sirve para ambos usos.

## El LLM como etapa separada

La extracción de texto y la generación del resumen son dos pasos distintos. Esto permite:
- testear la extracción sin gastar cuota de API
- reemplazar el extractor (agregar OCR, por ejemplo) sin tocar el LLM
- cambiar de proveedor de LLM sin tocar la extracción

El pipeline no depende de un proveedor específico. Define un orden de preferencia (GitHub Models → OpenRouter → Gemini) y usa el primero que esté disponible.

## Procesamiento incremental

El manifest con SHA-256 por archivo evita reprocesar lo que no cambió. En un flujo semanal con materias que se actualizan poco, la mayoría de los archivos se saltan. Esto mantiene el costo de API bajo. Y, para el scope de este proyecto, con los rate limits de Github Models y OpenRouter, nulo.

El trade-off: si cambia el prompt o la lógica de extracción, hay que hacer `FORCE_REPROCESS=true` para regenerar todo. Es un costo aceptable.

## Tolerancia a fallos por documento

Si un archivo falla (PDF sin texto, cuota de LLM agotada, formato no soportado), el pipeline lo registra y continúa. Un archivo roto no mata la corrida entera.

Los documentos fallidos quedan como placeholders con link al original en Moodle, en vez de desaparecer.

## Nombres de una sola palabra

Los archivos generados usan solo la primera palabra del nombre original, en minúsculas y sin acentos. `CRONOGRAMA AMI -1C 2026.pdf` → `cronograma`.

Esto mantiene las URLs limpias y el explorador legible. El título completo del documento queda en el cuerpo del resumen generado por el LLM.

## Separación de zonas de contenido

`content/notas-automaticas/` es exclusivo del pipeline. `content/notas-colaborativas/` es exclusivo de contribuciones humanas. Esta separación hace que los conflictos de merge sean prácticamente imposibles y las responsabilidades estén claras.

## Quartz como sitio

Quartz es un generador de digital gardens basado en Obsidian. Tiene búsqueda, grafo de conexiones entre notas, tabla de contenidos y explorer de archivos. Todo eso sin configurar nada extra.

El único costo fue adaptar el output del pipeline al formato que Quartz espera (frontmatter estándar, links relativos, estructura de directorios coherente).
