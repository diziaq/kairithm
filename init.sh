#!/bin/bash
set -euo pipefail

# Creates the virtual environment and installs the dependencies.
# Run it again at any time. It only does the work that is missing.
# Use --dev to add the test dependencies.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"
MIN_VERSION="3.11"

if ! command -v "$PYTHON" > /dev/null 2>&1; then
  echo "ERROR: $PYTHON not found. Install Python $MIN_VERSION or newer, or set PYTHON to its path."
  exit 1
fi

if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "ERROR: Python $MIN_VERSION or newer is required. Found $("$PYTHON" -V)."
  exit 1
fi

WITH_DEV=0
for arg in "$@"; do
  case "$arg" in
    --dev) WITH_DEV=1 ;;
    *)
      echo "ERROR: unknown option '$arg'. The only option is --dev."
      exit 1
      ;;
  esac
done

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Creating $VENV_DIR with $("$PYTHON" -V)"
  "$PYTHON" -m venv "$VENV_DIR"
else
  echo "Using the existing $VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"

echo "Installing the runtime dependencies"
"$PIP" install --quiet --disable-pip-version-check -r requirements.txt

if [ "$WITH_DEV" -eq 1 ]; then
  echo "Installing the test dependencies"
  "$PIP" install --quiet --disable-pip-version-check -r requirements-dev.txt
fi

mkdir -p sessions

echo
echo "Ready. Start the tool with ./run.sh"
if [ "$WITH_DEV" -eq 1 ]; then
  echo "Run the tests with $VENV_DIR/bin/python -m pytest tests/ -q"
fi
