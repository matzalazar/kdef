from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.manifest import compute_file_hash, needs_processing


class ManifestKeyStabilityTests(unittest.TestCase):
    def test_skips_processing_when_stable_source_key_matches_hash(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "kdef-moodle-abc" / "analisis-i" / "semana-1" / "cronograma.pdf"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(b"contenido")

            digest = compute_file_hash(source_path)
            manifest = {
                "version": 1,
                "last_run": None,
                "files": {
                    "analisis-i/semana-1/cronograma.pdf": {
                        "sha256": digest,
                    }
                },
            }

            self.assertFalse(
                needs_processing(
                    source_path,
                    manifest,
                    source_key="analisis-i/semana-1/cronograma.pdf",
                )
            )

    def test_processes_when_stable_source_key_hash_changes(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "kdef-moodle-xyz" / "analisis-i" / "semana-1" / "cronograma.pdf"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(b"contenido nuevo")

            manifest = {
                "version": 1,
                "last_run": None,
                "files": {
                    "analisis-i/semana-1/cronograma.pdf": {
                        "sha256": "0" * 64,
                    }
                },
            }

            self.assertTrue(
                needs_processing(
                    source_path,
                    manifest,
                    source_key="analisis-i/semana-1/cronograma.pdf",
                )
            )

    def test_legacy_temp_path_key_still_works(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "kdef-moodle-old" / "analisis-i" / "semana-1" / "cronograma.pdf"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_bytes(b"contenido")

            digest = compute_file_hash(source_path)
            manifest = {
                "version": 1,
                "last_run": None,
                "files": {
                    str(source_path): {
                        "sha256": digest,
                    }
                },
            }

            self.assertFalse(
                needs_processing(
                    source_path,
                    manifest,
                    source_key="analisis-i/semana-1/cronograma.pdf",
                )
            )


if __name__ == "__main__":
    unittest.main()
