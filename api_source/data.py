import os

import requests
from dotenv import load_dotenv

load_dotenv()

SUPERHERO_API_TOKEN = os.environ["SUPERHERO_API_TOKEN"]
BASE_URL = f"https://superheroapi.com/api/{SUPERHERO_API_TOKEN}"
REQUEST_TIMEOUT_SECONDS = 10


class SuperheroAPIError(Exception):
    """Raised when the Superhero API can't be reached or returns something unexpected."""


class SuperheroNotFoundError(Exception):
    """Raised when the API responds successfully but finds no matching character."""


def search_hero(name: str) -> list[dict]:
    """Search the Superhero API by name and return the list of matching characters."""
    url = f"{BASE_URL}/search/{name}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise SuperheroAPIError(f"Request to Superhero API failed: {exc}") from exc

    if response.status_code != 200:
        raise SuperheroAPIError(
            f"Superhero API returned status {response.status_code}: {response.text}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise SuperheroAPIError("Superhero API returned invalid JSON") from exc

    if payload.get("response") == "error":
        raise SuperheroNotFoundError(payload.get("error", f"No character found for '{name}'"))

    return payload.get("results", [])


if __name__ == "__main__":
    results = search_hero("Superman")
    print(f"Found {len(results)} result(s):")
    for hero in results:
        print(f"- {hero['name']} (id {hero['id']})")
