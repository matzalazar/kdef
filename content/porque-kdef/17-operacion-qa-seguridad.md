---
title: "17 — qa y seguridad"
date: 2026-04-08
tags: [meta, docs, operacion]
---

# 17. Operación, QA y seguridad

## Operación local

**Sitio:**

```bash
npm install
npm run serve
```

**Pipeline:**

```bash
cp .env.example .env        # completar valores reales
pip install -r scripts/requirements.txt

DRY_RUN=true python scripts/pipeline.py   # simulación
python scripts/pipeline.py                 # ejecución real
```

## Tests

- Unit tests: `tests/test_calendar.py`, `tests/test_manifest.py`
- Comando: `python -m unittest discover -s tests`

## Smoke test recomendado

1. `cp .env.example .env` y completar valores.
2. `python -m unittest discover -s tests`.
3. `DRY_RUN=true python scripts/pipeline.py` — valida orquestación.
4. `python scripts/pipeline.py` en corrida controlada — valida Moodle + LLM.

## Observabilidad / debugging

- El pipeline usa logging "una línea" amigable con GitHub Actions.
- Si hay errores por documento, el pipeline:
  - continúa con los demás,
  - pero termina con exit code != 0 para visibilidad en CI.

## Seguridad y privacidad

### Secrets

- `.env` NO debe commitearse (ver `.gitignore`).
- Los secrets de Moodle y LLM son **credenciales sensibles**.

### Datos

- El contenido procesado proviene de Moodle (material académico).
- El LLM recibe texto extraído; se recomienda asumir que puede contener datos personales (nombres, emails, etc.), y por lo tanto requiere criterio al elegir proveedor y logs.

### Headers de seguridad (Cloudflare Pages)

Archivo `_headers` aplica:

- `Content-Security-Policy` restrictiva (con excepciones por Quartz),
- `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`, etc.

## Limitaciones actuales a monitorear

- PDFs escaneados sin OCR pueden no producir resumen usable.
- Reintentos del summarizer hoy se enfocan en errores de red (no todos los 429/5xx están cubiertos).
