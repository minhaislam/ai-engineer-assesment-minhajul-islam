"""Classifies a question into one of three intents: "dataset", "superhero", or "both"."""

import json

from services.gemini import call_gemini

PROMPT_PATH = "prompts/intent_system.txt"
VALID_INTENTS = {"dataset", "superhero", "both"}


def classify_intent(question: str) -> str:
    """Ask Gemini which source(s) the question needs. Falls back to "both" if the
    classifier's reply can't be parsed, rather than crashing the request."""
    with open(PROMPT_PATH, encoding="utf-8") as f:
        system_prompt = f.read()

    raw_reply = call_gemini(system_prompt=system_prompt, user_message=question)

    try:
        intent = json.loads(raw_reply).get("intent", "").strip().lower()
    except (json.JSONDecodeError, AttributeError):
        intent = ""

    return intent if intent in VALID_INTENTS else "both"
