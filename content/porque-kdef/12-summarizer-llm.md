---
title: "12 — resúmenes con LLM"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 12. Feature: generación de resúmenes con LLM (summarizer)

## Objetivo

Tomar un archivo descargado (PDF/DOCX/PPTX/TXT/MD), extraer su texto y generar:

1. un resumen estructurado en Markdown para Quartz, y
2. un bloque machine-readable con eventos académicos (`important_dates`) para alimentar el calendario.

## Entradas

- `path: Path` — archivo local a procesar.
- `model: str` — nombre con prefijo de proveedor:
  - `github/<model>` (GitHub Models; API compatible con OpenAI)
  - `openrouter/<model>` (OpenRouter; API compatible con OpenAI)
  - `gemini/<model>` (Google Gemini; SDK `google-genai`)
  - `dry-run/mock` (placeholder)

## Salidas

`DocumentSummary` (ver `scripts/summarizer.py`):

- `markdown: str` — resumen visible.
- `important_dates: list[dict[str, str]]` — eventos normalizados.

## Extracción de texto

Código: `scripts/summarizer.py` → `extract_text()`.

| Tipo | Estrategia | Límite |
|---|---|---|
| `.pdf` | `pypdf` con marcadores `[Página N]` | `MAX_PDF_PAGES = 30` |
| `.docx` | `python-docx`, concatena párrafos no vacíos | — |
| `.pptx` | `python-pptx`, recorre slides y extrae `shape.text` | — |
| `.txt` / `.md` | lectura UTF-8 con `errors="replace"` | — |

**Limitación conocida**: PDFs escaneados sin texto seleccionable suelen fallar (no hay OCR implementado).

## Contrato del prompt y payload de eventos

El resumen se genera con dos prompts:

- `SYSTEM_PROMPT`: define reglas (idioma, estructura, no inventar, etc.).
- `USER_PROMPT_TEMPLATE`: inyecta `filename` y `content`.

**Contrato obligatorio de salida del LLM**: el LLM DEBE devolver, al final, un único code fence:

````text
```kdef-events
{"important_dates": [...]}
```
````

Ese bloque se parsea en `scripts/academic_calendar.py` (`parse_llm_calendar_payload`).

## Selección de proveedor LLM

Código: `scripts/summarizer.py` → `summarize_document()`.

- `github/...`:
  - usa `openai` SDK con `base_url="https://models.inference.ai.azure.com"`.
  - usa `GITHUB_MODELS_KEY` del entorno.
  - límite de input: 25.000 caracteres. `temperature=0.3`, `max_tokens=3800`.
- `openrouter/...`:
  - usa `openai` SDK con `base_url="https://openrouter.ai/api/v1"`.
  - usa `OPENROUTER_API_KEY` del entorno.
  - el system prompt se fusiona en el mensaje de usuario (compatibilidad con modelos sin rol `system`).
  - límite de input: 25.000 caracteres.
- `gemini/...`:
  - usa SDK `google-genai` (`google.genai.Client`).
  - usa `GEMINI_API_KEY` del entorno.
  - límite de input: 80.000 caracteres.
- `dry-run/mock`:
  - retorna un Markdown placeholder sin eventos.

## Reintentos (resiliencia)

Código: `scripts/summarizer.py` usa `tenacity`:

- `MAX_RETRY_ATTEMPTS = 4`
- backoff exponencial: min `15s`, max `120s`
- reintenta ante: `ConnectionError`, `TimeoutError`, `openai.RateLimitError` y equivalentes de Gemini.
- **No** reintenta ante errores de autenticación (401, 403) ni inputs inválidos (400).

## Errores esperables

- `DocumentTooLargeError`: PDF supera `MAX_PDF_PAGES` (30 páginas).
- `DocumentUnreadableError`: PDF sin texto extraíble (escaneado).
- `ValueError`: extensión no soportada o falta API key del proveedor.
- Excepciones del proveedor (OpenAI/Gemini): propagadas; el pipeline decide si continuar (ver [14 — orquestador del pipeline](./14-orquestador-pipeline)).
