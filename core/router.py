"""The orchestrator: classify the question, fetch context from the right source(s), answer it."""

import asyncio
from pathlib import Path

from core import memory
from core.intent import classify_intent
from core.responder import generate_answer
from models.schemas import AskResponse
from services.gemini import call_gemini
from sources.dataset import DATASET_PATH, search_dataset
from sources.superhero import (
    SuperheroAPIError,
    SuperheroNotFoundError,
    build_hero_context,
    search_hero,
)

# A small extra classification step, specific to the superhero source: the question is
# free-form ("what are Batman's powers?"), but search_hero() needs an actual name.
HERO_EXTRACT_SYSTEM_PROMPT = (
    "Identify every superhero or supervillain name mentioned in the user's question. "
    "Reply with ONLY a comma-separated list of names, nothing else. "
    "If no hero/villain name is mentioned, reply with exactly: NONE. "
    "The message may start with 'Conversation so far: ...' before 'New question: ...' - use "
    "that only to resolve a vague reference (e.g. 'his weaknesses' meaning a hero named earlier)."
)


def _get_superhero_context(question: str, history: str = "") -> tuple[str, list[str]]:
    """Extract hero name(s) from the question, look each up, and combine their context.
    Returns (context_text, source_labels) - both empty if no hero could be identified."""
    user_message = f"Conversation so far: {history}\n\nNew question: {question}" if history else question
    reply = call_gemini(system_prompt=HERO_EXTRACT_SYSTEM_PROMPT, user_message=user_message).strip()
    names = [] if reply.upper() == "NONE" else [n.strip() for n in reply.split(",") if n.strip()]

    sections = []
    source_labels = []

    for name in names:
        try:
            results = search_hero(name)
        except SuperheroNotFoundError:
            sections.append(f"'{name}': no matching hero found in the Superhero API.")
            continue
        except SuperheroAPIError as exc:
            sections.append(f"'{name}': Superhero API unavailable ({exc}).")
            continue

        sections.append(f"Results for '{name}':\n{build_hero_context(results)}")
        source_labels.append(f"superhero_api: {name}")

    return "\n\n".join(sections), source_labels


def _get_dataset_context(question: str) -> tuple[str, list[str]]:
    """Keyword-search the local dataset. Returns (context_text, source_labels)."""
    context = search_dataset(question)
    label = f"dataset: {Path(DATASET_PATH).name}" if DATASET_PATH else "dataset"
    return context, ([label] if context else [])


async def handle_question(question: str) -> AskResponse:
    """Classify the question, gather context from the source(s) that intent calls for,
    then answer it. "both" fetches from superhero + dataset concurrently.

    Also maintains a short in-memory conversation history (see core/memory.py) so follow-up
    questions ("what about his weaknesses?") can be understood and answered coherently."""
    history = await asyncio.to_thread(memory.get_summary)
    intent = classify_intent(question, history)

    context_parts: list[str] = []
    sources: list[str] = []

    if intent == "superhero":
        context, labels = await asyncio.to_thread(_get_superhero_context, question, history)
        context_parts.append(context)
        sources.extend(labels)

    elif intent == "dataset":
        context, labels = await asyncio.to_thread(_get_dataset_context, question)
        context_parts.append(context)
        sources.extend(labels)

    else:  # "both"
        (hero_context, hero_labels), (dataset_context, dataset_labels) = await asyncio.gather(
            asyncio.to_thread(_get_superhero_context, question, history),
            asyncio.to_thread(_get_dataset_context, question),
        )
        context_parts.extend([hero_context, dataset_context])
        sources.extend(hero_labels)
        sources.extend(dataset_labels)

    combined_context = "\n\n".join(part for part in context_parts if part)
    if not combined_context:
        combined_context = "No relevant information was found for this question."

    response = generate_answer(
        question=question, context=combined_context, sources=sources, history=history
    )
    response.intent = intent

    memory.add_turn(question, response.answer)
    return response
