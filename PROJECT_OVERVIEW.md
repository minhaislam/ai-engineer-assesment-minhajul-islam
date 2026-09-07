# Project Overview

FastAPI chatbot (`POST /ask`) answering questions from a local text dataset and the Superhero
API, routing via LLM classification, with sources cited in every response. Assessment spec:
`ai_engineer_assessment_v2.2 (1) (2026).pdf`.

## Current features

- Superhero API client (`api_source/data.py`): search by name, with distinct
  not-found vs. API-error handling.

## Not yet built

- FastAPI app / `POST /ask` route
- Local text dataset + keyword/BM25 search
- Gemini classify step (dataset / superhero / both) and answer step
- Structured `sources` field on responses
- Tests (routing, error paths)
- README

## Update log

- **2026-09-07** — Added Superhero API client (`api_source/data.py`) with
  `search_hero(name)`, `SuperheroNotFoundError`, `SuperheroAPIError`. Verified live against the
  real API (found "Superman", correctly raised not-found for a nonsense name). Added
  `requirements.txt` (`requests`, `python-dotenv`).
