from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.pipeline import (
    CONTENT_AUTO_DIR,
    _first_word,
    _section_title_from_slug,
    build_output_path,
    get_relative_source_path,
    load_config,
)


class FirstWordTests(unittest.TestCase):
    def test_extracts_first_word_from_simple_name(self):
        self.assertEqual(_first_word("cronograma.pdf"), "cronograma")

    def test_strips_multiple_extensions_in_cascade(self):
        # .pdf is stripped, then .docx → leaves just "doc"
        self.assertEqual(_first_word("doc.docx.pdf"), "doc")

    def test_lowercases_result(self):
        self.assertEqual(_first_word("CRONOGRAMA.pdf"), "cronograma")

    def test_removes_accents(self):
        self.assertEqual(_first_word("Análisis.pdf"), "analisis")

    def test_multiword_filename_returns_first_word(self):
        self.assertEqual(_first_word("Clase 0 - Presentacion.pdf"), "clase")

    def test_underscore_separator_splits_correctly(self):
        self.assertEqual(_first_word("CRONOGRAMA_ALG.pdf"), "cronograma")

    def test_separator_only_name_returns_doc_fallback(self):
        # Nombre compuesto solo de separadores → no hay primera palabra válida
        self.assertEqual(_first_word("-_.pdf"), "doc")


class GetRelativeSourcePathTests(unittest.TestCase):
    def test_strips_temp_dir_prefix(self):
        path = Path("/tmp/kdef-moodle-abc123/analisis-i/semana-1/cronograma.pdf")
        result = get_relative_source_path(path)
        self.assertEqual(result, Path("analisis-i/semana-1/cronograma.pdf"))

    def test_falls_back_to_filename_without_prefix(self):
        path = Path("/some/other/path/file.pdf")
        result = get_relative_source_path(path)
        self.assertEqual(result, Path("file.pdf"))

    def test_handles_deep_nesting_under_prefix(self):
        path = Path("/tmp/kdef-moodle-xyz/algebra-i/06-04-a-10-04/CRONOGRAMA ALG.pdf")
        result = get_relative_source_path(path)
        self.assertEqual(result, Path("algebra-i/06-04-a-10-04/CRONOGRAMA ALG.pdf"))


class SectionTitleFromSlugTests(unittest.TestCase):
    def test_date_range_slug_formatted_with_slashes(self):
        self.assertEqual(_section_title_from_slug("06-04-a-10-04"), "06/04 al 10/04")

    def test_single_word_slug_returns_as_is(self):
        self.assertEqual(_section_title_from_slug("intro"), "intro")

    def test_hyphenated_slug_returns_first_segment(self):
        self.assertEqual(_section_title_from_slug("semana-1"), "semana")


class BuildOutputPathTests(unittest.TestCase):
    def test_output_name_includes_date_prefix(self):
        source = Path("/tmp/kdef-moodle-abc/analisis-i/semana-1/cronograma.pdf")
        now = datetime(2026, 4, 8, tzinfo=timezone.utc)
        result = build_output_path(source, now)
        self.assertTrue(result.name.startswith("2026-04-08-"))

    def test_output_is_under_content_auto_dir(self):
        source = Path("/tmp/kdef-moodle-abc/analisis-i/semana-1/cronograma.pdf")
        now = datetime(2026, 4, 8, tzinfo=timezone.utc)
        result = build_output_path(source, now)
        self.assertTrue(str(result).startswith(str(CONTENT_AUTO_DIR)))

    def test_output_preserves_subject_and_section_dirs(self):
        source = Path("/tmp/kdef-moodle-abc/algebra-i/06-04-a-10-04/programa.pdf")
        now = datetime(2026, 4, 8, tzinfo=timezone.utc)
        result = build_output_path(source, now)
        self.assertIn("algebra-i", result.parts)
        self.assertIn("06-04-a-10-04", result.parts)

    def test_output_file_has_md_extension(self):
        source = Path("/tmp/kdef-moodle-abc/ingles-i/semana-1/clase.pdf")
        now = datetime(2026, 4, 8, tzinfo=timezone.utc)
        result = build_output_path(source, now)
        self.assertEqual(result.suffix, ".md")


class LoadConfigTests(unittest.TestCase):
    def test_dry_run_false_by_default(self):
        with patch("scripts.pipeline.load_dotenv"), \
             patch.dict(os.environ, {
                 "DRY_RUN": "false",
                 "MOODLE_URL": "https://dummy.example.com",
                 "MOODLE_USER": "user",
                 "MOODLE_PASS": "pass",
             }, clear=False):
            config = load_config()
            self.assertFalse(config["dry_run"])

    def test_dry_run_true_from_env(self):
        with patch("scripts.pipeline.load_dotenv"), \
             patch.dict(os.environ, {"DRY_RUN": "true"}, clear=False):
            config = load_config()
            self.assertTrue(config["dry_run"])

    def test_force_reprocess_false_by_default(self):
        with patch("scripts.pipeline.load_dotenv"), \
             patch.dict(os.environ, {"DRY_RUN": "true", "FORCE_REPROCESS": "false"}, clear=False):
            config = load_config()
            self.assertFalse(config["force_reprocess"])

    def test_force_reprocess_true_from_env(self):
        with patch("scripts.pipeline.load_dotenv"), \
             patch.dict(os.environ, {"DRY_RUN": "true", "FORCE_REPROCESS": "true"}, clear=False):
            config = load_config()
            self.assertTrue(config["force_reprocess"])

    def test_tracked_subjects_all_resolves_to_none(self):
        with patch("scripts.pipeline.load_dotenv"), \
             patch.dict(os.environ, {"DRY_RUN": "true", "TRACKED_SUBJECTS": "all"}, clear=False):
            config = load_config()
            self.assertIsNone(config["tracked_subjects"])


if __name__ == "__main__":
    unittest.main()
