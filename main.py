"""FastAPI chatbot: single POST /ask endpoint.

Request arrives -> validated by models/schemas.py (AskRequest) -> core/router.py classifies
the intent, fetches context from the right source(s), and answers it. See PROJECT_OVERVIEW.md
for the full data flow.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from core.router import handle_question
from models.schemas import AskRequest, AskResponse
from sources.dataset import load_dataset


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the dataset into memory once, at startup, instead of lazily on the first request:
    # the first user isn't the one who pays for the file read, and a missing/broken dataset
    # file fails fast at boot instead of surfacing as a confusing error on the first /ask call.
    load_dataset()
    yield


app = FastAPI(title="Superhero Chatbot", lifespan=lifespan)


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    try:
        return await handle_question(request.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to answer question: {exc}") from exc
