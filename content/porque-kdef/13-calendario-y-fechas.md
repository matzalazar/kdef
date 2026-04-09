---
title: "13 — calendario y fechas"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 13. Feature: eventos académicos + calendario agregado

Implementado en `scripts/academic_calendar.py`. Cumple tres responsabilidades:

1. Parsear y normalizar eventos detectados por el LLM (`kdef-events`).
2. Renderizar una sección "Fechas importantes" dentro de cada página generada.
3. Agregar eventos de todo `content/notas-automaticas/` en una página `fechas-importantes.md` por materia.

## 13.1 Schema de evento (normalizado)

Un evento normalizado es un `dict[str, str]` con:

**Requeridos:**
- `title` (string)
- `kind` (string): `parcial|final|examen|entrega|clase|otro`
- `date_text` (string): texto original o fallback a `date_iso`

**Opcionales:**
- `date_iso` (`YYYY-MM-DD`) — solo si es fecha confirmada.
- `time_text` (string)
- `details` (string)
- `source_excerpt` (string)

Reglas:
- Un evento DEBE tener `title` y al menos `date_iso` o `date_text`.
- `kind` se normaliza por aliases (`EVENT_KIND_ALIASES`).
- `date_iso` solo se acepta si `date.fromisoformat` lo valida.

**Schema JSON esperado del LLM:**

```json
{
  "title": "Primer Parcial",
  "kind": "parcial|final|examen|entrega|clase|otro",
  "date_iso": "YYYY-MM-DD",
  "date_text": "texto original de la fecha",
  "time_text": "hora si existe",
  "details": "contexto breve",
  "source_excerpt": "fragmento del material"
}
```

## 13.2 Parseo del payload del LLM

Función: `parse_llm_calendar_payload(raw_summary) -> (markdown, events)`.

El LLM DEBE devolver, al final del markdown, un único fence `kdef-events` con JSON:

````text
```kdef-events
{"important_dates": [...]}
```
````

- Si no existe, retorna el markdown original y una lista vacía.
- Si existe:
  - elimina el bloque del cuerpo visible,
  - parsea JSON y extrae `important_dates`,
  - normaliza cada evento.

## 13.3 Almacenamiento en el frontmatter

Las fechas detectadas se escriben en el frontmatter de cada `.md` generado:

```yaml
important_dates:
  - title: Primer Parcial
    kind: parcial
    date_iso: '2026-05-21'
    date_text: 21 de mayo de 2026
    details: Unidades 1 a 3
```

Si el LLM no detecta fechas: `important_dates: []`.

## 13.4 Sección por documento: "Fechas importantes"

Función: `render_important_dates_section(events) -> str`.

- Si no hay eventos: retorna string vacío (no renderiza sección).
- Si hay:
  - ordena por `date_iso` primero; luego por `date_text`.
  - renderiza bullets con:
    - etiqueta de fecha (`date_iso` o `date_text`)
    - `kind` como código (`` `parcial` ``)
    - `title` en negrita
    - extras (`time_text`, `details`) en texto.

## 13.5 Agregación de calendario (página `.md`)

### Recolección de entradas

Función: `collect_calendar_entries(content_auto_dir) -> list[dict]`.

- Recorre `content_auto_dir.rglob("*.md")`.
- Excluye la página calendario legacy y el índice raíz de auto.
- Por cada markdown: lee frontmatter, toma `important_dates` si es lista.
- Deduplica por `source_origin`:
  - `source_origin = frontmatter.source_path` si existe; si no, usa el path del archivo.
  - conserva solo la página con `generated_at` más reciente.

Luego enriquece cada evento con: `source_title`, `source_path`, `source_origin`, `subject`.

### Render de la página por materia

Función: `render_subject_calendar_page(subject_slug, entries, content_auto_dir, generated_at) -> str`.

- Dos secciones:
  - "Con fecha confirmada" (solo `date_iso`), agrupado por mes.
  - "Sin fecha exacta" (sin `date_iso`).
- Los ítems incluyen link relativo hacia la página fuente. El texto del link se construye desde el path relativo para que sea legible y estable:

```
analisis-i / 06-04-a-10-04 / 2026-04-08-cronograma
```

## 13.6 Escritura de outputs

Función: `write_calendar_outputs(content_auto_dir, generated_at) -> entries`.

- Por cada materia con eventos: escribe `content/notas-automaticas/{slug}/fechas-importantes.md`.
- No genera feed `.ics` en la implementación actual (el helper `render_calendar_ics` existe, pero no se invoca).

## Limitaciones actuales

| Situación | Comportamiento |
|---|---|
| PDF escaneado (sin texto) | Se omite; el pipeline genera un placeholder con link a Moodle |
| PDF > 30 páginas | Se omite |
| Fecha ambigua sin `date_iso` | Aparece en "Sin fecha exacta" |
| LLM no detecta fechas | `important_dates: []` y no se renderiza sección en el doc |
| Documento reprocesado | Se usa la versión más reciente en el calendario agregado |

## Posibles mejoras

- Permitir agregar fechas manualmente vía PR (en notas colaborativas).
- Vista unificada de todas las materias.
- Publicar feed `.ics` por materia (solo eventos con `date_iso` confirmado).
