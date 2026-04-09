---
title: "08 — autenticación en moodle"
date: 2026-04-08
tags: [meta, docs, pipeline]
---

# 08. Feature: autenticación en Moodle

## Objetivo

Crear una sesión autenticada contra Moodle usando el formulario estándar de login (CSRF token `logintoken`), de forma reutilizable por el scraper.

## Entradas

- `moodle_url` (string)
- `username` (string)
- `password` (string)

## Salidas

- `requests.Session` autenticada lista para acceder a páginas protegidas.

## API de módulo

Código: `scripts/auth.py`

- `fetch_login_token(session, moodle_url) -> str`
- `session_looks_authenticated(session, moodle_url) -> bool`
- `create_moodle_session(moodle_url, username, password) -> requests.Session`

## Flujo (contrato)

1. `fetch_login_token`:
   - GET `{moodle_url}/login/index.php`
   - parsea HTML y extrae `input[name="logintoken"]`.
   - si no existe, falla con `RuntimeError`.
2. `create_moodle_session`:
   - crea `requests.Session` y setea `User-Agent: kdef-bot/1.0 (...)`.
   - POST a `/login/index.php` con `username`, `password`, `logintoken`.
   - valida sesión llamando `session_looks_authenticated`.
3. `session_looks_authenticated`:
   - GET `{moodle_url}/my/`
   - heurística: el HTML no debe contener inputs típicos del login (`username`, `password`, `login-form`).

## Errores esperables

- Token CSRF no encontrado → `RuntimeError`.
- Credenciales inválidas o sesión no válida → `RuntimeError`.
- Errores HTTP (403/500) → `requests.HTTPError` por `raise_for_status()`.
- Timeouts de red → excepciones de `requests` (propagan).

## Consideraciones de seguridad

- El `password` nunca debe loguearse.
- La verificación de autenticación es heurística; si Moodle cambia el HTML, puede requerir ajuste.
