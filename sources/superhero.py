"""Superhero API client: fetch hero data by name and build a compact LLM context string."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("SUPERHERO_API_TOKEN")
BASE_URL = "https://superheroapi.com/api"
REQUEST_TIMEOUT = 10


class SuperheroAPIError(Exception):
    """Raised when the API can't be reached or returns something unexpected."""


class SuperheroNotFoundError(Exception):
    """Raised when the API understood the request but found no matching hero."""


def search_hero(name: str) -> list[dict]:
    """Search the Superhero API by name. A name can match several heroes, so this
    always returns a list (never assumes a single result)."""
    url = f"{BASE_URL}/{TOKEN}/search/{name}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise SuperheroAPIError(f"Could not reach Superhero API: {exc}") from exc

    if response.status_code != 200:
        raise SuperheroAPIError(f"Superhero API returned status {response.status_code}")

    try:
        data = response.json()
    except ValueError as exc:
        raise SuperheroAPIError("Superhero API returned malformed JSON") from exc

    if data.get("response") == "error":
        raise SuperheroNotFoundError(data.get("error", f"No hero found for '{name}'"))

    return data.get("results", [])


def build_hero_context(results: list[dict]) -> str:
    """Turn a list of hero results into one compact string, suitable as LLM context."""
    blocks = []

    for hero in results:
        biography = hero.get("biography", {})
        powerstats = hero.get("powerstats", {})

        blocks.append(
            f"Name: {hero.get('name')}\n"
            f"Full name: {biography.get('full-name')}\n"
            f"Publisher: {biography.get('publisher')}\n"
            f"Alignment: {biography.get('alignment')}\n"
            f"Powerstats: {powerstats}"
        )

    return "\n---\n".join(blocks)


if __name__ == "__main__":
    heroes = search_hero("Batman")
    print(f"Found {len(heroes)} match(es):\n")
    print(build_hero_context(heroes))
