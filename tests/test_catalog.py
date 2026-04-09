from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.catalog import (
    get_course_ids,
    load_campus_catalog,
    parse_tracked_subjects,
    select_tracked_subjects,
)


class ParseTrackedSubjectsTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(parse_tracked_subjects(None))

    def test_all_returns_none(self):
        self.assertIsNone(parse_tracked_subjects("all"))

    def test_empty_string_returns_none(self):
        self.assertIsNone(parse_tracked_subjects(""))

    def test_whitespace_only_returns_none(self):
        self.assertIsNone(parse_tracked_subjects("   "))

    def test_all_case_insensitive(self):
        self.assertIsNone(parse_tracked_subjects("ALL"))
        self.assertIsNone(parse_tracked_subjects("All"))

    def test_single_slug(self):
        result = parse_tracked_subjects("analisis-i")
        self.assertEqual(result, {"analisis-i"})

    def test_multiple_slugs(self):
        result = parse_tracked_subjects("analisis-i,algebra-i")
        self.assertEqual(result, {"analisis-i", "algebra-i"})

    def test_strips_whitespace_from_slugs(self):
        result = parse_tracked_subjects("  analisis-i  ,  algebra-i  ")
        self.assertEqual(result, {"analisis-i", "algebra-i"})

    def test_normalizes_to_lowercase(self):
        result = parse_tracked_subjects("ANALISIS-I")
        self.assertEqual(result, {"analisis-i"})


class SelectTrackedSubjectsTests(unittest.TestCase):
    CATALOG = {
        "subjects": [
            {"slug": "analisis-i", "moodle_course_id": 548, "enabled": True},
            {"slug": "algebra-i", "moodle_course_id": 545, "enabled": True},
            {"slug": "ingles-i", "moodle_course_id": 546, "enabled": False},
        ]
    }

    def test_returns_all_enabled_when_tracked_is_none(self):
        result = select_tracked_subjects(self.CATALOG, None)
        slugs = [s["slug"] for s in result]
        self.assertEqual(slugs, ["analisis-i", "algebra-i"])

    def test_filters_to_tracked_slug(self):
        result = select_tracked_subjects(self.CATALOG, {"analisis-i"})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["slug"], "analisis-i")

    def test_excludes_disabled_subjects_even_when_tracked(self):
        result = select_tracked_subjects(self.CATALOG, {"ingles-i"})
        self.assertEqual(result, [])

    def test_empty_catalog(self):
        result = select_tracked_subjects({"subjects": []}, None)
        self.assertEqual(result, [])

    def test_unmatched_tracked_returns_empty(self):
        result = select_tracked_subjects(self.CATALOG, {"no-existe"})
        self.assertEqual(result, [])


class GetCourseIdsTests(unittest.TestCase):
    def test_extracts_ids_as_strings(self):
        subjects = [
            {"slug": "analisis-i", "moodle_course_id": 548},
            {"slug": "algebra-i", "moodle_course_id": 545},
        ]
        result = get_course_ids(subjects)
        self.assertEqual(result, ["548", "545"])

    def test_skips_subject_without_course_id(self):
        subjects = [
            {"slug": "sin-id"},
            {"slug": "algebra-i", "moodle_course_id": 545},
        ]
        result = get_course_ids(subjects)
        self.assertEqual(result, ["545"])

    def test_skips_none_course_id(self):
        subjects = [{"slug": "x", "moodle_course_id": None}]
        result = get_course_ids(subjects)
        self.assertEqual(result, [])

    def test_empty_input(self):
        self.assertEqual(get_course_ids([]), [])


class LoadCampusCatalogTests(unittest.TestCase):
    def test_missing_file_returns_empty_catalog(self):
        result = load_campus_catalog(Path("/no/existe/campus.yml"))
        self.assertEqual(result["subjects"], [])
        self.assertEqual(result["campus"], {})

    def test_loads_valid_yaml(self):
        with TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "campus.yml"
            catalog_path.write_text(
                "campus:\n  name: Test\nsubjects:\n  - slug: test\n    enabled: true\n",
                encoding="utf-8",
            )
            result = load_campus_catalog(catalog_path)
            self.assertEqual(len(result["subjects"]), 1)
            self.assertEqual(result["subjects"][0]["slug"], "test")

    def test_non_dict_yaml_raises_value_error(self):
        with TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "campus.yml"
            catalog_path.write_text("- item1\n- item2\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_campus_catalog(catalog_path)

    def test_subjects_not_list_raises_value_error(self):
        with TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "campus.yml"
            catalog_path.write_text("campus: {}\nsubjects: not-a-list\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_campus_catalog(catalog_path)


if __name__ == "__main__":
    unittest.main()
