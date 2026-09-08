# AI Engineer Assessment — Superhero Chatbot

Technical assessment submission: a FastAPI chatbot with a single `POST /ask` endpoint that
answers natural-language questions using two sources — a small local text dataset and the
[Superhero API](https://superheroapi.com/) — routing each question to the right source via an
LLM classification step, and citing sources in every response.

Full requirements are in `ai_engineer_assessment_v2.2 (1) (2026).pdf` in the repo root.

## Current state

This is early-stage. Only the Superhero API client exists so far (`api_source/data.py`); the
FastAPI app, dataset/classification logic, and tests have not been built yet. See
[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for feature status and design decisions.

## Requirements

- Python 3.10+
- A [Superhero API](https://superheroapi.com/) access token

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

   `SUPERHERO_API_TOKEN` is required. `GEMINI_API_KEY` is reserved for the upcoming LLM
   classification/answering step and isn't used by any code yet.

## Running

There is no FastAPI app yet. The only runnable piece today is the Superhero API client's demo
call:

```bash
python api_source/data.py
```

This looks up "Superman" via the Superhero API and prints the matching results.

## Testing

There is no test suite yet.
