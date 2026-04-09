"""
catalog.py — Campus subject catalog loader

Carga el catálogo declarativo de materias desde config/campus.yml y
selecciona las materias a trackear en base a TRACKED_SUBJECTS.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import yaml

log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CATALOG_PATH = REPO_ROOT / "config" / "campus.yml"


def load_campus_catalog(catalog_path: Path = DEFAULT_CATALOG_PATH) -> dict:
    """Load the campus catalog YAML file."""
    if not catalog_path.exists():
        log.warning("No existe %s — se usará un catálogo vacío", catalog_path)
        return {"campus": {}, "subjects": []}

    raw = catalog_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError(f"El archivo {catalog_path} debe contener un mapping YAML")

    data.setdefault("campus", {})
    data.setdefault("subjects", [])
    if not isinstance(data["subjects"], list):
        raise ValueError("'subjects' en campus.yml debe ser una lista")

    return data


def parse_tracked_subjects(value: str | None) -> set[str] | None:
    """Parse TRACKED_SUBJECTS from env. `all` or empty means all enabled."""
    if value is None:
        return None

    normalized = value.strip()
    if not normalized or normalized.lower() == "all":
        return None

    tracked = {item.strip().lower() for item in normalized.split(",") if item.strip()}
    return tracked or None


def select_tracked_subjects(catalog: dict, tracked_subjects: set[str] | None) -> list[dict]:
    """Return only enabled subjects that match TRACKED_SUBJECTS (or all enabled)."""
    subjects = [subject for subject in catalog.get("subjects", []) if isinstance(subject, dict)]
    enabled = [subject for subject in subjects if subject.get("enabled", True)]

    if tracked_subjects is None:
        return enabled

    return [
        subject
        for subject in enabled
        if str(subject.get("slug", "")).lower() in tracked_subjects
    ]


def get_course_ids(subjects: Iterable[dict]) -> list[str]:
    """Extract Moodle course IDs from a list of subject entries."""
    course_ids: list[str] = []
    for subject in subjects:
        course_id = subject.get("moodle_course_id")
        if course_id in (None, ""):
            continue
        course_ids.append(str(course_id))
    return course_ids
