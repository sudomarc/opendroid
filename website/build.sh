#!/usr/bin/env bash
# Build the static OpenDroid website.
#
# This site is intentionally tool-free: copy the publishable static files and
# validate JavaScript syntax when Node is available. Avoid regex minification;
# it can silently corrupt valid CSS/JavaScript.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"

printf '%s\n' 'Building OpenDroid website...'
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

cp -r "$SCRIPT_DIR/assets" "$DIST_DIR/assets"
cp -r "$SCRIPT_DIR/css" "$DIST_DIR/css"
cp -r "$SCRIPT_DIR/js" "$DIST_DIR/js"
cp "$SCRIPT_DIR"/*.html "$DIST_DIR/"
cp "$SCRIPT_DIR"/robots.txt "$DIST_DIR/"
cp "$SCRIPT_DIR"/sitemap.xml "$DIST_DIR/"
cp "$SCRIPT_DIR"/llms.txt "$DIST_DIR/"

if command -v node >/dev/null 2>&1; then
  node --check "$DIST_DIR/js/main.js"
  node --check "$DIST_DIR/js/theme-init.js"
fi

printf '%s\n' "Build complete: $DIST_DIR"
