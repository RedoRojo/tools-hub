#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

HUB_PORT="${HUB_PORT:-7777}"

# Check if the Hub is already running
if python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $HUB_PORT)); s.close()" 2>/dev/null; then
    echo "=========================================================="
    echo " Tools Hub is already running at:"
    echo " http://127.0.0.1:$HUB_PORT"
    echo "=========================================================="
else
    echo "Starting Tools Hub at http://127.0.0.1:$HUB_PORT ..."
    nohup python3 -u hub.py "$HUB_PORT" </dev/null > hub.log 2>&1 &
    PID=$!
    echo "Tools Hub started in the background (PID: $PID, log: hub.log)"
    
    # Wait until it responds
    for i in {1..20}; do
        if python3 -c "import socket; s = socket.socket(); s.connect(('127.0.0.1', $HUB_PORT)); s.close()" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done
fi

# Open in default browser if xdg-open is available
if command -v xdg-open >/dev/null 2>&1; then
    echo "Opening Tools Hub in your browser..."
    xdg-open "http://127.0.0.1:$HUB_PORT" >/dev/null 2>&1 &
fi

echo "=========================================================="
echo " Active Dashboard: http://127.0.0.1:$HUB_PORT"
echo "=========================================================="
