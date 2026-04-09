# kdef

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="quartz/static/banner-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="quartz/static/banner-light.png">
  <img alt="kdef banner" src="quartz/static/banner-light.png" width="100%">
</picture>

> Automated knowledge garden for students of the Cyber Defense degree program at UNDEF (Argentina).

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)
[![CI](https://github.com/matzalazar/kdef/actions/workflows/ci.yml/badge.svg)](https://github.com/matzalazar/kdef/actions/workflows/ci.yml)
[![Pipeline](https://github.com/matzalazar/kdef/actions/workflows/update-garden.yml/badge.svg)](https://github.com/matzalazar/kdef/actions/workflows/update-garden.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Site](https://img.shields.io/website?url=https%3A%2F%2Fkdef.com.ar)](https://kdef.com.ar)

## Overview

`kdef` is an independent student project that:

- downloads course materials from Moodle,
- generates structured summaries with LLMs,
- extracts important academic dates from those materials,
- publishes those summaries as a static website,
- and allows students to add collaborative notes.

The project is designed to stay simple, low-cost, and easy to replicate for other academic programs.

## Scope

This repository is:

- a student-maintained learning resource,
- a searchable and linkable knowledge garden,
- and an automated content pipeline.

This repository is **not**:

- official UNDEF content,
- an institutional publication,
- or a replacement for the official Moodle platform.

## Content model

The content layer is intentionally split into three areas:

- `content/notas-automaticas/`: bot-generated summaries from Moodle materials (pipeline-owned)
- `content/notas-colaborativas/`: human-written collaborative notes
- `content/porque-kdef/`: project documentation (architecture, contribution guide, replication guide)

## Repository structure

```text
.github/
  workflows/
    ci.yml
    dependabot-automerge.yml
    update-garden.yml
config/
  campus.yml
content/
  notas-automaticas/
  notas-colaborativas/
  porque-kdef/
scripts/
  auth.py
  catalog.py
  pipeline.py
  scraper.py
  summarizer.py
  manifest.py
  academic_calendar.py
quartz/
quartz.config.ts
quartz.layout.ts
```

## How it works

The weekly GitHub Actions workflow (`.github/workflows/update-garden.yml`) runs the pipeline:

1. Scrape/download source materials from Moodle.
2. Generate summaries with LLMs (primary + fallback model strategy).
3. Detect and normalize important dates (finals, exams, deliveries, etc.) from each document.
4. Publish a generated calendar page plus an `.ics` feed in `content/notas-automaticas/calendario/`.
5. Track processed files with SHA-256 (`scripts/manifest.py`) to avoid reprocessing unchanged inputs.
6. Commit new/updated generated markdown in `content/notas-automaticas/`.
7. Build and deploy the static site.

## Local development

### Website

```bash
npm install
npm run serve
```

The site is served at `http://localhost:8080`.

Generated non-markdown assets under `content/` are copied by Quartz as-is, so the
calendar feed ends up published alongside the generated pages.

### Pipeline (Python)

```bash
cp .env.example .env
# fill your environment values
pip install -r scripts/requirements.txt
DRY_RUN=true python scripts/pipeline.py
```

## Environment variables

Core variables used by the pipeline and deployment:

- `TRACKED_SUBJECTS`
- `MOODLE_URL`
- `MOODLE_USER`
- `MOODLE_PASS`
- `MODELS_API_KEY`
- `GEMINI_API_KEY`
- `CF_API_TOKEN`
- `CF_ACCOUNT_ID`
- `DRY_RUN`
- `FORCE_REPROCESS`

See `.env.example` for details.

The campus course catalogue lives in `config/campus.yml`. `TRACKED_SUBJECTS`
selects which `slug` values from that file should be processed.

## Contributing

- Add student notes in `content/notas-colaborativas/`.
- Follow the contribution guide in `content/porque-kdef/18-como-contribuir.md`.
- Do **not** edit `content/notas-automaticas/` manually.

## Replicating this model

To reuse this setup for other degree programs, see:

- `content/porque-kdef/19-copiar-modelo.md`

## License

MIT. See `LICENSE.txt`.
