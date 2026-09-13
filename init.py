"""One-time setup script: checks the OS and Python version, creates a virtual environment,
installs requirements.txt into it, and verifies the required .env variables are set.

Run with whatever Python you have available (no dependencies needed for this script itself -
stdlib only, since it has to work before requirements.txt is installed):

    python init.py
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
ENV_FILE = BASE_DIR / ".env"
REQUIRED_ENV_VARS = ["SUPERHERO_API_TOKEN", "GEMINI_API_KEY", "DATASET_PATH"]


def step(number: int, title: str) -> None:
    print(f"\n[{number}/5] {title}")


def check_os() -> None:
    step(1, "Checking operating system")
    print(f"  Detected: {platform.system()} ({platform.platform()})")


def check_python_version() -> None:
    step(2, "Checking Python version")
    major, minor = sys.version_info[:2]
    print(f"  Detected: Python {major}.{minor}")
    if (major, minor) < MIN_PYTHON:
        print(f"  ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required.")
        sys.exit(1)
    print("  OK")


def venv_python_path() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def create_venv() -> None:
    step(3, "Creating virtual environment")
    if VENV_DIR.exists():
        print(f"  Already exists at {VENV_DIR}, skipping.")
        return

    print(f"  Creating at {VENV_DIR} ...")
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
    print("  OK")


def install_requirements() -> None:
    step(4, "Installing requirements.txt")
    if not REQUIREMENTS_FILE.exists():
        print(f"  ERROR: {REQUIREMENTS_FILE} not found.")
        sys.exit(1)

    print(f"  Installing into {VENV_DIR} ...")
    subprocess.run(
        [str(venv_python_path()), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS_FILE)],
        check=True,
    )
    print("  OK")


def check_env_vars() -> None:
    step(5, "Checking required environment variables")

    if not ENV_FILE.exists():
        print(f"  ERROR: {ENV_FILE} not found.")
        print("  Create one with:")
        for var in REQUIRED_ENV_VARS:
            print(f"    {var}=...")
        sys.exit(1)

    # Minimal .env parsing here (not python-dotenv): this script must run before
    # requirements.txt is installed, so it can't rely on third-party packages.
    found = {}
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            found[key.strip()] = value.strip().strip("'\"")

    missing = []
    for var in REQUIRED_ENV_VARS:
        present = bool(found.get(var))
        print(f"  {var}: {'OK' if present else 'MISSING'}")
        if not present:
            missing.append(var)

    if missing:
        print(f"\n  ERROR: set these in .env: {', '.join(missing)}")
        sys.exit(1)


def main() -> None:
    check_os()
    check_python_version()
    create_venv()
    install_requirements()
    check_env_vars()

    activate_cmd = (
        r".venv\Scripts\activate" if platform.system() == "Windows" else "source .venv/bin/activate"
    )
    print("\nSetup complete. Next steps:")
    print(f"  1. Activate the environment: {activate_cmd}")
    print("  2. Run the API: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
