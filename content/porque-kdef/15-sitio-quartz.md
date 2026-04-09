---
title: "15 — sitio quartz"
date: 2026-04-08
tags: [meta, docs, sitio]
---

# 15. Feature: sitio estático con Quartz

## Objetivo

Publicar el conocimiento (notas automáticas + notas colaborativas + documentación) como un sitio estático:

- navegable por carpetas y tags,
- con búsqueda,
- con grafo de enlaces,
- con soporte de markdown extendido.

## Comandos

Definidos en `package.json`:

- `npm run serve`: build Quartz + sirve en `http://localhost:8080`
- `npm run build`: build estático en `public/`
- `npm run check`: `tsc --noEmit` + `prettier --check`

## Configuración del sitio

Archivo: `quartz.config.ts`

- `locale: "es-AR"` (locale custom: mapea a `es-ES` porque Quartz no lo incluía nativamente)
- `baseUrl: "kdef.com.ar"`
- `fontOrigin: "local"` — sin Google Fonts, evita dependencias externas
- SPA + popovers habilitados.
- Tema con tipografía local (JetBrains Mono) y paleta terminal.
- Plugins habilitados:
  - frontmatter, fechas created/modified, syntax highlighting,
  - OMD + GFM, TOC, crawl links, description,
  - pages: content, folder, tags, index (RSS + sitemap), static, favicon, 404.

## Layout

Archivo: `quartz.layout.ts`

Incluye (entre otros):

- breadcrumbs (condicional),
- búsqueda, dark mode, reader mode,
- explorer, grafo, TOC (desktop), backlinks.

## Publicación de assets no markdown

Quartz copia archivos no-markdown bajo `content/` "as-is".

Si en el futuro el pipeline publica un `.ics`, Quartz lo servirá automáticamente junto al resto de archivos estáticos bajo `content/`.

## Docker

`Dockerfile`:

- Instala dependencias con `npm ci`.
- Ejecuta `npx quartz build --serve`.
