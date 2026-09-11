# AI Engineer Assessment — Superhero Chatbot

Technical assessment submission: a FastAPI chatbot with a single `POST /ask` endpoint that
answers natural-language questions using two sources — a small local text dataset and the
[Superhero API](https://superheroapi.com/) — routing each question to the right source via an
LLM classification step, and citing sources in every response.

Full requirements are in `ai_engineer_assessment_v2.2 (1) (2026).pdf` in the repo root.

## Current state

The FastAPI app (`main.py`) has one working endpoint, `POST /ask`, but it only forwards the
question straight to Gemini for now — there's no dataset or superhero-lookup routing wired in
yet, and no classification step. See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for feature
status and design decisions.

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
  -d '{"question": "What is the capital of France?"}'
```

```json
{"answer": "The capital of France is Paris.", "sources": [{"type": "gemini", "detail": "..."}]}
```

An empty question returns `400` with a clear error instead of a crash. You can also try it from
the browser via the auto-generated docs at http://127.0.0.1:8000/docs.

## Running the individual clients

Each building block also has its own demo call, useful for testing it in isolation:

```bash
python sources/superhero.py     # looks up "Batman", prints a compact context string
python services/gemini.py       # sends one prompt to Gemini, prints the answer
```

## Testing

There is no test suite yet.
