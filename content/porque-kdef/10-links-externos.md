---
title: "10 — links externos"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 10. Links externos — Criterio de inclusión en el garden

## Problema

Moodle incluye muchos links externos sin valor académico para el garden: redes sociales de la institución, links de descarga de la app móvil de Moodle, formularios de inscripción, etc. Incluirlos genera ruido en `content/notas-automaticas/`.

## Criterio actual

El scraper aplica la siguiente lógica para links externos (recursos que no son
archivos descargables):

| Tipo de link | Comportamiento |
|---|---|
| Video de YouTube (`youtube.com`, `youtu.be`) | Se registra como placeholder y se publica como nota en `content/notas-automaticas/` |
| Cualquier otro link externo | Se ignora silenciosamente (log en `DEBUG`) |

La lógica vive en `scripts/scraper.py`:

- `_is_youtube_url(url)` — detecta URLs de YouTube por netloc
- En el loop de `download_course_materials()`: solo se llama a `_write_link_placeholder()` si la URL es YouTube; cualquier otro link externo se descarta con `log.debug`

## Cómo agregar dominios permitidos

### Opción A — Agregar manualmente a `content/notas-colaborativas/`

La más simple. Crear un `.md` en `content/notas-colaborativas/{materia}/` con el link y una descripción. No requiere tocar el código y es la opción recomendada para links puntuales.

### Opción B — Extender el allowlist en el scraper

Para dominios que aparecen frecuentemente y siempre son relevantes (ej: todos los papers del repositorio institucional), agregar una función `_is_allowed_external_link(url)` en `scripts/scraper.py`:

```python
ALLOWED_EXTERNAL_DOMAINS = {
    "arxiv.org",
    "doi.org",
    "es.wikipedia.org",
    # agregar más según necesidad
}

def _is_allowed_external_link(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    return any(host == d or host.endswith("." + d) for d in ALLOWED_EXTERNAL_DOMAINS)
```

Luego en el loop de descarga:

```python
if resource.get("kind") == "link":
    url = resource["url"]
    if _is_youtube_url(url) or _is_allowed_external_link(url):
        # crear placeholder
    else:
        log.debug("Link externo ignorado: %s", url)
    continue
```

### Opción C — Allowlist por materia en `campus.yml`

Para control más fino (ej: solo para una materia específica), agregar una clave `allowed_external_domains` por subject en `config/campus.yml` y pasarla al scraper como parámetro. No está implementada — es trabajo futuro si se necesita.

## Placeholders generados para YouTube

Cuando el scraper encuentra un link de YouTube, crea un placeholder `.md` en el árbol temporal de descarga con frontmatter:

```yaml
kdef_skip: true
kdef_kind: "youtube"
source_url: "https://youtube.com/watch?v=..."
```

Ese placeholder entra al pipeline como si fuera "un archivo más". El pipeline detecta `kdef_skip: true` y genera una nota de salida en `content/notas-automaticas/` sin llamar al LLM (ver `scripts/pipeline.py` → `write_placeholder_output`).
