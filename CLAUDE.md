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

`main.py` runs a FastAPI app with one endpoint, `POST /ask`, but it currently just forwards the
question straight to Gemini and returns the answer — no dataset/superhero routing or
classification step yet, even though `sources/superhero.py` exists and is ready to be wired in.

## Commands

```bash
pip install -r requirements.txt      # install deps (requests, python-dotenv, google-genai, fastapi, uvicorn)
uvicorn main:app --reload            # run the API (POST /ask); docs at /docs
python sources/superhero.py          # run the Superhero API client's demo call directly
python services/gemini.py            # run the Gemini client's demo call directly
```

There is no test suite yet.

## Architecture

- **Config/secrets**: loaded from a root-level `.env` (gitignored) via `python-dotenv`.
  `SUPERHERO_API_TOKEN` and `GEMINI_API_KEY` (Google Gemini AI Studio) are both required now.
- **`main.py`**: FastAPI app, single `POST /ask` route. Validates `question` is non-empty (400 if
  not), calls `services.gemini.call_gemini` (502 on failure), and returns `{"answer": ...,
  "sources": [...]}`. Right now it always answers from Gemini's own knowledge with no retrieval —
  the `sources` entry says so explicitly (`type: "gemini"`) rather than pretending otherwise.
  Wiring in `sources/superhero.py` and a local dataset behind an actual classification step is
  the next planned increment (see below).
- **`sources/superhero.py`**: `search_hero(name)` wraps `GET
  https://superheroapi.com/api/{token}/search/{name}`, returning the API's `results` list — a
  name can match several heroes, so this always returns a list rather than assuming one match. It
  raises `SuperheroNotFoundError` when the API reports no match, and `SuperheroAPIError` for
  network/timeout/non-200/malformed-JSON failures — callers should catch these to distinguish
  "no such hero" from "the API is unavailable" rather than letting either crash the request.
  `build_hero_context(results)` turns that list into one compact string (name, publisher, full
  name, alignment, powerstats per hero) meant to be dropped straight into an LLM prompt later.
- **`services/gemini.py`**: the only file that knows Gemini exists. `_get_client()` builds the
  `google.genai.Client` once (`@lru_cache`) instead of per request. `call_gemini(system_prompt,
  user_message) -> str` is the single entry point every other module should use — swapping LLM
  providers later means changing only this file. Uses model `gemini-3.6-flash` (`gemini-2.5-flash`
  was retired for new users mid-build; keep an eye on Google's model deprecation notices).

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
