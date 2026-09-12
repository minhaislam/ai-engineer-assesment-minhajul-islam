"""FastAPI chatbot: single POST /ask endpoint.

Request arrives -> validated by models/schemas.py (AskRequest) -> core/router.py classifies
the intent, fetches context from the right source(s), and answers it. See PROJECT_OVERVIEW.md
for the full data flow.
"""

from fastapi import FastAPI, HTTPException

from core.router import handle_question
from models.schemas import AskRequest, AskResponse

app = FastAPI(title="Superhero Chatbot")


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest) -> AskResponse:
    try:
        return await handle_question(request.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to answer question: {exc}") from exc
