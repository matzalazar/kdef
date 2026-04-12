---
title: "02 — resúmenes"
date: 2026-04-12
tags: [meta, troubleshooting, summarizer, llm, chunking]
---

# 02. Resúmenes incompletos en documentos de pocas páginas

## Síntomas

PDFs de entre 7 y 15 páginas generaban resúmenes que parecían cubrir solo la primera mitad del documento. El pipeline no reportaba ningún error, el archivo `.md` se escribía correctamente, pero el contenido del resumen se cortaba a mitad del desarrollo temático, omitiendo definiciones, ejemplos y secciones completas presentes en el original.

El problema era más pronunciado en materiales técnicos densos (apuntes de álgebra, análisis, sistemas operativos) que en documentos administrativos de la misma extensión.

## Hipótesis iniciales

**Hipótesis 1 — el documento realmente es escaso.**
La primera lectura del síntoma era que el PDF simplemente no tenía mucho contenido. Un PDF de 8 páginas podría tener figuras, gráficos o espaciado generoso que reducen el texto extraíble.

Descartada: al imprimir `len(text)` en los logs de debug, un PDF de 10 páginas de álgebra devolvía ~48.000 caracteres extraídos por `pypdf`. El contenido era denso y completo.

**Hipótesis 2 — truncamiento silencioso del input.**
El código enviaba `text[:MAX_INPUT_CHARS_GITHUB]` al LLM, con `MAX_INPUT_CHARS_GITHUB = 25_000`. Si `len(text) > 25_000`, solo se procesaba el primer 52% del documento sin ningún warning ni indicación al usuario.

Confirmada.

## Debugging

Se añadió un log de comparación antes de la llamada al LLM:

```python
if len(text) > MAX_INPUT_CHARS_GITHUB:
    log.warning(
        "Texto truncado: %d chars → %d chars enviados al LLM",
        len(text), MAX_INPUT_CHARS_GITHUB,
    )
```

Sobre una muestra de los PDFs problemáticos:

| Archivo | Páginas | Chars extraídos | Chars enviados | Cobertura |
|---|---|---|---|---|
| programa-algebra.pdf | 7 | 31.200 | 25.000 | 80% |
| apunte-integrales.pdf | 10 | 48.700 | 25.000 | 51% |
| tp-sistemas-operativos.pdf | 12 | 55.400 | 25.000 | 45% |

El LLM resumía solo lo que recibía. Para el apunte de integrales, las secciones de series y convergencia (páginas 6–10) no existían en el input — el modelo no podía resumirlas.

## Root cause

`MAX_INPUT_CHARS_GITHUB = 25_000` fue calibrado para el tier gratuito de GitHub Models, que tiene un límite de ~8k tokens de input por request. Para un documento de pocas páginas con texto poco denso (cronogramas, programas de materia), 25.000 caracteres cubre el 100% del contenido. Para materiales técnicos con notación matemática, definiciones extensas o ejemplos desarrollados, el límite se supera fácilmente.

El truncamiento con slice directo (`text[:N]`) no genera error, no actualiza el frontmatter del resumen, y no hay forma de distinguir en el output si el resumen es completo o parcial.

## Resolución

Se implementó un esquema de map-reduce en `_summarize_with_github_models` (`scripts/summarizer.py`):

1. **Ruta directa** (sin cambios): si `len(text) <= 25_000`, se envía en una sola llamada como antes.
2. **Ruta multi-chunk**: si el texto supera el límite, se divide en fragmentos de `CHUNK_SIZE_CHARS = 18_000` chars, intentando cortar en límites de párrafo (`\n\n`) para no romper oraciones.
3. **Fase map**: cada fragmento se procesa con `CHUNK_EXTRACT_PROMPT_TEMPLATE`, un prompt ligero que extrae conceptos clave, términos técnicos, fechas y referencias. Output máximo: 800 tokens por fragmento.
4. **Fase reduce**: las extracciones de todos los fragmentos se consolidan en una llamada final con `MERGE_PROMPT_TEMPLATE` y el `SYSTEM_PROMPT` completo, produciendo el resumen estructurado con el bloque `kdef-events`.

Para respetar el rate limit del tier gratuito (~15 req/min), se intercala un `time.sleep(INTER_CHUNK_DELAY_SECONDS)` de 20 segundos entre cada llamada. Un documento de 30 páginas densas (~144k chars → 8 fragmentos + 1 síntesis = 9 llamadas) tarda unos 3–4 minutos, lo cual es aceptable en un pipeline de CI.

El cap de `MAX_CHUNKS = 8` garantiza que documentos excepcionalmente largos no generen docenas de llamadas encadenadas.

## Lección

Truncar silenciosamente el input de un LLM no es equivalente a procesar un documento parcialmente — es equivalente a no haberlo leído. Un PDF de 10 páginas técnicas puede superar el límite de una sola llamada con facilidad, independientemente de su conteo de páginas.

Para APIs con ventanas de contexto reducidas, la solución no es bajar la calidad del input sino implementar map-reduce: extracciones ligeras por fragmento + síntesis final. Los costos en tiempo y llamadas son predecibles y acotables.
