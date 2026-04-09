---
title: "01 — scraping Moodle: 0 archivos en Actions, funciona en local"
date: 2026-04-09
tags: [meta, troubleshooting, scraping, github-actions]
---

# 01. Scraping Moodle: 0 archivos en Actions, funciona en local

## Síntomas

El pipeline corría exitosamente en local y descargaba materiales de Moodle. En GitHub Actions, la autenticación era correcta (`Sesión autenticada correctamente`), los cursos se leían, pero el scraper devolvía siempre 0 archivos descargados:

```
Scraping completado — 0 archivo(s) descargado(s)
Pipeline completado — procesados: 0, saltados: 0, errores: 0
```

No había errores ni excepciones. El pipeline completaba silenciosamente sin procesar nada.

## Hipótesis iniciales

**Hipótesis 1 — exit node Tailscale.**
Antes de investigar este bug, ya se había resuelto un problema previo: Moodle bloqueaba las IPs de los runners de GitHub Actions (rangos de AWS). Para evitarlo, se configuró una Raspberry Pi propia como exit node de Tailscale, haciendo que todo el tráfico del runner saliera desde una IP residencial (Bahía Blanca, AR). Esa capa funciona correctamente y no era la causa del problema.

Durante el debugging se consideró si el ruteo por la Pi podía estar afectando el HTML devuelto por Moodle, pero se descartó: el tamaño del HTML era byte-a-byte idéntico entre local y Actions (`170699 bytes` para el mismo curso en ambos entornos). Misma cuenta, mismo momento.

**Hipótesis 2 — User-Agent.**
La sesión usa `kdef-bot/1.0 (student knowledge garden)` como User-Agent. La hipótesis era que Moodle detectaba el bot y servía una versión simplificada de la página sin `?section=N` en los links de tiles.

También descartada por el mismo motivo: HTML idéntico.

**Hipótesis 3 — tiles restringidos.**
Los logs de debugging mostraban que casi todos los tiles aparecían como `tile-restricted` en Actions, mientras que en local varios tiles estaban accesibles. Parecía que Moodle estaba ocultando contenido en Actions.

Descartada: el usuario confirmó estar logueado con la misma cuenta en el mismo momento y ver los tiles accesibles.

## Debugging

Se agregaron prints de diagnóstico marcados con `# DEBUG-RM` (reversibles con `sed -i '/# DEBUG-RM/d'`) en puntos clave del scraper:

- `list_course_resources`: tamaño del HTML, URL final, tiles encontrados por selector, tiles marcados como restringidos.
- `_tile_section_links`: conteo de `li[id^="tile-"]`, estado de cada tile (link encontrado, restringido).
- `_resources_from_section_page`: si el contenedor de sección fue encontrado, candidatos extraídos.

Output de Actions con debugging:

```
[DBG] curso 548 — elementos li[id^='tile-']: 2
[DBG] tile id=tile-1 | tile-link encontrado=True | restringido=False
[DBG] curso 548 — tiles encontrados: 0
[DBG] curso 548 — tiles restringidos: 1
```

Output de local con el mismo debugging:

```
[DBG] curso 548 — elementos li[id^='tile-']: 2
[DBG] tile id=tile-1 | tile-link encontrado=True | restringido=False
[DBG] curso 548 — tiles encontrados: 1
[DBG] curso 548 — tiles restringidos: 1
Explorando tile/sección 1: Presentación de la materia 06/04 al 10/04
[DBG] sección URL=.../course/view.php?id=548&section=1 | section_number=1 | container_encontrado=True
```

Los números de tiles y el estado de restricción eran idénticos. La diferencia: en local `tiles encontrados: 1`, en Actions `tiles encontrados: 0`.

El único filtro restante entre "tile-link encontrado" y "tiles encontrados" era `_extract_section_number(href)`. En local el href del tile era `course/view.php?id=548&section=1`; en Actions no tenía `?section=N` y la función devolvía `None`, descartando el tile.

## Root cause

**Diferencia de parser HTML entre entornos.**

`requirements.txt` declaraba `beautifulsoup4>=4.12.0` pero no fijaba el parser. BeautifulSoup acepta varios parsers (`html.parser`, `lxml`, `html5lib`) y el código usaba `"html.parser"` explícitamente. Sin embargo, el comportamiento de `html.parser` varía entre versiones de Python.

En local: Python con `lxml` instalado como dependencia transitiva de otro paquete. En Actions: entorno limpio de Ubuntu sin `lxml`, usando únicamente `html.parser` de stdlib.

Con el mismo HTML de entrada, `html.parser` y `lxml` parsean de forma diferente ciertos atributos de los tiles del plugin Tiles de Moodle. El resultado: los `href` de los elementos `a.tile-link` quedaban truncados o malformados con `html.parser`, sin el parámetro `?section=N`, haciendo que `_extract_section_number` devolviera `None` y todos los tiles fueran descartados.

## Resolución

1. Agregar `lxml>=4.9.0` a `scripts/requirements.txt` para garantizar su presencia en todos los entornos.
2. Reemplazar todas las instancias de `BeautifulSoup(html, "html.parser")` por `BeautifulSoup(html, "lxml")` en `scripts/scraper.py` y `scripts/auth.py` (6 ocurrencias).

Con lxml instalado y fijado como parser, el HTML de Moodle se parsea de forma consistente entre local y Actions, y los href de los tiles incluyen correctamente `?section=N`.

## Lección

Cuando BeautifulSoup no lanza errores pero el parsing produce resultados inesperados, la causa suele ser el parser. `html.parser` y `lxml` no son intercambiables con HTML complejo o no estándar. Fijar explícitamente `lxml` en requirements es la forma de garantizar paridad entre entornos.
