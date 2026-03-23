#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FRONT_DIR="$PROJECT_DIR/front"

echo "=== Building Next.js frontend (static export) ==="

cd "$FRONT_DIR"

if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

echo "Installing @tauri-apps/cli..."
npm install -D @tauri-apps/cli@latest

export TAURI_ENV_PLATFORM=1

echo "Cleaning .next cache..."
rm -rf "$FRONT_DIR/.next"

API_ROUTE_DIR="$FRONT_DIR/app/api"
API_ROUTE_BACKUP="$FRONT_DIR/.api-route-backup"

if [ -d "$API_ROUTE_DIR" ]; then
    echo "Temporarily moving Next.js API routes (incompatible with static export)..."
    mv "$API_ROUTE_DIR" "$API_ROUTE_BACKUP"
fi

echo "Building static export..."
npm run build
BUILD_EXIT=$?

if [ -d "$API_ROUTE_BACKUP" ]; then
    mv "$API_ROUTE_BACKUP" "$API_ROUTE_DIR"
    echo "Restored API routes."
fi

if [ $BUILD_EXIT -ne 0 ]; then
    echo "Build failed!"
    exit $BUILD_EXIT
fi

echo "=== Frontend built to: ${FRONT_DIR}/out ==="
echo "Done."
