---
title: "02 — cómo funciona"
date: 2026-04-08
tags: [meta, docs]
---

# 02. Cómo funciona

Si buscás el "por qué" y el alcance, empezá por [01 — visión y alcance](./01-vision-y-alcance). Si querés el desglose técnico por componente, ver [04 — arquitectura y flujo end-to-end](./04-arquitectura-y-flujo).

## La idea de fondo

El problema que intenta resolver kdef es simple: los materiales de la carrera viven dispersos en Moodle, en formatos distintos, sin una forma fácil de buscarlos o relacionarlos entre sí. Un jardín de conocimiento resuelve eso, pero construirlo a mano no escala. La respuesta fue automatizarlo.

Dos veces por semana, sin intervención humana, el sistema entra a Moodle, baja lo que cambió, lo resume con un modelo de lenguaje, extrae las fechas importantes y publica todo como un sitio estático navegable.

---

## El flujo

### 1. Configuración

Todo lo que varía entre instalaciones vive en dos lugares:

- `config/campus.yml` — qué materias trackear, con qué IDs de Moodle (ver [07 — catálogo de materias](./07-catalogo-de-materias))
- Variables de entorno (`.env` en local, secrets en GitHub Actions) — credenciales de Moodle y API keys de LLM (ver [06 — configuración y secrets](./06-configuracion-y-secrets))

No hay base de datos. No hay servidor. Todo es archivos.

### 2. Autenticación en Moodle

El scraper inicia sesión con usuario y contraseña, igual que lo haría un estudiante desde el navegador (ver [08 — autenticación en Moodle](./08-auth-moodle)).

### 3. Descarga de materiales

Por cada materia configurada, el scraper recorre las secciones (tiles) del curso y descarga los archivos adjuntos a un directorio temporal en `/tmp` (ver [09 — scraper de Moodle](./09-scraper-moodle)).

Links externos: hoy se registra solo YouTube como placeholder y el resto se ignora (ver [10 — links externos](./10-links-externos)).

### 4. Procesamiento incremental

Antes de enviar un archivo al LLM, el pipeline calcula su SHA-256 y lo compara con el manifest (`data/manifest.json`). Si ya fue procesado y no cambió, lo salta (ver [11 — manifest incremental](./11-manifest-incremental)).

### 5. Resumen con LLM

El texto extraído se envía a un modelo de lenguaje con un prompt que devuelve:
- un resumen estructurado en Markdown, y
- un bloque JSON con fechas académicas (ver [12 — resúmenes con LLM](./12-summarizer-llm)).

### 6. Fechas importantes

El bloque JSON del LLM se parsea, se normaliza y se guarda en el frontmatter del `.md` generado. Además:
- se renderiza una sección "Fechas importantes" al final del documento, y
- se agrega en una página `fechas-importantes.md` por materia (ver [13 — calendario y fechas](./13-calendario-y-fechas)).

### 7. Publicación

Los archivos `.md` generados se escriben en `content/notas-automaticas/`. GitHub Actions commitea los cambios, construye el sitio con Quartz y despliega a Cloudflare Pages.

Ver también: [16 — CI/CD y deploy](./16-ci-cd-y-deploy) y [15 — sitio con Quartz](./15-sitio-quartz).

---

## Outputs y ownership

- `content/notas-automaticas/` lo escribe el pipeline (no tocar a mano).
- `content/notas-colaborativas/` lo escriben humanos vía PRs.
- `content/porque-kdef/` es documentación del proyecto.

Para los contratos de frontmatter y los paths de salida, ver [05 — modelo de contenido](./05-modelo-de-contenido).

## Estructura de archivos (mapa rápido)

```
content/
  notas-automaticas/      ← pipeline-owned, no tocar
    analisis-i/
      06-04-a-10-04/
        2026-04-08-programa.md
      fechas-importantes.md
    algebra-i/
      ...
  notas-colaborativas/    ← zona humana, contribuciones vía PR
    analisis-i/
    algebra-i/
    ...
  porque-kdef/            ← documentación técnica y de producto

scripts/
  pipeline.py             ← orquestador
  catalog.py              ← catálogo/selección de materias
  auth.py                 ← autenticación Moodle
  scraper.py              ← descarga de Moodle
  summarizer.py           ← extracción de texto + LLM
  academic_calendar.py    ← fechas y calendario
  manifest.py             ← tracking incremental

config/
  campus.yml              ← catálogo de materias

data/
  manifest.json           ← registro de archivos procesados

.github/
  workflows/update-garden.yml  ← cron + ejecución del pipeline
```
