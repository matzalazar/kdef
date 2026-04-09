"""
calendar.py — helpers para fechas importantes y calendario agregado

Este módulo concentra la lógica relacionada con fechas académicas:
  - parsear el bloque estructurado que devuelve el LLM,
  - normalizar eventos importantes por documento,
  - renderizar una sección de fechas legible en markdown,
  - agregar todos los eventos publicados en content/auto/,
  - y emitir un feed .ics para importar en agendas externas.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

EVENTS_FENCE = "kdef-events"
CALENDAR_DIRNAME = "calendario"
CALENDAR_PAGE_NAME = "index.md"
CALENDAR_ICS_NAME = "fechas-importantes.ics"

MONTH_NAMES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

EVENT_KIND_ALIASES = {
    "parcial": "parcial",
    "parciales": "parcial",
    "final": "final",
    "finales": "final",
    "examen": "examen",
    "exámenes": "examen",
    "examenes": "examen",
    "entrega": "entrega",
    "deadline": "entrega",
    "clase": "clase",
    "otro": "otro",
}


def _clean_text(value: Any) -> str:
    """Normalize a raw value to a stripped, single-spaced string."""
    if value is None:
        return ""

    text = str(value).strip()
    return re.sub(r"\s+", " ", text)


def _normalize_kind(value: Any) -> str:
    """Map a raw kind string to a canonical event kind, defaulting to 'otro'."""
    normalized = _clean_text(value).lower()
    return EVENT_KIND_ALIASES.get(normalized, "otro")


def _normalize_date_iso(value: Any) -> str:
    """Validate and normalize a date string to ISO 8601, or return empty on failure."""
    candidate = _clean_text(value)
    if not candidate:
        return ""

    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return ""


def normalize_event(raw_event: Any) -> dict[str, str] | None:
    """Normalizar un evento detectado por el LLM o leído del frontmatter."""
    if not isinstance(raw_event, dict):
        return None

    title = _clean_text(raw_event.get("title"))
    date_iso = _normalize_date_iso(raw_event.get("date_iso") or raw_event.get("date"))
    date_text = _clean_text(raw_event.get("date_text"))

    if not title:
        return None

    if not date_iso and not date_text:
        return None

    event = {
        "title": title,
        "kind": _normalize_kind(raw_event.get("kind")),
    }

    if date_iso:
        event["date_iso"] = date_iso
    if date_text:
        event["date_text"] = date_text
    elif date_iso:
        event["date_text"] = date_iso

    time_text = _clean_text(raw_event.get("time_text"))
    details = _clean_text(raw_event.get("details"))
    source_excerpt = _clean_text(raw_event.get("source_excerpt"))

    if time_text:
        event["time_text"] = time_text
    if details:
        event["details"] = details
    if source_excerpt:
        event["source_excerpt"] = source_excerpt

    return event


def parse_llm_calendar_payload(raw_summary: str) -> tuple[str, list[dict[str, str]]]:
    """
    Separar el markdown visible del bloque estructurado con fechas importantes.

    El contrato esperado es un code fence:
      ```kdef-events
      {"important_dates": [...]}
      ```
    """
    # Captura todo lo que esté entre los delimitadores del fence, sin intentar
    # matchear llaves directamente — más robusto ante JSON anidado y whitespace variable.
    pattern = re.compile(
        rf"```\s*{re.escape(EVENTS_FENCE)}\s*\n(.*?)\n\s*```",
        flags=re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(raw_summary)

    if not match:
        return raw_summary.strip(), []

    body = f"{raw_summary[:match.start()]}{raw_summary[match.end():]}".strip()
    body = re.sub(r"\n{3,}", "\n\n", body)

    try:
        payload = json.loads(match.group(1).strip())
    except json.JSONDecodeError as exc:
        log.warning("No se pudo parsear el bloque %s: %s", EVENTS_FENCE, exc)
        return body, []

    raw_events = payload.get("important_dates", [])
    if not isinstance(raw_events, list):
        log.warning("El bloque %s no contiene una lista en 'important_dates'", EVENTS_FENCE)
        return body, []

    events: list[dict[str, str]] = []
    for raw_event in raw_events:
        event = normalize_event(raw_event)
        if event:
            events.append(event)

    return body, events


def _event_sort_key(event: dict[str, str]) -> tuple[int, str, str, str]:
    """Sort dated events first (chronologically), then undated events (alphabetically)."""
    if event.get("date_iso"):
        return (0, event["date_iso"], event.get("title", "").lower(), event.get("kind", ""))
    return (1, event.get("date_text", "").lower(), event.get("title", "").lower(), event.get("kind", ""))


def render_important_dates_section(events: list[dict[str, str]]) -> str:
    """Renderizar una sección markdown con las fechas detectadas, o vacío si no hay."""
    if not events:
        return ""

    lines = [
        "## Fechas importantes",
        "",
    ]

    for event in sorted(events, key=_event_sort_key):
        date_label = event.get("date_iso") or event.get("date_text", "Fecha sin normalizar")
        kind = event.get("kind", "otro")
        line = f"- **{date_label}** · `{kind}` · **{event['title']}**"

        extras: list[str] = []
        if event.get("time_text"):
            extras.append(f"Horario: {event['time_text']}.")
        if event.get("details"):
            extras.append(event["details"])

        if extras:
            line += " " + " ".join(extras)

        lines.append(line)

    return "\n".join(lines).strip() + "\n"


def dump_frontmatter(data: dict[str, Any]) -> str:
    """Serializar frontmatter YAML preservando el orden de las keys."""
    serialized = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=120,
    ).strip()
    return f"---\n{serialized}\n---\n"


def load_markdown_frontmatter(path: Path) -> dict[str, Any]:
    """Leer el frontmatter YAML de un markdown generado."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        return {}

    data = yaml.safe_load(match.group(1)) or {}
    return data if isinstance(data, dict) else {}


def collect_calendar_entries(content_auto_dir: Path) -> list[dict[str, Any]]:
    """Recolectar todos los eventos estructurados publicados en content/auto/."""
    calendar_page = content_auto_dir / CALENDAR_DIRNAME / CALENDAR_PAGE_NAME
    latest_pages: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []

    for path in sorted(content_auto_dir.rglob("*.md")):
        if path == calendar_page:
            continue
        if path == content_auto_dir / "index.md":
            continue

        frontmatter = load_markdown_frontmatter(path)
        raw_events = frontmatter.get("important_dates", [])
        if not isinstance(raw_events, list):
            continue

        source_origin = _clean_text(frontmatter.get("source_path")) or path.as_posix()
        generated_at = _clean_text(frontmatter.get("generated_at"))

        current_page = latest_pages.get(source_origin)
        if current_page and generated_at <= current_page["generated_at"]:
            continue

        latest_pages[source_origin] = {
            "generated_at": generated_at,
            "frontmatter": frontmatter,
            "path": path,
        }

    for source_origin, page_data in latest_pages.items():
        path = page_data["path"]
        frontmatter = page_data["frontmatter"]
        # Construir el título del link desde el path relativo (materia / sección)
        # para no depender del frontmatter title que es solo la primera palabra
        try:
            rel_parts = path.relative_to(content_auto_dir).parts
            source_title = " / ".join(rel_parts[:-1]) if len(rel_parts) > 1 else path.stem
        except ValueError:
            source_title = _clean_text(frontmatter.get("title")) or path.stem
        raw_events = frontmatter.get("important_dates", [])

        # Derivar el slug de la materia del primer componente del path relativo
        try:
            subject_slug = path.relative_to(content_auto_dir).parts[0]
        except (ValueError, IndexError):
            subject_slug = "sin-materia"

        for raw_event in raw_events:
            event = normalize_event(raw_event)
            if not event:
                continue

            enriched = dict(event)
            enriched["source_title"] = source_title
            enriched["source_path"] = path
            enriched["source_origin"] = source_origin
            enriched["subject"] = subject_slug
            entries.append(enriched)

    return sorted(entries, key=_event_sort_key)


def _format_month_heading(month_key: str) -> str:
    """Format a YYYY-MM key as a readable Spanish month heading (e.g. 'mayo 2026')."""
    year, month = month_key.split("-", 1)
    return f"{MONTH_NAMES_ES.get(int(month), month)} {year}"


def _markdown_link(from_dir: Path, target: Path) -> str:
    """Build a relative markdown link path from from_dir to target, stripping .md extension."""
    relative = os.path.relpath(target, start=from_dir).replace(os.sep, "/")
    if relative.endswith("/index.md"):
        return relative[: -len("index.md")]
    if relative.endswith(".md"):
        return relative[:-3]
    return relative


def _escape_ics_text(value: str) -> str:
    """Escape special characters per RFC 5545 for iCalendar TEXT fields."""
    escaped = value.replace("\\", "\\\\")
    escaped = escaped.replace(";", r"\;")
    escaped = escaped.replace(",", r"\,")
    escaped = escaped.replace("\n", r"\n")
    return escaped


def _fold_ics_line(line: str, limit: int = 75) -> list[str]:
    """Fold a long iCalendar line at the RFC 5545 75-octet limit.

    Continuation lines must start with a single space character.
    """
    if len(line) <= limit:
        return [line]

    chunks = [line[:limit]]
    line = line[limit:]
    while line:
        chunks.append(" " + line[: limit - 1])
        line = line[limit - 1 :]
    return chunks


def render_calendar_ics(entries: list[dict[str, Any]], generated_at: datetime) -> str:
    """Renderizar un archivo iCalendar (.ics) con los eventos fechados."""
    dtstamp = generated_at.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//kdef//fechas-importantes//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:kdef — fechas importantes",
        "X-WR-CALDESC:Fechas academicas detectadas automaticamente por kdef",
    ]

    for entry in entries:
        date_iso = entry.get("date_iso")
        if not date_iso:
            continue

        day = date.fromisoformat(date_iso)
        next_day = day + timedelta(days=1)
        uid_source = f"{entry.get('source_origin', entry['source_path'])}|{date_iso}|{entry['title']}|{entry['kind']}"
        uid_hash = hashlib.sha1(uid_source.encode("utf-8")).hexdigest()

        description_parts = []
        if entry.get("details"):
            description_parts.append(entry["details"])
        if entry.get("time_text"):
            description_parts.append(f"Horario: {entry['time_text']}")
        description_parts.append(f"Fuente: {entry['source_title']}")

        description = " ".join(description_parts)

        subject = entry.get("subject", "")
        categories = ",".join(filter(None, [entry["kind"], subject]))

        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid_hash}@kdef.com.ar",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART;VALUE=DATE:{day.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{next_day.strftime('%Y%m%d')}",
            f"SUMMARY:{_escape_ics_text(entry['title'])}",
            f"CATEGORIES:{_escape_ics_text(categories)}",
            f"DESCRIPTION:{_escape_ics_text(description)}",
            "END:VEVENT",
        ]
        lines.extend(event_lines)

    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(_fold_ics_line(line))

    return "\r\n".join(folded) + "\r\n"


def render_subject_calendar_page(
    subject_slug: str,
    entries: list[dict[str, Any]],
    content_auto_dir: Path,
    generated_at: datetime,
) -> str:
    """Construir la página de fechas importantes para una materia específica."""
    subject_dir = content_auto_dir / subject_slug
    subject_entries = [e for e in entries if e.get("subject") == subject_slug]
    dated = [e for e in subject_entries if e.get("date_iso")]
    undated = [e for e in subject_entries if not e.get("date_iso")]

    frontmatter = {
        "title": "fechas importantes",
        "date": generated_at.date().isoformat(),
        "tags": ["auto-generado", "calendario", subject_slug],
        "generated_at": generated_at.isoformat(),
        "calendar_generated": True,
        "calendar_event_count": len(subject_entries),
    }

    lines = [dump_frontmatter(frontmatter).strip(), ""]

    if dated:
        lines.extend(["## Con fecha confirmada", ""])
        current_month = None
        for entry in dated:
            month_key = entry["date_iso"][:7]
            if month_key != current_month:
                current_month = month_key
                lines.extend([f"### {_format_month_heading(month_key)}", ""])
            link = _markdown_link(subject_dir, entry["source_path"])
            bullet = (
                f"- **{entry['date_iso']}** · `{entry['kind']}` · **{entry['title']}**"
                f" — [{entry['source_title']}]({link})"
            )
            extras: list[str] = []
            if entry.get("time_text"):
                extras.append(f"Horario: {entry['time_text']}.")
            if entry.get("details"):
                extras.append(entry["details"])
            if extras:
                bullet += " " + " ".join(extras)
            lines.append(bullet)
        lines.append("")
    else:
        lines.extend(["## Con fecha confirmada", "", "_Sin fechas exactas por ahora._", ""])

    if undated:
        lines.extend(["## Sin fecha exacta", ""])
        for entry in undated:
            link = _markdown_link(subject_dir, entry["source_path"])
            bullet = (
                f"- **{entry.get('date_text', 'Fecha pendiente')}** · `{entry['kind']}` · **{entry['title']}**"
                f" — [{entry['source_title']}]({link})"
            )
            if entry.get("details"):
                bullet += f" {entry['details']}"
            lines.append(bullet)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_calendar_outputs(content_auto_dir: Path, generated_at: datetime) -> list[dict[str, Any]]:
    """Escribir la página de fechas importantes por materia."""
    entries = collect_calendar_entries(content_auto_dir)

    subjects = dict.fromkeys(e["subject"] for e in entries if e.get("subject"))
    for subject_slug in subjects:
        subject_dir = content_auto_dir / subject_slug
        if not subject_dir.is_dir():
            continue
        page = render_subject_calendar_page(subject_slug, entries, content_auto_dir, generated_at)
        (subject_dir / "fechas-importantes.md").write_text(page, encoding="utf-8")

    return entries
