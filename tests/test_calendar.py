from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.academic_calendar import (
    dump_frontmatter,
    parse_llm_calendar_payload,
    write_calendar_outputs,
)


class ParseLlmCalendarPayloadTests(unittest.TestCase):
    def test_extracts_markdown_and_normalizes_events(self) -> None:
        raw = """## Resumen

Contenido principal.

```kdef-events
{"important_dates": [{"title": "Mesa de julio", "kind": "finales", "date_iso": "2026-07-15", "date_text": "15 de julio de 2026", "details": "Primer llamado"}]}
```"""

        markdown, events = parse_llm_calendar_payload(raw)

        self.assertEqual(markdown, "## Resumen\n\nContenido principal.")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Mesa de julio")
        self.assertEqual(events[0]["kind"], "final")
        self.assertEqual(events[0]["date_iso"], "2026-07-15")
        self.assertEqual(events[0]["details"], "Primer llamado")


class WriteCalendarOutputsTests(unittest.TestCase):
    def test_generates_markdown_calendar_and_ics_feed(self) -> None:
        with TemporaryDirectory() as tmp_dir:
            content_auto_dir = Path(tmp_dir) / "content" / "auto"
            subject_dir = content_auto_dir / "analisis" / "semana-1"
            subject_dir.mkdir(parents=True, exist_ok=True)

            old_page = subject_dir / "2026-04-01-cronograma.md"
            old_page.write_text(
                "\n".join(
                    [
                        dump_frontmatter(
                            {
                                "title": "Cronograma analisis",
                                "date": "2026-04-08",
                                "tags": ["auto-generado"],
                                "source_path": "analisis/semana-1/cronograma.pdf",
                                "generated_at": "2026-04-01T12:00:00+00:00",
                                "important_dates": [
                                    {
                                        "title": "Fecha vieja",
                                        "kind": "parcial",
                                        "date_iso": "2026-05-01",
                                        "date_text": "1 de mayo de 2026",
                                    },
                                ],
                            }
                        ).strip(),
                        "",
                        "## Resumen",
                        "",
                        "Cronograma detectado.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            generated_page = subject_dir / "2026-04-08-cronograma.md"
            generated_page.write_text(
                "\n".join(
                    [
                        dump_frontmatter(
                            {
                                "title": "Cronograma analisis",
                                "date": "2026-04-08",
                                "tags": ["auto-generado"],
                                "source_path": "analisis/semana-1/cronograma.pdf",
                                "generated_at": "2026-04-08T12:00:00+00:00",
                                "important_dates": [
                                    {
                                        "title": "Primer parcial",
                                        "kind": "parcial",
                                        "date_iso": "2026-05-12",
                                        "date_text": "12 de mayo de 2026",
                                        "details": "Unidades 1 a 3",
                                    },
                                    {
                                        "title": "Mesa final de julio",
                                        "kind": "final",
                                        "date_text": "julio de 2026",
                                        "details": "Sin día confirmado",
                                    },
                                ],
                            }
                        ).strip(),
                        "",
                        "## Resumen",
                        "",
                        "Cronograma detectado.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            entries = write_calendar_outputs(
                content_auto_dir,
                datetime(2026, 4, 8, 12, 0, tzinfo=timezone.utc),
            )

            self.assertEqual(len(entries), 2)

            # Página de fechas importantes por materia
            subject_page = (content_auto_dir / "analisis" / "fechas-importantes.md").read_text(encoding="utf-8")
            self.assertIn("fechas importantes", subject_page)
            self.assertIn("Primer parcial", subject_page)
            self.assertIn("Mesa final de julio", subject_page)
            self.assertNotIn("Fecha vieja", subject_page)


if __name__ == "__main__":
    unittest.main()
