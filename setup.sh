#!/usr/bin/env bash
# ==============================================================================
# Tools Hub - Tool installation and synchronization script
# Clones or updates all independent tool repositories.
# ==============================================================================
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

GITHUB_USER="RedoRojo"
TOOLS=(
    "transcript"
    "pdf-toolbox"
    "qr-code"
    "kindle-toolbox"
)

echo "=========================================================="
echo " Synchronizing Tools Hub repositories (@$GITHUB_USER)"
echo "=========================================================="

for tool in "${TOOLS[@]}"; do
    if [ -d "$tool/.git" ]; then
        echo "Updating $tool..."
        git -C "$tool" pull --ff-only || echo "Warning: Could not fast-forward $tool (check local changes)."
    elif [ -d "$tool" ]; then
        echo "Directory '$tool/' already exists locally without .git. Skipping clone."
    else
        echo "Cloning $tool..."
        git clone "https://github.com/$GITHUB_USER/$tool.git" "$tool"
    fi
done

echo ""
echo "All tools are ready."
echo "Run ./start-hub.sh to open the dashboard at http://localhost:7777"
