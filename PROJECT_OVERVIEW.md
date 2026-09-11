# Project Overview

FastAPI chatbot (`POST /ask`) answering questions from a local text dataset and the Superhero
API, routing via LLM classification, with sources cited in every response. Assessment spec:
`ai_engineer_assessment_v2.2 (1) (2026).pdf`.

## Current features

- FastAPI app (`main.py`), `POST /ask`: validates the question is non-empty (400 if not), calls
  Gemini, returns `{"answer": ..., "sources": [...]}`. **Gemini-only for now** — no dataset or
  superhero-lookup routing wired in yet, so every response cites `"type": "gemini"` and is
  answered from the model's own general knowledge. This was a deliberate, scoped-down first cut
  to prove the HTTP → LLM path end-to-end before adding retrieval.
- Superhero API client (`sources/superhero.py`): `search_hero(name)` returns all matching heroes
  for a name (a search can match several, e.g. "Batman" returns 3 distinct heroes), with distinct
  not-found vs. API-error handling. `build_hero_context(results)` compacts those results into a
  single string for later use as LLM prompt context. Not yet called from `main.py`.
- Gemini LLM client (`services/gemini.py`): the only file that talks to Gemini. Client is built
  once via `@lru_cache`, not per request. Exposes one function, `call_gemini(system_prompt,
  user_message) -> str`, so swapping providers later means touching one file.

## Not yet built

- Superhero-lookup routing and local dataset retrieval wired into `POST /ask`
- Local text dataset + keyword/BM25 search
- Gemini classify step (dataset / superhero / both) and answer step, built on top of `call_gemini`
- Structured multi-type `sources` field (currently always just `"gemini"`)
- Tests (routing, error paths)

## Update log

- **2026-09-12** — Added the FastAPI app (`main.py`) with `POST /ask`. Scoped down deliberately:
  it forwards the question straight to `call_gemini` and returns the answer, with no
  dataset/superhero routing yet (confirmed with the user this is a follow-up step). Empty-question
  input returns a 400 with a clear message; a Gemini failure returns a 502 instead of a raw
  traceback. Verified live end-to-end (`uvicorn main:app`): a real question returns a real
  Gemini-backed answer, an empty question returns 400, and the auto-generated Swagger UI at
  `/docs` renders. Added `fastapi` and `uvicorn` to `requirements.txt`.
- **2026-09-12** — Added Gemini LLM client (`services/gemini.py`) with a cached client
  (`@lru_cache`) and a single `call_gemini(system_prompt, user_message)` entry point. Verified
  live: initially hit a 404 because `gemini-2.5-flash` was retired for new users mid-build;
  switched to `gemini-3.6-flash` and confirmed a real round trip ("What is the capital of
  France?" → "The capital of France is Paris."). Added `google-genai` to `requirements.txt`.
- **2026-09-11** — Rebuilt the Superhero API client under `sources/` (was `api_source/`), adding
  `build_hero_context(results)` to compact multi-hero results into one LLM-ready string.
  Verified live against the real API: "Batman" correctly returns 3 distinct matches, and a
  nonsense name correctly raises `SuperheroNotFoundError`. Recreated `CLAUDE.md`,
  `PROJECT_OVERVIEW.md`, and `README.md`.
- **2026-09-07** — Added Superhero API client (`api_source/data.py`) with
  `search_hero(name)`, `SuperheroNotFoundError`, `SuperheroAPIError`. Verified live against the
  real API (found "Superman", correctly raised not-found for a nonsense name). Added
  `requirements.txt` (`requests`, `python-dotenv`).
