#!/usr/bin/env bash
# One-time setup script: checks the OS and Python version, creates a virtual environment,
# installs requirements.txt into it, and verifies the required .env variables are set.
#
# Run with bash (no dependencies needed for this script itself - POSIX/bash + a system
# python3, since it has to work before requirements.txt is installed):
#
#     ./init.sh
#
# Or source it to also activate the venv in your current shell once setup finishes, instead
# of activating it yourself afterward:
#
#     source ./init.sh

# Detect whether this script is being sourced (`source ./init.sh` / `. ./init.sh`) rather than
# executed (`./init.sh` / `bash init.sh`). Sourcing runs in the caller's own shell process, so
# it's the only form that can activate the venv directly in the caller's shell (see the end of
# main()) - executing runs in a subprocess, so any activation there would be lost the moment
# the subprocess exits.
if (return 0 2>/dev/null); then
    SOURCED=1
else
    SOURCED=0
fi

# No `set -e`: under sourcing, errexit would tear down the caller's interactive shell on the
# first failing command instead of just stopping this script. Every step below checks its own
# commands explicitly and returns/exits on failure instead, so behavior is identical either way.
set -uo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$BASE_DIR/.venv"
REQUIREMENTS_FILE="$BASE_DIR/requirements.txt"
ENV_FILE="$BASE_DIR/.env"
REQUIRED_ENV_VARS=(SUPERHERO_API_TOKEN GEMINI_API_KEY DATASET_PATH)
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10
PYTHON_BIN=""

step() {
    printf "\n[%s/5] %s\n" "$1" "$2"
}

find_python() {
    # A `command -v` hit isn't enough on Windows: the WindowsApps python3/python entries on
    # PATH are App Execution Alias stubs that "exist" but fail (or prompt the Store) when run
    # if no real Python is installed, so each candidate must actually execute successfully.
    for candidate in python3 python py; do
        if command -v "$candidate" >/dev/null 2>&1 && "$candidate" --version >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    echo "ERROR: no working python3/python found on PATH." >&2
    return 1
}

check_os() {
    step 1 "Checking operating system"
    echo "  Detected: $(uname -s) ($(uname -sr))"
}

check_python_version() {
    step 2 "Checking Python version"
    PYTHON_BIN="$(find_python)" || return 1
    local version major minor
    version="$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')" || {
        echo "  ERROR: failed to run $PYTHON_BIN."
        return 1
    }
    echo "  Detected: Python $version"
    major="${version%%.*}"
    minor="${version##*.}"
    if [ "$major" -lt "$MIN_PYTHON_MAJOR" ] || { [ "$major" -eq "$MIN_PYTHON_MAJOR" ] && [ "$minor" -lt "$MIN_PYTHON_MINOR" ]; }; then
        echo "  ERROR: Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required."
        return 1
    fi
    echo "  OK"
}

venv_python_path() {
    if [ -x "$VENV_DIR/Scripts/python.exe" ]; then
        echo "$VENV_DIR/Scripts/python.exe"
    else
        echo "$VENV_DIR/bin/python"
    fi
}

create_venv() {
    step 3 "Creating virtual environment"
    if [ -d "$VENV_DIR" ]; then
        echo "  Already exists at $VENV_DIR, skipping."
        return 0
    fi
    echo "  Creating at $VENV_DIR ..."
    if ! "$PYTHON_BIN" -m venv "$VENV_DIR"; then
        echo "  ERROR: failed to create the virtual environment."
        return 1
    fi
    echo "  OK"
}

install_requirements() {
    step 4 "Installing requirements.txt"
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        echo "  ERROR: $REQUIREMENTS_FILE not found."
        return 1
    fi
    echo "  Installing into $VENV_DIR ..."
    if ! "$(venv_python_path)" -m pip install -q -r "$REQUIREMENTS_FILE"; then
        echo "  ERROR: pip install failed."
        return 1
    fi
    echo "  OK"
}

check_env_vars() {
    step 5 "Checking required environment variables"

    if [ ! -f "$ENV_FILE" ]; then
        echo "  ERROR: $ENV_FILE not found."
        echo "  Create one with:"
        for var in "${REQUIRED_ENV_VARS[@]}"; do
            echo "    $var=..."
        done
        return 1
    fi

    # Minimal .env parsing here (not python-dotenv): last matching line wins, surrounding
    # quotes are stripped.
    local missing=() var value
    for var in "${REQUIRED_ENV_VARS[@]}"; do
        value="$(grep -E "^[[:space:]]*${var}[[:space:]]*=" "$ENV_FILE" | tail -n1 | cut -d'=' -f2- | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e "s/^['\"]//" -e "s/['\"]$//")"
        if [ -n "$value" ]; then
            echo "  $var: OK"
        else
            echo "  $var: MISSING"
            missing+=("$var")
        fi
    done

    if [ "${#missing[@]}" -gt 0 ]; then
        local joined
        joined="$(IFS=,; echo "${missing[*]}")"
        echo ""
        echo "  ERROR: set these in .env: $joined"
        return 1
    fi
}

main() {
    check_os
    check_python_version || return 1
    create_venv || return 1
    install_requirements || return 1
    check_env_vars || return 1

    local activate_script
    if [ -x "$VENV_DIR/Scripts/python.exe" ]; then
        activate_script="$VENV_DIR/Scripts/activate"
    else
        activate_script="$VENV_DIR/bin/activate"
    fi

    echo ""
    if [ "$SOURCED" -eq 1 ]; then
        echo "Setup complete. Activating the virtual environment in this shell..."
        # shellcheck disable=SC1090
        source "$activate_script"
        echo "  Activated. Next step: uvicorn main:app --reload"
    else
        echo "Setup complete. Next steps:"
        echo "  1. Activate the environment: source \"$activate_script\""
        echo "  2. Run the API: uvicorn main:app --reload"
        echo ""
        echo "  Tip: run this script with 'source ./init.sh' next time to activate it"
        echo "  automatically once setup finishes."
    fi
}

main "$@"
