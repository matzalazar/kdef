---
title: "03 — fórmulas LaTeX"
date: 2026-04-12
tags: [meta, troubleshooting, summarizer, llm, latex, quartz]
---

# 03. Fórmulas LaTeX sin renderizar: `\[...\]` en lugar de `$$...$$`

## Síntomas

En los resúmenes generados de materiales con contenido matemático (álgebra, análisis, probabilidad), las fórmulas aparecían como texto plano en el sitio. En lugar de renderizar la expresión, Quartz mostraba literalmente los caracteres de control:

```
La fórmula general es \[E = mc^2\] donde \(m\) es la masa en reposo.
```

El markdown del archivo `.md` generado contenía las fórmulas correctas conceptualmente, pero con delimitadores que KaTeX no reconocía.

## Hipótesis iniciales

**Hipótesis 1 — Quartz sin soporte LaTeX configurado.**
El plugin `latex.ts` de Quartz es opcional y debe incluirse explícitamente en la configuración.

Descartada: `quartz/plugins/transformers/latex.ts` existe y está registrado en `quartz.config.ts`. El renderizado funciona correctamente cuando el markdown usa `$...$` o `$$...$$` — el problema era exclusivamente el formato de los delimitadores en el output del LLM.

**Hipótesis 2 — el modelo usa la notación canónica de LaTeX en lugar de la de Markdown.**
Los LLMs suelen generar texto válido para compiladores LaTeX (`.tex`), donde `\[...\]` y `\(...\)` son las formas estándar de abrir entornos matemáticos. Esa notación no es la que espera KaTeX embebido en un sitio web.

Confirmada.

## Debugging

Se tomaron resúmenes generados por `gpt-4o-mini` de apuntes de álgebra y análisis I y se buscaron los patrones:

```bash
grep -n '\\\[' content/notas-automaticas/**/*.md
grep -n '\\\(' content/notas-automaticas/**/*.md
```

Todos los archivos de materias con contenido matemático tenían ocurrencias. El modelo usaba consistentemente `\[...\]` para display math y `\(...\)` para inline math, ignorando las instrucciones de formato del system prompt que solo decían "usar markdown limpio".

Se verificó además que KaTeX (el motor que usa Quartz) acepta `\[...\]` solo si se configura explícitamente con `trust: true` y opciones adicionales — configuración que no queremos para un jardín de conocimiento público. La notación `$...$` y `$$...$$` funciona out-of-the-box.

## Root cause

Los modelos de lenguaje son entrenados sobre grandes corpus de texto donde `\[...\]` y `\(...\)` son los delimitadores LaTeX más frecuentes (LaTeX nativo, papers de arXiv, StackExchange). La notación con `$` también es común, pero el modelo no tiene preferencia fuerte a menos que se le indique explícitamente.

El system prompt original no incluía ninguna instrucción sobre delimitadores matemáticos. Al pedirle "markdown limpio adecuado para Quartz", el modelo interpretaba "markdown" como un estilo general de escritura, no como una restricción sobre la notación matemática.

El problema se reproducía de forma consistente en `gpt-4o-mini` y también apareció esporádicamente en el modelo de OpenRouter. La severidad dependía del contenido: documentos sin fórmulas no se veían afectados.

## Resolución

Se adoptó un enfoque de dos capas en `scripts/summarizer.py`:

**Capa 1 — instrucción explícita en el prompt:**
Se agregó la regla 15 al `SYSTEM_PROMPT`, con ejemplos concretos de lo permitido y lo prohibido:

```
15. Para expresiones matemáticas y fórmulas usar EXCLUSIVAMENTE delimitadores LaTeX de Markdown:
    - Inline: $expresión$ (ejemplo: $E = mc^2$, $\alpha$, $x_i$)
    - Display/bloque: $$expresión$$ en su propia línea (ejemplo: $$\sum_{i=1}^{n} x_i$$)
    - PROHIBIDO usar \(...\) o \[...\] bajo cualquier circunstancia — Quartz no los renderiza
```

**Capa 2 — normalización post-generación:**
Se implementó `_normalize_latex_delimiters(text)`, aplicada a `raw_summary` antes de pasarlo a `parse_llm_calendar_payload`:

```python
_LATEX_DISPLAY_RE = re.compile(r'\\\[(.+?)\\\]', re.DOTALL)
_LATEX_INLINE_RE  = re.compile(r'\\\((.+?)\\\)')

def _normalize_latex_delimiters(text: str) -> str:
    text = _LATEX_DISPLAY_RE.sub(r'$$\1$$', text)
    text = _LATEX_INLINE_RE.sub(r'$\1$', text)
    return text
```

El orden importa: display math primero, para que el patrón inline no capture fragmentos de una expresión multilinea que empiece con `\(`.

La función se aplica al output de los tres proveedores (GitHub Models, OpenRouter, Gemini) antes del chequeo de truncamiento.

## Lección

Los prompts son guías, no contratos. Para propiedades de formato que tienen consecuencias visibles en el renderizado final (delimitadores, sintaxis de bloques de código, estructura de frontmatter), no alcanza con describir el resultado esperado en términos generales: hay que prohibir explícitamente las alternativas indeseadas y, además, implementar un post-procesamiento determinista como red de seguridad.

La combinación de instrucción explícita + corrección post-generación es más robusta que cualquiera de las dos por separado: el prompt reduce la frecuencia del error, la función lo elimina cuando igual ocurre.
