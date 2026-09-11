"""FastAPI chatbot: single POST /ask endpoint.

For now this just forwards the question straight to Gemini and returns its answer — it proves
the HTTP -> LLM wiring end-to-end. Routing to the superhero API / local dataset, and the
classify-then-answer flow, come in a later step (see PROJECT_OVERVIEW.md).
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.gemini import call_gemini

app = FastAPI(title="Superhero Chatbot")

SYSTEM_PROMPT = "You are a helpful assistant. Answer the user's question directly and concisely."


class AskRequest(BaseModel):
    question: str


class Source(BaseModel):
    type: str
    detail: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")

    try:
        answer = call_gemini(system_prompt=SYSTEM_PROMPT, user_message=question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}") from exc

    return AskResponse(
        answer=answer,
        sources=[
            Source(
                type="gemini",
                detail="Answered directly from the LLM's own general knowledge (no retrieval yet)",
            )
        ],
    )
