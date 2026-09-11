#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# FDH Site Builder
# Usage:
#   bash build.sh          — build only
#   bash build.sh --push   — build + git commit & push
# ─────────────────────────────────────────────────────────────
set -e  # stop immediately if any step fails

cd "$(dirname "$0")"  # always run from repo root

echo ""
echo "╔══════════════════════════════════════╗"
echo "║       FDH Site Builder               ║"
echo "╚══════════════════════════════════════╝"
echo ""

echo "── Step 1/5: Computing H2H rivalry data..."
python3 scripts/compute_rivalries.py

echo ""
echo "── Step 2/5: Patching site generator with H2H data..."
python3 scripts/patch_rivalries_gen.py

echo ""
echo "── Step 3/5: Generating all HTML pages..."
python3 scripts/generate_site.py

echo ""
echo "── Step 4/5: Injecting H2H lookup JS..."
python3 scripts/inject_h2h_js.py

echo ""
echo "── Step 5/5: Fixing colours + removing matrix table..."
python3 scripts/polish_rivalries.py

echo ""
echo "✅ Build complete!"
echo ""

# ── Optional: git push ───────────────────────────────────────
if [ "$1" = "--push" ]; then
  echo "── Pushing to GitHub..."
  git add -A
  git commit -m "chore: rebuild site $(date -u +%Y-%m-%dT%H:%MZ)"
  git push origin main
  echo "✅ Pushed!"
fi
