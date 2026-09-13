# AI Engineer Assessment — Superhero Chatbot

A FastAPI chatbot with a single `POST /ask` endpoint. It answers natural-language questions
using a local text dataset and/or the [Superhero API](https://superheroapi.com/), automatically
routing each question to the right source, and citing sources in every response.

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for the full design and data flow.

## 1. Set environment variables

Create a `.env` file in the repo root:

```
SUPERHERO_API_TOKEN=your_superhero_api_token
GEMINI_API_KEY=your_gemini_api_key
DATASET_PATH=data/football.txt
```

- `SUPERHERO_API_TOKEN` — from [superheroapi.com](https://superheroapi.com/) (sign in with GitHub).
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/).
- `DATASET_PATH` — path to a text file, one factual sentence per line (not a table/CSV). The
  bundled example, `data/football.txt`, works out of the box.

## 2. Run the setup script

```bash
python init.py
```

This checks your OS and Python version, creates a `.venv` virtual environment, installs
`requirements.txt` into it, and verifies the three variables above are set — printing the
result of each step. Then activate the environment it created:

```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

## 3. Run the API

```bash
uvicorn main:app --reload
```

## 4. Use it

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who won the first FIFA World Cup?"}'
```

```json
{
  "answer": "Uruguay won the first FIFA World Cup in 1930.\n\nSources: dataset: football.txt",
  "sources": ["dataset: football.txt"],
  "intent": "dataset"
}
```

Ask about a superhero instead ("What are Batman's powerstats?") and it routes to the Superhero
API; ask something that needs both, and it fetches from both sources. Or try it interactively at
http://127.0.0.1:8000/docs.

An empty or >500-character question returns `422`; a Gemini or Superhero API failure returns
`502` with the real reason.
