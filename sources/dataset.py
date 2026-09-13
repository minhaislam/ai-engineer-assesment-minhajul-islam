"""Local text dataset: load a user-provided text file into memory once, then keyword-search it
for relevant lines.

The dataset location isn't hardcoded into this file - it comes from the DATASET_PATH
environment variable (set in .env), so any text file, anywhere on disk, can be used without
touching this code.

Expected format: one factual sentence per line (like data/football.txt), not a delimited
table. Retrieval here is "find the most relevant existing lines," not "parse structured
columns and compute an aggregate" - a tab/CSV file with a "most sold game" style question
won't work, since no single row answers that; the underlying data would need to be rewritten
as sentences (e.g. "Battle Titans sold 10.4 million units, the most of any game here.") first.
"""

import os
import re
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

DATASET_PATH = os.getenv("DATASET_PATH")
TOP_N = 5

# Common words that would otherwise inflate every line's overlap score without meaning anything.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "in", "on", "and", "to",
    "for", "what", "who", "how", "does", "do", "did", "with", "at", "by", "it",
}


@lru_cache(maxsize=1)
def load_dataset() -> list[str]:
    """Read the dataset file once and split it into individual lines (facts). Fails fast if
    DATASET_PATH isn't configured, rather than silently falling back to something else."""
    if not DATASET_PATH:
        raise RuntimeError(
            "DATASET_PATH is not set in the environment. Set it in .env to the path of the "
            "text file you want the chatbot to use as its dataset."
        )

    with open(DATASET_PATH, encoding="utf-8") as f:
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
