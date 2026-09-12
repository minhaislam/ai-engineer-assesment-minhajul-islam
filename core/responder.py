"""Turns already-gathered context into the final answer. Doesn't know how the context was
built - it just uses it."""

from models.schemas import AskResponse
from services.gemini import call_gemini

PROMPT_PATH = "prompts/answer_system.txt"


def generate_answer(question: str, context: str, sources: list[str]) -> AskResponse:
    """Answer the question from the given context only, citing the given sources."""
    with open(PROMPT_PATH, encoding="utf-8") as f:
        system_prompt = f.read()

    source_list = ", ".join(sources) if sources else "none"
    user_message = (
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        f"Sources available: {source_list}"
    )

    answer = call_gemini(system_prompt=system_prompt, user_message=user_message)

    # intent is set by router.py, which is the caller that actually knows it.
    return AskResponse(answer=answer, sources=sources, intent="")
