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

# Install the global `tools` CLI dispatcher into ~/.local/bin
BIN_DIR="${TOOLS_BIN_DIR:-$HOME/.local/bin}"
mkdir -p "$BIN_DIR"
chmod +x "$DIR/bin/tools"
ln -sf "$DIR/bin/tools" "$BIN_DIR/tools"
echo "Installed CLI dispatcher: $BIN_DIR/tools -> $DIR/bin/tools"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) echo "Warning: $BIN_DIR is not in your PATH. Add it to use the 'tools' command." ;;
esac

echo ""
echo "All tools are ready."
echo "Run ./start-hub.sh to open the dashboard at http://localhost:7777"
echo "Run 'tools' to list the command line interfaces."
