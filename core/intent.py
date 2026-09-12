"""Classifies a question into one of three intents: "dataset", "superhero", or "both"."""

import json

from services.gemini import call_gemini
from sources.dataset import load_dataset

PROMPT_PATH = "prompts/intent_system.txt"
VALID_INTENTS = {"dataset", "superhero", "both"}
DATASET_SAMPLE_SIZE = 5
DATASET_SAMPLE_PLACEHOLDER = "<<DATASET_SAMPLE>>"


def classify_intent(question: str) -> str:
    """Ask Gemini which source(s) the question needs. The prompt is shown a live sample of the
    dataset instead of a hardcoded topic description, so swapping data/football.txt for a
    different file doesn't require editing this prompt by hand. Falls back to "both" if the
    classifier's reply can't be parsed, rather than crashing the request."""
    with open(PROMPT_PATH, encoding="utf-8") as f:
        prompt_template = f.read()

    sample = "\n".join(load_dataset()[:DATASET_SAMPLE_SIZE])
    system_prompt = prompt_template.replace(DATASET_SAMPLE_PLACEHOLDER, sample)

    raw_reply = call_gemini(system_prompt=system_prompt, user_message=question)

    try:
        intent = json.loads(raw_reply).get("intent", "").strip().lower()
    except (json.JSONDecodeError, AttributeError):
        intent = ""

    return intent if intent in VALID_INTENTS else "both"
