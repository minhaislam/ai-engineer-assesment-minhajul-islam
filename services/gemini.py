"""Gemini LLM client. The only file in the project that knows Gemini exists.

Every other module that needs an LLM call goes through call_gemini() — swapping providers
later means changing only this file.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Build the Gemini client once and reuse it for every call (not per-request)."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in the environment")

    return genai.Client(api_key=GEMINI_API_KEY)


def call_gemini(system_prompt: str, user_message: str) -> str:
    """Send one prompt to Gemini and return the plain text response."""
    client = _get_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_message,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    return response.text


if __name__ == "__main__":
    answer = call_gemini(
        system_prompt="You are a concise assistant. Answer in one short sentence.",
        user_message="What is the capital of France?",
    )
    print(answer)
