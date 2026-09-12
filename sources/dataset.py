"""Local text dataset: load football facts once, then keyword-search them for relevant lines.

Assumes the process is run from the repo root (same convention as the other demo scripts),
so the dataset file is found at data/football.txt.
"""

import re
from functools import lru_cache

DATA_PATH = "data/football.txt"
TOP_N = 5

# Common words that would otherwise inflate every line's overlap score without meaning anything.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "and", "to",
    "for", "what", "who", "how", "does", "do", "did", "with", "at", "by", "it",
}


@lru_cache(maxsize=1)
def load_dataset() -> list[str]:
    """Read the dataset file once and split it into individual lines (facts)."""
    with open(DATA_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    return [line.strip() for line in lines if line.strip()]


def _keywords(text: str) -> set[str]:
    """Lowercase, punctuation-free words, with stopwords removed."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in STOPWORDS}


def search_dataset(question: str) -> str:
    """Return the TOP_N dataset lines most relevant to the question, joined into one string."""
    question_words = _keywords(question)

    scored = []
    for line in load_dataset():
        overlap = len(question_words & _keywords(line))
        if overlap > 0:
            scored.append((overlap, line))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    top_lines = [line for _, line in scored[:TOP_N]]

    return "\n".join(top_lines)


if __name__ == "__main__":
    print(search_dataset("Who won the first World Cup?"))
