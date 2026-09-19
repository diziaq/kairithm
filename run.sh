#!/bin/bash
set -euo pipefail

# Starts the tool and prints the address to open.
# Any argument is passed on to run.py, so ./run.sh --port 9000 works.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

VENV_PYTHON=".venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "ERROR: $VENV_PYTHON not found. Run ./init.sh first."
  exit 1
fi

# exec replaces this shell, so Ctrl-C reaches the server instead of the wrapper.
exec "$VENV_PYTHON" run.py "$@"
