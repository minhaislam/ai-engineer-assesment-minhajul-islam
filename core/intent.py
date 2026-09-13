"""Classifies a question into one of three intents: "dataset", "superhero", or "both"."""

import json
from pathlib import Path

from services.gemini import call_gemini
from sources.dataset import load_dataset

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root, regardless of cwd or OS
PROMPT_PATH = BASE_DIR / "prompts" / "intent_system.txt"
VALID_INTENTS = {"dataset", "superhero", "both"}
DATASET_SAMPLE_SIZE = 5
DATASET_SAMPLE_PLACEHOLDER = "<<DATASET_SAMPLE>>"


def classify_intent(question: str, history: str = "") -> str:
    """Ask Gemini which source(s) the question needs. The prompt is shown a live sample of the
    dataset instead of a hardcoded topic description, so pointing DATASET_PATH at a different
    file doesn't require editing this prompt by hand. Falls back to "both" if the classifier's
    reply can't be parsed, rather than crashing the request.

    `history` (a short conversation summary, if any) is included so a vague follow-up like
    "what about his weaknesses?" can still be classified using what was discussed before."""
    with open(PROMPT_PATH, encoding="utf-8") as f:
        prompt_template = f.read()

    sample = "\n".join(load_dataset()[:DATASET_SAMPLE_SIZE])
    system_prompt = prompt_template.replace(DATASET_SAMPLE_PLACEHOLDER, sample)

    user_message = f"Conversation so far: {history}\n\nNew question: {question}" if history else question
    raw_reply = call_gemini(system_prompt=system_prompt, user_message=user_message)

    try:
        intent = json.loads(raw_reply).get("intent", "").strip().lower()
    except (json.JSONDecodeError, AttributeError):
        intent = ""

    return intent if intent in VALID_INTENTS else "both"
