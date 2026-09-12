# Project Overview

FastAPI chatbot (`POST /ask`) answering questions from a local text dataset and the Superhero
API, routing via LLM classification, with sources cited in every response. Assessment spec:
`ai_engineer_assessment_v2.2 (1) (2026).pdf`.

## Current features

The full pipeline is wired up end-to-end:

```
main.py (POST /ask)
  -> models/schemas.py validates the request (AskRequest)
  -> core/router.py: handle_question(question)
       -> core/intent.py: classify_intent(question) -> "dataset" | "superhero" | "both"
       -> calls the matching source(s):
            sources/superhero.py  (extract hero name(s) via Gemini, then search_hero + build_hero_context)
            sources/dataset.py    (search_dataset: keyword overlap)
          "both" runs the two concurrently (asyncio.gather + asyncio.to_thread)
       -> core/responder.py: generate_answer(question, context, sources) -> AskResponse
       -> router.py sets response.intent before returning
  -> main.py returns the AskResponse (502 on any failure, with the real reason)
```

- `models/schemas.py`: `AskRequest` (question, 1-500 chars, rejects blank-after-strip via a
  `field_validator`) and `AskResponse` (`answer: str`, `sources: list[str]`, `intent: str`).
- `prompts/intent_system.txt` and `prompts/answer_system.txt`: system prompts as text files, not
  Python strings, so they're editable without a code change or restart.
- `core/intent.py`: one Gemini call, parses `{"intent": "..."}` JSON, falls back to `"both"` on
  an unparseable reply instead of crashing. The prompt doesn't hardcode the dataset's topic —
  it shows the classifier a live sample of `sources.dataset.load_dataset()` (first 5 lines,
  substituted into the `<<DATASET_SAMPLE>>` placeholder in `prompts/intent_system.txt`), so
  swapping `data/football.txt` for a different file doesn't require editing the prompt by hand.
- `core/router.py`: the orchestrator. Superhero questions get an extra inline Gemini call (hero
  name extraction from free text — same design validated in `scripts/test_superhero_gemini.py`)
  before `search_hero()` can run.
- `core/responder.py`: builds the final answer, telling Gemini to use *only* the given context,
  plus a `Sources:` line at the end of the answer text itself, in addition to the structured
  `sources` list.
- Superhero API client (`sources/superhero.py`) and local dataset (`sources/dataset.py` +
  `data/football.txt`) — see their entries further down for how each works; both are now called
  from `main.py` via the router instead of standalone.
- Gemini LLM client (`services/gemini.py`) — unchanged, still the only file that knows Gemini
  exists.
- Manual test script (`scripts/test_superhero_gemini.py`) — the design prototype for the
  superhero half of `core/router.py`; still useful standalone for testing just that piece.

## Not yet built / known limitations

- Tests (routing, error paths) — the assessment's explicit "sensible error handling" bar wants
  at least empty-input and superhero-not-found covered.
- No cap on fan-out: a question naming many heroes, or an ambiguous name with many API matches,
  grows the prompt with no limit.
- `gemini-3.6-flash`'s free tier is 20 requests/day, and each question costs 2-3 calls (classify,
  optional hero extraction, answer) — easy to exhaust during a test session. See the update-log
  entry below.

## Update log

- **2026-09-12** — Fixed a coupling issue in `prompts/intent_system.txt`: it used to hardcode
  "football (soccer) facts" as the dataset's topic, which would silently go stale if
  `data/football.txt` were ever swapped for a different dataset. `core/intent.py` now injects a
  live sample (first 5 lines of `load_dataset()`) into a `<<DATASET_SAMPLE>>` placeholder in the
  prompt instead. Verified: the constructed prompt correctly contains real dataset lines with no
  leftover placeholder, and `classify_intent()` still returns the right label for
  dataset/superhero/both questions (tested via `gemini-3.5-flash-lite` while `3.6-flash`'s quota
  was still exhausted — see below).
- **2026-09-12** — Discovered `gemini-2.5-flash-lite` is also retired for new API keys (404, same
  as `gemini-2.5-flash` earlier) — not a quota issue, the model is simply unavailable. Confirmed
  `gemini-3.5-flash-lite` works and draws from a separate quota than `gemini-3.6-flash`, so it's
  a viable fallback for testing while the primary model's daily quota is exhausted.
- **2026-09-12** — Wired the full pipeline together: `models/schemas.py` (`AskRequest`/
  `AskResponse`), `prompts/intent_system.txt` + `prompts/answer_system.txt`, and
  `core/{intent,router,responder}.py`. `main.py` now delegates entirely to
  `core.router.handle_question` instead of calling Gemini directly. Verified live for the
  `"dataset"` path: "Who won the first FIFA World Cup?" → correct intent, correct answer, correct
  citation both in the answer text and the structured `sources` field. Verification of the
  `"superhero"` and `"both"` paths was cut short by hitting Gemini's free-tier quota (20
  requests/day for `gemini-3.6-flash`) partway through — the 429 came back as a clean 502 from
  `main.py`, confirming the error handling works, but live-testing those two paths (and the
  edge cases: >500 char question, ambiguous multi-hero "both" question) is still pending a quota
  reset or a different key.
- **2026-09-12** — Added the local dataset: `data/football.txt` (~25 curated football/soccer
  facts, one per line) and `sources/dataset.py` with `load_dataset()` (cached, reads the file
  once) and `search_dataset(question)` (keyword-overlap scoring, stopwords stripped, top 5 lines
  joined into one string). Verified live: "Who won the first World Cup?" surfaces the exact
  Uruguay-1930 line first; "What is the offside rule?" returns just the one line that actually
  defines it; a fully unrelated question ("capital of France?") correctly returns an empty
  string rather than forcing irrelevant lines into the context.
- **2026-09-12** — Extended `scripts/test_superhero_gemini.py` to a full two-stage flow:
  `extract_hero_names()` (a Gemini call) pulls out zero, one, or multiple hero names from a
  free-form question, then `gather_hero_context()` looks each up and combines results before the
  final answer call. Handles the cases discussed: "difference between Batman and Superman" →
  extracts both names, fetches both, produces a real comparison; "tell me about Superman" (2
  matches incl. Cyborg Superman) → all matches included, Gemini addresses the ambiguity instead
  of guessing; a question with no hero mentioned → extraction correctly returns none; a
  hero-styled but fake name ("Captain Nonexistentman") → extracted, then `search_hero` correctly
  reports not-found and Gemini relays that honestly. This is the design intended for `main.py`'s
  `/ask`, pending final review before wiring it in.
- **2026-09-12** — Added `scripts/test_superhero_gemini.py`, a manual script that passes
  `build_hero_context()` output into `call_gemini()` alongside a question, to sanity-check the
  combination before wiring it into `main.py`. Verified live: "Batman" (3 matches) → Gemini
  correctly notes strengths/weaknesses aren't in the data; "Superman" (2 matches, including
  Cyborg Superman) → Gemini answers for both rather than guessing which one was meant; a
  nonsense name fails at the `search_hero` step with `SuperheroNotFoundError`, never reaching
  Gemini.
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
