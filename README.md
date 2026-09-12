# AI Engineer Assessment — Superhero Chatbot

Technical assessment submission: a FastAPI chatbot with a single `POST /ask` endpoint that
answers natural-language questions using two sources — a small local text dataset and the
[Superhero API](https://superheroapi.com/) — routing each question to the right source via an
LLM classification step, and citing sources in every response.

Full requirements are in `ai_engineer_assessment_v2.2 (1) (2026).pdf` in the repo root.

## Current state

The FastAPI app (`main.py`) has one working endpoint, `POST /ask`. It classifies the question
(football dataset / superhero API / both), fetches context from the right source(s), and answers
from that context only, citing sources. See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the
full data flow and design decisions.

## Requirements

- Python 3.10+
- A [Superhero API](https://superheroapi.com/) access token
- A [Google Gemini AI Studio](https://aistudio.google.com/) API key

## Setup

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the repo root with:

   ```
   SUPERHERO_API_TOKEN=your_superhero_api_token
   GEMINI_API_KEY=your_gemini_api_key
   ```

   Both are required.

## Running the API

```bash
uvicorn main:app --reload
```

Then send a question:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who won the first FIFA World Cup?"}'
```

```json
{
  "answer": "Uruguay won the first FIFA World Cup in 1930.\n\nSources: dataset: football facts",
  "sources": ["dataset: football facts"],
  "intent": "dataset"
}
```

Ask about a superhero instead ("What are Batman's powerstats?") and it routes to the Superhero
API; ask something that needs both, and it fetches from both sources concurrently. An empty or
>500-character question returns `422` with a clear validation error instead of a crash; a Gemini
or Superhero API failure returns `502` with the real reason. You can also try it from the browser
via the auto-generated docs at http://127.0.0.1:8000/docs.

**Note:** Gemini's free tier caps `gemini-3.6-flash` at 20 requests/day, and each question here
costs 2-3 calls (classify, optional hero-name extraction, answer) — it's easy to hit that limit
during a test session. A 429 from Gemini surfaces as a `502` from `/ask`, not a crash.

## Running the individual clients

Each building block also has its own demo call, useful for testing it in isolation:

```bash
python sources/superhero.py     # looks up "Batman", prints a compact context string
python services/gemini.py       # sends one prompt to Gemini, prints the answer
python sources/dataset.py       # keyword-searches data/football.txt, prints the top matches
```

## Testing

There is no test suite yet.
