"""In-memory conversation history: keeps the last few turns for the life of the running
process, and summarizes them before each answer so prompt size stays bounded as a conversation
grows instead of including the raw transcript verbatim.

This is a single global history, not per-session - main.py's /ask endpoint has no session or
conversation ID, so this keeps that request/response contract unchanged. It's plain in-memory
state (a deque), never written to disk, so restarting the process clears it automatically.
"""

from collections import deque

from services.gemini import call_gemini

MAX_TURNS = 5

_history: deque[tuple[str, str]] = deque(maxlen=MAX_TURNS)

SUMMARY_SYSTEM_PROMPT = (
    "Summarize the conversation below in 2-4 short sentences. Keep only details that would "
    "matter for understanding a follow-up question - names, topics, and key facts already "
    "given. Do not add anything that wasn't actually said."
)


def add_turn(question: str, answer: str) -> None:
    """Record a finished question/answer turn. Oldest turn drops off past MAX_TURNS."""
    _history.append((question, answer))


def get_summary() -> str:
    """Summarize the stored history into a short string, or "" if there's no history yet."""
    if not _history:
        return ""

    transcript = "\n".join(f"Q: {q}\nA: {a}" for q, a in _history)
    return call_gemini(system_prompt=SUMMARY_SYSTEM_PROMPT, user_message=transcript)


def reset() -> None:
    """Clear the history. Mainly useful for tests."""
    _history.clear()
