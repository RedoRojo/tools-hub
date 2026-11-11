#!/usr/bin/env bash
# CLI launcher: resolves this tool's Python environment and runs cli.py.
# IMPORTANT: never `cd` here. Output files default to the caller's working directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"

if [ -n "${EXAMPLE_TOOL_PYTHON:-}" ] && [ -x "$EXAMPLE_TOOL_PYTHON" ]; then
    PYTHON_CMD="$EXAMPLE_TOOL_PYTHON"
elif [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
else
    echo "Creating virtual environment in $SCRIPT_DIR/.venv (first run)..." >&2
    python3 -m venv "$SCRIPT_DIR/.venv" >&2
    "$SCRIPT_DIR/.venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt" >&2
    PYTHON_CMD="$SCRIPT_DIR/.venv/bin/python"
fi

exec "$PYTHON_CMD" "$SCRIPT_DIR/cli.py" "$@"
