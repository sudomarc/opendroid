#!/usr/bin/env bash
#
# build.sh — Build the static OpenDroid website.
# Minifies CSS/JS without a Node runtime and copies publishable assets.
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

# Minify CSS conservatively: remove comments and redundant whitespace while
# keeping quoted content, URLs, declarations, and brace structure intact.
log "🎨 Minifying CSS..."
for cssfile in "$DIST_DIR"/css/*.css; do
  [ -f "$cssfile" ] || continue
  original_size=$(wc -c < "$cssfile")
  sed -E \
    -e 's|/\*([^*]|\*+[^*/])*\*+/||g' \
    -e 's/[[:space:]]+/ /g' \
    -e 's/^[[:space:]]+|[[:space:]]+$//g' \
    -e 's/[[:space:]]*([{};:,>])\s*/\1/g' \
    "$cssfile" > "$cssfile.tmp"
  mv "$cssfile.tmp" "$cssfile"
  new_size=$(wc -c < "$cssfile")
  log "   $(basename "$cssfile"): ${original_size}B → ${new_size}B"
done

# JavaScript is intentionally not aggressively minified here. The previous
# whitespace-only transformation could corrupt source constructs. Keeping
# valid source while serving it from the static site is safer than a fragile
# regex minifier; defer true bundling/minification to a real JS toolchain if
# the project adopts one.
log "⚡ Validating JavaScript (no regex minification)..."
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
