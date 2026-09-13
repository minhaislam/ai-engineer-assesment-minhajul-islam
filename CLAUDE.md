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

The full pipeline is wired up: `main.py`'s `POST /ask` validates the request, then
`core/router.py` classifies intent, fetches context from the right source(s), and answers from
that context only. Not yet built: tests, and a cap on how many hero names/matches a single
question can pull into the prompt.

## Commands

```bash
python init.py                       # bootstrap: checks OS/Python version, creates .venv,
                                      # installs requirements.txt, verifies .env variables
uvicorn main:app --reload            # run the API (POST /ask); docs at /docs
python sources/superhero.py          # run the Superhero API client's demo call directly
python services/gemini.py            # run the Gemini client's demo call directly
python sources/dataset.py            # run the dataset keyword-search demo call directly
```

There is no test suite yet.

## Architecture

Request flow: `main.py` → `models/schemas.py` (validation) → `core/router.py` →
`core/intent.py` (classify) → `sources/superhero.py` and/or `sources/dataset.py` (retrieve) →
`core/responder.py` (answer) → back to `main.py`. Full diagram in `PROJECT_OVERVIEW.md`.

- **`init.py`**: stdlib-only bootstrap script (no third-party imports — it has to run before
  `requirements.txt` is installed). Checks OS + Python version (fails clearly if below 3.10),
  creates `.venv` if missing, installs `requirements.txt` into it via the venv's own
  `python -m pip` (not the system one), and parses `.env` itself (a minimal inline parser, not
  `python-dotenv`, for the same "must run before deps exist" reason) to confirm
  `SUPERHERO_API_TOKEN`/`GEMINI_API_KEY`/`DATASET_PATH` are all set. Prints each step's result.
  Does not activate the venv or start the server — cross-process activation isn't possible, so
  those remain manual steps (see `README.md`).
- **Config/secrets**: loaded from a root-level `.env` (gitignored) via `python-dotenv`.
  `SUPERHERO_API_TOKEN`, `GEMINI_API_KEY`, and `DATASET_PATH` are all required now.
- **`models/schemas.py`**: `AskRequest` (question, 1-500 chars, blank-after-strip rejected) and
  `AskResponse` (`answer: str`, `sources: list[str]`, `intent: str`) — the contract everything
  else builds on.
- **`prompts/intent_system.txt`** / **`prompts/answer_system.txt`**: system prompts as plain text
  files (not Python strings) so they can be tuned without touching code. Loaded fresh on every
  call — no caching, since re-reading a small text file is negligible and it means a prompt edit
  takes effect without restarting the server. `core/intent.py` and `core/responder.py` locate
  these files via `Path(__file__).resolve().parent.parent`, not a plain relative string, so they
  resolve correctly no matter the process's cwd or OS.
- **`main.py`**: FastAPI app, single `POST /ask` route. A `lifespan` handler calls
  `sources.dataset.load_dataset()` once at startup, so the dataset is in memory (via its
  `@lru_cache`) before the first request rather than lazily on it — a broken/missing dataset
  file then fails fast at boot instead of surfacing on the first `/ask` call. The route itself
  delegates everything to `core.router.handle_question`; catches any exception and returns 502
  with the real reason (rather than a raw traceback) so a Gemini outage/rate-limit or Superhero
  API outage fails cleanly. Field-level validation (empty/too-long question) is handled by
  `AskRequest` itself and
  surfaces as FastAPI's standard 422.
- **`core/memory.py`**: a single global, in-memory conversation history (`deque(maxlen=5)` of
  `(question, answer)` pairs) — not per-session, since `/ask` has no session/conversation ID and
  this keeps `models/schemas.py`'s contract unchanged. `get_summary()` condenses the stored
  turns into a short paragraph via one extra Gemini call (bounds prompt size regardless of how
  long the conversation runs, at the cost of one more API call per question once history exists
  — worth knowing given the free-tier quota). Pure in-process state, nothing written to disk, so
  it resets automatically on every restart — there's no explicit "refresh" step because there's
  nothing to invalidate.
- **`core/intent.py`**: `classify_intent(question, history="")` loads `prompts/intent_system.txt`,
  calls Gemini, and parses a `{"intent": "..."}` JSON reply into one of `dataset`/`superhero`/
  `both`. Falls back to `"both"` if the reply can't be parsed, rather than crashing the request.
  The prompt doesn't hardcode the dataset's topic — a `<<DATASET_SAMPLE>>` placeholder is filled
  in with the first 5 lines of `sources.dataset.load_dataset()` at call time, so the classifier
  always sees what the dataset actually contains rather than a description that can go stale.
  `history` (from `core/memory.py`), when non-empty, is prepended to the user message so a vague
  follow-up ("what about his weaknesses?") still classifies correctly.
- **`core/router.py`**: the orchestrator. Calls `classify_intent`, then fetches context from the
  matching source(s) — `"both"` runs superhero + dataset lookups concurrently via
  `asyncio.gather`/`asyncio.to_thread` since both are blocking I/O. For superhero questions it
  runs a small extra Gemini call first (`HERO_EXTRACT_SYSTEM_PROMPT`, inline in this file, not a
  separate prompt file) to pull hero name(s) out of the free-form question, since
  `search_hero()` needs an actual name, not a whole sentence — also given the conversation
  history, so "his weaknesses" resolves to whichever hero was named earlier. Combines whatever
  context came back (or a "no relevant information" fallback if nothing did) and calls
  `core.responder.generate_answer`, then sets `intent` on the returned `AskResponse` and records
  the turn via `memory.add_turn` before handing the response back to `main.py`.
- **`core/responder.py`**: `generate_answer(question, context, sources, history="")` loads
  `prompts/answer_system.txt`, calls Gemini with the question + context + source labels (+
  conversation history if any, for tone/reference resolution only — the prompt tells Gemini
  never to treat history as a fact source), and returns an `AskResponse` (with `intent` left
  blank — `router.py` fills that in, since responder doesn't know it).
- **`sources/superhero.py`**: `search_hero(name)` wraps `GET
  https://superheroapi.com/api/{token}/search/{name}`, returning the API's `results` list — a
  name can match several heroes, so this always returns a list rather than assuming one match. It
  raises `SuperheroNotFoundError` when the API reports no match, and `SuperheroAPIError` for
  network/timeout/non-200/malformed-JSON failures — callers should catch these to distinguish
  "no such hero" from "the API is unavailable" rather than letting either crash the request.
  `build_hero_context(results)` turns that list into one compact string (name, publisher, full
  name, alignment, powerstats per hero) meant to be dropped straight into an LLM prompt later.
- **`sources/dataset.py`**: the dataset location isn't hardcoded — `DATASET_PATH` comes from the
  environment (`.env`), so any text file, anywhere on disk, works without touching this file or
  needing a `data/` directory. `load_dataset()` reads it once (`@lru_cache`) and splits it into
  one fact per line; raises `RuntimeError` at call time if `DATASET_PATH` isn't set, so a missing
  config fails fast (and fails at app *startup*, since `main.py`'s `lifespan` calls
  `load_dataset()` immediately) rather than surfacing later as a confusing error.
  `data/football.txt` still ships as the example dataset, referenced by `DATASET_PATH` in `.env`.
  **Expected format is one factual sentence per line, not a delimited table** — retrieval finds
  relevant existing lines by keyword overlap, it can't parse columns or compute an aggregate
  (e.g. a CSV of game sales and "what's the most sold game" won't work; no single line/row
  answers that, it needs a max across all rows). `search_dataset(question)` scores each line by keyword
  overlap with the question (a small stopword list — "the", "is", "what", etc. — is stripped
  first so common words don't inflate every line's score) and returns the top 5 lines joined into
  one string, or `""` if nothing overlaps. Plain keyword matching, no embeddings/vector DB, per
  the "Dataset retrieval" decision below.
- **`services/gemini.py`**: the only file that knows Gemini exists. `_get_client()` builds the
  `google.genai.Client` once (`@lru_cache`) instead of per request. `call_gemini(system_prompt,
  user_message) -> str` is the single entry point every other module should use — swapping LLM
  providers later means changing only this file. Uses model `gemini-3.6-flash` (`gemini-2.5-flash`
  was retired for new users mid-build; keep an eye on Google's model deprecation notices).

## Design decisions (implemented)

- **Two/three-stage LLM flow**: a cheap Gemini call classifies each question as `dataset`,
  `superhero`, or `both`; for superhero questions, another cheap call extracts hero name(s) from
  the free-form question; a final Gemini call produces the answer from whatever context was
  retrieved. Kept as separate calls (not combined) so each step is unit-testable in isolation.
- **Dataset retrieval**: a small curated text file (`data/football.txt`), searched with plain
  keyword-overlap matching — no embeddings or vector DB.
- **Response shape**: `{"answer": ..., "sources": [...], "intent": "..."}` — `sources` is a flat
  `list[str]` of human-readable labels (e.g. `"superhero_api: Batman"`, `"dataset: football
  facts"`), not free prose, so citation is testable; `intent` exposes the classifier's decision
  for debugging/observability.

## Not yet built / known limitations

- **Test scope**: routing/classification is the must-have core, plus a couple of error-path tests
  (empty input, superhero-not-found) since "sensible error handling" is explicit in the
  assessment's grading bar. No tests exist yet.
- **No cap on fan-out**: a question naming many heroes, or a name with many API matches, grows
  the prompt with no limit. Fine for a single-user assessment demo, worth capping for real use.
- **Free-tier Gemini quota**: `gemini-3.6-flash`'s free tier is only 20 requests/day, and this
  pipeline uses 2-3 calls per question (classify, optional hero-name extraction, answer) — it's
  easy to exhaust during a normal test session. A 429 surfaces as a clean 502 from `main.py`
  rather than crashing, but be aware of it when demoing.
- **Scope is intentionally minimal**: no Docker, no CI — matches the assessment's "80-90%
  production-ready," not gold-plated.
