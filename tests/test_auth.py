from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from scripts.auth import fetch_login_token, session_looks_authenticated


def _mock_response(html: str) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status = MagicMock()
    return resp


class FetchLoginTokenTests(unittest.TestCase):
    def test_returns_token_from_login_form(self):
        html = '<input name="logintoken" value="abc123" />'
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        token = fetch_login_token(session, "https://moodle.example.com")
        self.assertEqual(token, "abc123")

    def test_raises_when_token_input_missing(self):
        html = "<html><body>No token here</body></html>"
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        with self.assertRaises(RuntimeError):
            fetch_login_token(session, "https://moodle.example.com")

    def test_raises_when_token_value_is_empty(self):
        html = '<input name="logintoken" value="" />'
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        with self.assertRaises(RuntimeError):
            fetch_login_token(session, "https://moodle.example.com")

    def test_trailing_slash_stripped_from_url(self):
        html = '<input name="logintoken" value="tok" />'
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        fetch_login_token(session, "https://moodle.example.com/")
        called_url = session.get.call_args[0][0]
        self.assertFalse(called_url.startswith("https://moodle.example.com//"))


class SessionLooksAuthenticatedTests(unittest.TestCase):
    def test_dashboard_page_returns_true(self):
        html = "<html><body><h1>Dashboard</h1></body></html>"
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        result = session_looks_authenticated(session, "https://moodle.example.com")
        self.assertTrue(result)

    def test_page_with_username_field_returns_false(self):
        html = '<form><input name="username" /><input name="password" /></form>'
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        result = session_looks_authenticated(session, "https://moodle.example.com")
        self.assertFalse(result)

    def test_page_with_login_form_class_returns_false(self):
        html = '<form id="login-form"><p>Ingresá tus credenciales</p></form>'
        session = MagicMock()
        session.get.return_value = _mock_response(html)

        result = session_looks_authenticated(session, "https://moodle.example.com")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
