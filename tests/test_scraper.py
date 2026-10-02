from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import requests

from scripts.scraper import (
    _decode_mojibake,
    _extension_from_url,
    _extract_section_number,
    _get_within_host,
    _is_youtube_url,
    _section_dirname,
    _slugify,
)


class SlugifyTests(unittest.TestCase):
    def test_normalizes_accented_chars(self):
        self.assertEqual(_slugify("Análisis I"), "analisis-i")

    def test_lowercases_result(self):
        self.assertEqual(_slugify("HELLO"), "hello")

    def test_replaces_spaces_with_hyphens(self):
        self.assertEqual(_slugify("hello world"), "hello-world")

    def test_collapses_multiple_hyphens(self):
        # Double space → double hyphen → collapsed to single
        self.assertEqual(_slugify("a  b"), "a-b")

    def test_strips_leading_trailing_hyphens(self):
        self.assertEqual(_slugify("  hello  "), "hello")

    def test_empty_string_returns_fallback(self):
        self.assertEqual(_slugify(""), "item")

    def test_non_alphanumeric_special_chars_removed(self):
        self.assertEqual(_slugify("a!@#b"), "ab")

    def test_already_clean_slug_unchanged(self):
        self.assertEqual(_slugify("semana-1"), "semana-1")


class SectionDirnameTests(unittest.TestCase):
    def test_date_range_with_slash_separators(self):
        self.assertEqual(_section_dirname("Semana 1 - 06/04 al 10/04"), "04-06-a-04-10")

    def test_date_range_pads_single_digit_days(self):
        self.assertEqual(_section_dirname("Clase 6/4 al 10/4"), "04-06-a-04-10")

    def test_no_date_range_falls_back_to_slugify(self):
        result = _section_dirname("Introducción al curso")
        self.assertIn("introducci", result)

    def test_generic_title_slugified(self):
        self.assertEqual(_section_dirname("Semana General"), "semana-general")


class DecodeMojibakeTests(unittest.TestCase):
    def test_decodes_latin1_interpreted_as_utf8(self):
        # "Presentación" encoded as UTF-8, then misread as latin-1 — classic Moodle bug
        mojibake = "Presentación".encode("utf-8").decode("latin-1")
        self.assertEqual(_decode_mojibake(mojibake), "Presentación")

    def test_passes_through_clean_ascii(self):
        self.assertEqual(_decode_mojibake("Clase 0"), "Clase 0")

    def test_returns_original_when_roundtrip_fails(self):
        # Characters outside latin-1 range can't encode to latin-1 → returns as-is
        result = _decode_mojibake("中文")
        self.assertEqual(result, "中文")


class IsYouTubeUrlTests(unittest.TestCase):
    def test_youtube_com_is_detected(self):
        self.assertTrue(_is_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_youtu_be_is_detected(self):
        self.assertTrue(_is_youtube_url("https://youtu.be/abc123"))

    def test_vimeo_is_not_youtube(self):
        self.assertFalse(_is_youtube_url("https://vimeo.com/123"))

    def test_moodle_url_is_not_youtube(self):
        self.assertFalse(_is_youtube_url("https://campus.fadena.undef.edu.ar/course/view.php?id=548"))


class ExtensionFromUrlTests(unittest.TestCase):
    def test_pdf_url(self):
        self.assertEqual(_extension_from_url("https://example.com/file.pdf"), ".pdf")

    def test_docx_with_query_string(self):
        self.assertEqual(_extension_from_url("https://example.com/doc.docx?token=abc"), ".docx")

    def test_trailing_slash_path_returns_empty(self):
        # Directorio sin nombre de archivo → sin extensión
        self.assertEqual(_extension_from_url("https://example.com/course/"), "")

    def test_percent_encoded_filename(self):
        self.assertEqual(_extension_from_url("https://example.com/Cronograma%20ALG.pdf"), ".pdf")


class ExtractSectionNumberTests(unittest.TestCase):
    def test_extracts_section_from_query(self):
        self.assertEqual(
            _extract_section_number("https://example.com/course?id=548&section=3"), "3"
        )

    def test_returns_none_when_no_section_param(self):
        self.assertIsNone(_extract_section_number("https://example.com/course?id=548"))

    def test_returns_none_for_empty_section_value(self):
        self.assertIsNone(_extract_section_number("https://example.com/course?section="))


def _fake_response(status: int, location: str | None = None) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    if location is not None:
        response.headers["Location"] = location
    return response


class GetWithinHostTests(unittest.TestCase):
    BASE_HOST = "campus.example.edu"

    def test_returns_response_when_no_redirect(self):
        session = MagicMock()
        session.get.return_value = _fake_response(200)
        url = "https://campus.example.edu/mod/page/view.php?id=1"
        final_url, response = _get_within_host(session, url, self.BASE_HOST)
        self.assertEqual(final_url, url)
        self.assertIsNotNone(response)

    def test_follows_relative_redirect_on_same_host(self):
        session = MagicMock()
        session.get.side_effect = [
            _fake_response(303, "/pluginfile.php/1/a.pdf"),
            _fake_response(200),
        ]
        final_url, response = _get_within_host(
            session, "https://campus.example.edu/mod/resource/view.php?id=2", self.BASE_HOST
        )
        self.assertEqual(final_url, "https://campus.example.edu/pluginfile.php/1/a.pdf")
        self.assertIsNotNone(response)

    def test_stops_at_external_redirect_without_requesting_it(self):
        session = MagicMock()
        session.get.return_value = _fake_response(303, "https://www.youtube.com/watch?v=abc")
        final_url, response = _get_within_host(
            session, "https://campus.example.edu/mod/url/view.php?id=3", self.BASE_HOST
        )
        self.assertEqual(final_url, "https://www.youtube.com/watch?v=abc")
        self.assertIsNone(response)
        session.get.assert_called_once()

    def test_raises_on_http_error_within_host(self):
        session = MagicMock()
        session.get.return_value = _fake_response(500)
        with self.assertRaises(requests.HTTPError):
            _get_within_host(session, "https://campus.example.edu/mod/url/view.php?id=4", self.BASE_HOST)

    def test_raises_on_redirect_loop(self):
        session = MagicMock()
        session.get.return_value = _fake_response(302, "/loop")
        with self.assertRaises(requests.TooManyRedirects):
            _get_within_host(session, "https://campus.example.edu/loop", self.BASE_HOST, max_redirects=3)


if __name__ == "__main__":
    unittest.main()
