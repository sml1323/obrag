#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TARGET_TRIPLE=$(rustc -vV | grep host | cut -d' ' -f2)

echo "=== Building FastAPI backend (PyInstaller) ==="
echo "Target: ${TARGET_TRIPLE}"

cd "$PROJECT_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

echo "Installing dependencies..."
uv sync

echo "Installing PyInstaller..."
uv pip install pyinstaller

echo "Running PyInstaller..."
uv run pyinstaller fastapi-server.spec --noconfirm --clean

BINARY_SRC="$PROJECT_DIR/dist/fastapi-server"
BINARY_DST="$PROJECT_DIR/front/src-tauri/binaries/fastapi-server-${TARGET_TRIPLE}"

if [ "$(uname)" = "Darwin" ] || [ "$(uname)" = "Linux" ]; then
    cp "$BINARY_SRC" "$BINARY_DST"
    chmod +x "$BINARY_DST"
else
    cp "${BINARY_SRC}.exe" "${BINARY_DST}.exe"
fi

echo "=== Backend binary copied to: ${BINARY_DST} ==="
echo "Done."
