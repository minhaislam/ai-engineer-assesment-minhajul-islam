"""Manual check: extract hero name(s) from a free-form question, fetch their data, and see if
the final answer actually reflects it.

Not a pytest test - a script to validate the two-stage flow (extract names -> fetch context ->
answer) before wiring it into main.py's /ask endpoint. Handles two tricky cases on purpose:
- Multiple heroes in one question ("difference between Batman and Superman").
- A name with multiple API matches ("Superman" -> Superman, Cyborg Superman, ...) - all matches
  are included and Gemini is told to address the ambiguity instead of guessing.

Run with a question as an argument, or edit QUESTION below:
    python scripts/test_superhero_gemini.py "What is the difference between Batman and Superman?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.gemini import call_gemini
from sources.superhero import (
    SuperheroAPIError,
    SuperheroNotFoundError,
    build_hero_context,
    search_hero,
)

QUESTION = "Tell me about Superman?"

EXTRACT_SYSTEM_PROMPT = (
    "Identify every superhero or supervillain name mentioned in the user's question. "
    "Reply with ONLY a comma-separated list of names, nothing else. "
    "If no hero/villain name is mentioned, reply with exactly: NONE"
)

ANSWER_SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant. Answer the user's question using ONLY the superhero data "
    "below. If a name has multiple matches, they are all listed - address the ambiguity "
    "instead of guessing which one was meant. If the data doesn't answer the question, say so.\n\n"
    "{context}"
)


def extract_hero_names(question: str) -> list[str]:
    """Ask Gemini which hero name(s), if any, are mentioned in the question."""
    reply = call_gemini(system_prompt=EXTRACT_SYSTEM_PROMPT, user_message=question).strip()

    if reply.upper() == "NONE":
        return []

    return [name.strip() for name in reply.split(",") if name.strip()]


def gather_hero_context(names: list[str]) -> str:
    """Look up each name and combine their contexts into one block, labeled by name."""
    sections = []

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

    return "\n\n".join(sections) if sections else "No superhero data found."


def main() -> None:
    question = sys.argv[1] if len(sys.argv) > 1 else QUESTION

    names = extract_hero_names(question)
    print(f"--- Extracted hero name(s): {names or '(none)'} ---\n")

    context = gather_hero_context(names)
    print("--- Combined superhero context ---")
    print(context)
    print()

    system_prompt = ANSWER_SYSTEM_PROMPT_TEMPLATE.format(context=context)
    answer = call_gemini(system_prompt=system_prompt, user_message=question)

    print("--- Gemini's answer ---")
    print(answer)


if __name__ == "__main__":
    main()
