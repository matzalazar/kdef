from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.summarizer import (
    DocumentTooLargeError,
    DocumentTruncatedError,
    DocumentUnreadableError,
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
