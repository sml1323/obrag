#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONT_DIR="$PROJECT_DIR/front"
BUNDLE_DIR="$FRONT_DIR/src-tauri/target/release/bundle"

echo "=========================================="
echo "  Obsidian RAG — Full Tauri Build"
echo "=========================================="

echo ""
echo "[1/4] Building Python backend..."
bash "$SCRIPT_DIR/build-backend.sh"

echo ""
echo "[2/4] Building Next.js frontend..."
bash "$SCRIPT_DIR/build-frontend.sh"

echo ""
echo "[3/4] Building Tauri app (.app bundle)..."
cd "$FRONT_DIR"
npx tauri build

APP_PATH="$BUNDLE_DIR/macos/Obsidian RAG.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: .app bundle not found at $APP_PATH"
    exit 1
fi
echo "  .app bundle created: $APP_PATH"

echo ""
echo "[4/4] Creating DMG installer..."
DMG_DIR="$BUNDLE_DIR/dmg"
mkdir -p "$DMG_DIR"
DMG_PATH="$DMG_DIR/Obsidian RAG_0.1.0_aarch64.dmg"
ICON_PATH="$FRONT_DIR/src-tauri/icons/icon.icns"

rm -f "$DMG_DIR"/*.dmg 2>/dev/null || true

if command -v create-dmg &>/dev/null; then
    create-dmg \
        --volname "Obsidian RAG" \
        --volicon "$ICON_PATH" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Obsidian RAG.app" 175 190 \
        --hide-extension "Obsidian RAG.app" \
        --app-drop-link 425 190 \
        "$DMG_PATH" \
        "$APP_PATH"
    echo "  DMG created: $DMG_PATH"
else
    echo "  WARNING: create-dmg not found. Install with: brew install create-dmg"
    echo "  Skipping DMG creation. Use the .app bundle directly."
fi

echo ""
echo "=========================================="
echo "  Build complete!"
echo ""
echo "  .app: $APP_PATH"
if [ -f "$DMG_PATH" ]; then
    echo "  .dmg: $DMG_PATH"
fi
echo "=========================================="
