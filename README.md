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
GEMINI_MODEL=gemini-3.6-flash
```

- `SUPERHERO_API_TOKEN` — from [superheroapi.com](https://superheroapi.com/) (sign in with GitHub).
- `GEMINI_API_KEY` — from [Google AI Studio](https://aistudio.google.com/).
- `DATASET_PATH` — path to a text file, one factual sentence per line (not a table/CSV). The
  bundled example, `data/football.txt`, works out of the box.
- `GEMINI_MODEL` — optional; which Gemini model to call. Leave unset to use the default
  (`gemini-3.6-flash`), or set it to switch models (e.g. if a model is retired or you hit its
  quota).

## 2. Run the setup script

```bash
source ./init.sh
```

This checks your OS and Python version, creates a `.venv` virtual environment, installs
`requirements.txt` into it, and verifies the three variables above are set — printing the
result of each step. Because it's run with `source`, it also activates the environment it
created in your current shell once setup finishes, so there's no separate activation step.

If you run it as `./init.sh` instead (without `source`), it does the same setup but can't
activate the venv in your shell — activate it yourself afterward:

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
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"tell me about flash?\"}"
```


Ask about a superhero instead ("What are Batman's powerstats?") and it routes to the Superhero
API; ask something that needs both, and it fetches from both sources. Or try it interactively at
http://127.0.0.1:8000/docs.

An empty or >500-character question returns `422`; a Gemini or Superhero API failure returns
`502` with the real reason.
