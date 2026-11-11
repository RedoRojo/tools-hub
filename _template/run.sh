#!/usr/bin/env bash
# Web launcher used by Tools Hub.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x ".venv/bin/python" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
    .venv/bin/pip install --quiet -r requirements.txt
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8005}"
export HOST PORT

echo "Starting Example Tool at http://$HOST:$PORT ..."
exec .venv/bin/python app.py
