# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

This is a technical assessment submission: a FastAPI chatbot with a single `POST /ask` endpoint
that answers natural-language questions using two sources — a small local text dataset and the
[Superhero API](https://superheroapi.com/) — routing each question to the right source (or both)
via an LLM classification step, and citing sources in every response. Full requirements are in
`ai_engineer_assessment_v2.2 (1) (2026).pdf` in the repo root.

Track ongoing feature status and changes in `PROJECT_OVERVIEW.md` — update it whenever a feature
is added or a design decision changes, rather than duplicating that info here.

## Current state

The project is early-stage. Only the Superhero API client exists so far
(`sources/superhero.py`); the FastAPI app, dataset/classification logic, and tests have not been
built yet.

## Commands

```bash
pip install -r requirements.txt      # install deps (requests, python-dotenv)
python sources/superhero.py          # run the Superhero API client's demo call directly
```

There is no test suite yet.

## Architecture

- **Config/secrets**: loaded from a root-level `.env` (gitignored) via `python-dotenv`.
  `SUPERHERO_API_TOKEN` is required; `GEMINI_API_KEY` is reserved for the LLM calls (Google
  Gemini AI Studio) but not yet used in code.
- **`sources/superhero.py`**: `search_hero(name)` wraps `GET
  https://superheroapi.com/api/{token}/search/{name}`, returning the API's `results` list — a
  name can match several heroes, so this always returns a list rather than assuming one match. It
  raises `SuperheroNotFoundError` when the API reports no match, and `SuperheroAPIError` for
  network/timeout/non-200/malformed-JSON failures — callers should catch these to distinguish
  "no such hero" from "the API is unavailable" rather than letting either crash the request.
  `build_hero_context(results)` turns that list into one compact string (name, publisher, full
  name, alignment, powerstats per hero) meant to be dropped straight into an LLM prompt later.

## Planned design (not yet implemented)

Agreed direction for the rest of the build, kept here so it isn't re-litigated from scratch:

- **Two-stage LLM flow**: a cheap Gemini call classifies each question as `dataset`, `superhero`,
  or `both` (plus extracted hero name(s) for superhero questions) before any retrieval happens;
  a second Gemini call produces the final answer from whatever context was retrieved. Kept as two
  calls (not combined) specifically so classification is unit-testable in isolation.
- **Dataset retrieval**: a small curated set of local text/markdown files, searched with simple
  keyword/BM25-style matching — no embeddings or vector DB.
- **Response shape**: `{"answer": ..., "sources": [{"type": "superhero_api"|"dataset", "detail":
  ...}]}` — sources are a structured field, not just prose, so citation is testable.
- **Test scope**: routing/classification is the must-have core, plus a couple of error-path tests
  (empty input, superhero-not-found) since "sensible error handling" is explicit in the
  assessment's grading bar.
- **Scope is intentionally minimal**: no Docker, no CI — matches the assessment's "80-90%
  production-ready," not gold-plated.
