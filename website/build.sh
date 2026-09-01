#!/usr/bin/env bash
#
# build.sh — Build the static OpenDroid website.
# Copies publishable assets and performs syntax checks without a Node build runtime.
#
# Usage:
#   cd website && bash build.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="${SCRIPT_DIR}/dist"

log() { printf '%s\n' "$*"; }

log "🔨 Building OpenDroid website..."
log "   Source: ${SCRIPT_DIR}"
log "   Output: ${DIST_DIR}"
log ""

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

log "📦 Copying files..."
cp -r "$SCRIPT_DIR/assets" "$DIST_DIR/assets"
cp -r "$SCRIPT_DIR/css" "$DIST_DIR/css"
cp -r "$SCRIPT_DIR/js" "$DIST_DIR/js"
cp "$SCRIPT_DIR"/*.html "$DIST_DIR/"
cp "$SCRIPT_DIR/sitemap.xml" "$DIST_DIR/"
cp "$SCRIPT_DIR/robots.txt" "$DIST_DIR/"
cp "$SCRIPT_DIR/llms.txt" "$DIST_DIR/"

# Keep source files intact. The previous regex-based CSS/JS minification could
# corrupt valid source. The current static site is small enough that correctness
# is preferable to an unsafe pseudo-minifier; a real bundler can be introduced
# later if measurements justify it.
log "⚡ Validating JavaScript syntax..."
if command -v node >/dev/null 2>&1; then
  node --check "$DIST_DIR/js/main.js"
  node --check "$DIST_DIR/js/theme-init.js"
fi

log ""
log "✅ Build complete!"
src_size=$(du -sh "$SCRIPT_DIR" --exclude="$DIST_DIR" 2>/dev/null | cut -f1 || du -sh "$SCRIPT_DIR" | cut -f1)
dist_size=$(du -sh "$DIST_DIR" | cut -f1)
log "   Source size: ${src_size}"
log "   Dist size:   ${dist_size}"
log "   Output:      ${DIST_DIR}/"
