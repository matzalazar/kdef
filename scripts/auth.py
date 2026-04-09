"""
auth.py — Moodle authentication helpers

Encapsula el login contra Moodle para que el scraper/pipeline no tengan
que repetir la lógica de obtención del logintoken y validación de sesión.

El módulo todavía es liviano a propósito:
  - fetch_login_token(): obtiene el token CSRF del formulario de login
  - create_moodle_session(): autentica y devuelve una Session válida
"""

from __future__ import annotations

import logging
from typing import Final

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

HTTP_TIMEOUT_SECONDS: Final = 30
USER_AGENT: Final = "kdef-bot/1.0 (student knowledge garden)"


def _base_url(moodle_url: str) -> str:
    """Strip trailing slash to avoid double-slash in constructed URLs."""
    return moodle_url.rstrip("/")


def fetch_login_token(session: requests.Session, moodle_url: str) -> str:
    """Fetch the login CSRF token from Moodle's login page."""
    login_url = f"{_base_url(moodle_url)}/login/index.php"
    response = session.get(login_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")
    token_input = soup.select_one('input[name="logintoken"]')
    # Moodle rota este token por sesión para prevenir CSRF — no cachearlo
    if token_input is None or not token_input.get("value"):
        raise RuntimeError("No se encontró logintoken en la página de login de Moodle")

    return str(token_input["value"])


def session_looks_authenticated(session: requests.Session, moodle_url: str) -> bool:
    """Check whether the current session has access to a protected page."""
    my_url = f"{_base_url(moodle_url)}/my/"
    response = session.get(my_url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()

    page = response.text.lower()
    return (
        'name="username"' not in page
        and 'name="password"' not in page
        and "login-form" not in page
    )


def create_moodle_session(moodle_url: str, username: str, password: str) -> requests.Session:
    """Create an authenticated Moodle session using the standard login form."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    login_url = f"{_base_url(moodle_url)}/login/index.php"
    token = fetch_login_token(session, moodle_url)

    response = session.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "logintoken": token,
        },
        timeout=HTTP_TIMEOUT_SECONDS,
        allow_redirects=True,
    )
    response.raise_for_status()

    if not session_looks_authenticated(session, moodle_url):
        raise RuntimeError("La autenticación en Moodle falló: revisar usuario y contraseña")

    log.info("Sesión autenticada correctamente contra Moodle")
    return session
