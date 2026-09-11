# Project Overview

FastAPI chatbot (`POST /ask`) answering questions from a local text dataset and the Superhero
API, routing via LLM classification, with sources cited in every response. Assessment spec:
`ai_engineer_assessment_v2.2 (1) (2026).pdf`.

## Current features

- Superhero API client (`sources/superhero.py`): `search_hero(name)` returns all matching heroes
  for a name (a search can match several, e.g. "Batman" returns 3 distinct heroes), with distinct
  not-found vs. API-error handling. `build_hero_context(results)` compacts those results into a
  single string for later use as LLM prompt context.

## Not yet built

- FastAPI app / `POST /ask` route
- Local text dataset + keyword/BM25 search
- Gemini classify step (dataset / superhero / both) and answer step
- Structured `sources` field on responses
- Tests (routing, error paths)

## Update log

- **2026-09-11** — Rebuilt the Superhero API client under `sources/` (was `api_source/`), adding
  `build_hero_context(results)` to compact multi-hero results into one LLM-ready string.
  Verified live against the real API: "Batman" correctly returns 3 distinct matches, and a
  nonsense name correctly raises `SuperheroNotFoundError`. Recreated `CLAUDE.md`,
  `PROJECT_OVERVIEW.md`, and `README.md`.
- **2026-09-07** — Added Superhero API client (`api_source/data.py`) with
  `search_hero(name)`, `SuperheroNotFoundError`, `SuperheroAPIError`. Verified live against the
  real API (found "Superman", correctly raised not-found for a nonsense name). Added
  `requirements.txt` (`requests`, `python-dotenv`).
