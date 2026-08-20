from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.summarizer import (
    DocumentTooLargeError,
    DocumentTruncatedError,
    DocumentUnreadableError,
    TransientProviderError,
    _openrouter_error_detail,
    extract_text,
)


class DocumentExceptionTests(unittest.TestCase):
    def test_truncated_error_stores_partial_markdown(self):
        exc = DocumentTruncatedError("contenido parcial aquí")
        self.assertEqual(exc.partial_markdown, "contenido parcial aquí")

    def test_truncated_error_empty_partial_by_default(self):
        exc = DocumentTruncatedError()
        self.assertEqual(exc.partial_markdown, "")

    def test_truncated_error_message_describes_truncation(self):
        exc = DocumentTruncatedError()
        self.assertIn("truncad", str(exc).lower())

    def test_too_large_error_is_exception(self):
        exc = DocumentTooLargeError("archivo.pdf tiene 50 páginas")
        self.assertIsInstance(exc, Exception)

    def test_unreadable_error_is_exception(self):
        exc = DocumentUnreadableError("sin texto extraíble")
        self.assertIsInstance(exc, Exception)


class ExtractTextDispatcherTests(unittest.TestCase):
    def test_unsupported_extension_raises_value_error(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "hoja.xlsx"
            path.write_bytes(b"dummy content")
            with self.assertRaises(ValueError) as ctx:
                extract_text(path)
            self.assertIn(".xlsx", str(ctx.exception))

    def test_txt_file_returns_content(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "nota.txt"
            path.write_text("contenido de prueba", encoding="utf-8")
            result = extract_text(path)
            self.assertEqual(result, "contenido de prueba")

    def test_md_file_returns_content(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "nota.md"
            content = "## Título\n\nContenido del apunte."
            path.write_text(content, encoding="utf-8")
            result = extract_text(path)
            self.assertEqual(result, content)

    def test_error_message_includes_unsupported_extension(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "video.mp4"
            path.write_bytes(b"not a document")
            with self.assertRaises(ValueError) as ctx:
                extract_text(path)
            self.assertIn(".mp4", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


class OpenRouterNullChoicesTests(unittest.TestCase):
    """OpenRouter responde 200 con choices=None cuando el upstream falla."""

    class _Response:
        def __init__(self, payload):
            self._payload = payload
            self.choices = payload.get("choices")

        def model_dump(self):
            return self._payload

    def _patched_call(self, response):
        """Ejecutar _summarize_with_openrouter con un cliente OpenAI falso."""
        import scripts.summarizer as summarizer

        class _Completions:
            def create(self, **kwargs):
                return response

        class _Chat:
            completions = _Completions()

        class _Client:
            chat = _Chat()

            def __init__(self, **kwargs):
                pass

        import openai

        original = openai.OpenAI
        openai.OpenAI = _Client
        try:
            return summarizer._summarize_with_openrouter("texto", "doc.pdf", "key", "modelo", "2026")
        finally:
            openai.OpenAI = original

    def test_null_choices_raises_transient_error(self):
        response = self._Response({
            "choices": None,
            "error": {"message": "Provider returned error", "code": 429},
        })
        with self.assertRaises(TransientProviderError) as ctx:
            self._patched_call(response)
        self.assertIn("doc.pdf", str(ctx.exception))
        self.assertIn("Provider returned error", str(ctx.exception))

    def test_empty_choices_raises_transient_error(self):
        response = self._Response({"choices": []})
        with self.assertRaises(TransientProviderError):
            self._patched_call(response)

    def test_error_detail_without_error_field(self):
        response = self._Response({"choices": None})
        self.assertEqual(_openrouter_error_detail(response), "sin detalle en la respuesta")

    def test_error_detail_formats_message_and_code(self):
        response = self._Response({"error": {"message": "rate limited", "code": 429}})
        self.assertEqual(_openrouter_error_detail(response), "rate limited (code=429)")

    def test_error_detail_survives_object_without_model_dump(self):
        self.assertEqual(_openrouter_error_detail(object()), "sin detalle en la respuesta")
