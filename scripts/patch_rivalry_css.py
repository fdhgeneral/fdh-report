#!/usr/bin/env python3
"""
patch_rivalry_css.py
====================
Applies rivalry tab style upgrades to assets/css/fdh.css:
  1. Imports Bebas Neue from Google Fonts (sport condensed font)
  2. Adds --font-sport and --fdh-red-vivid CSS variables
  3. Updates .rivalry-card__manager to use sport font
  4. Adds .rivalry-pts-stat class for bright red pts/PPG display
  5. Brightens rivalry-badge border color

Run from your project root:
    python scripts/patch_rivalry_css.py
"""

import re
import shutil
from pathlib import Path

CSS = Path("assets/css/fdh.css")
if not CSS.exists():
    print(f"ERROR: {CSS} not found. Run from your project root.")
    raise SystemExit(1)

bak = CSS.with_suffix(".css.bak")
shutil.copy2(CSS, bak)
print(f"✓ Backup saved → {bak.name}")

src = CSS.read_text(encoding="utf-8")
applied = []
skipped = []

def patch(label, old, new):
    global src
    if old in src:
        src = src.replace(old, new, 1)
        applied.append(label)
    else:
        skipped.append(label)

# FIX 1: Add Bebas Neue Google Fonts import at very top
BEBAS_IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');\n"
if BEBAS_IMPORT.strip() not in src:
    src = BEBAS_IMPORT + src
    applied.append("FIX 1: Added Bebas Neue Google Fonts import")
else:
    skipped.append("FIX 1: Bebas Neue import already present")

# FIX 2a: Add --font-sport variable
patch(
    "FIX 2a: Added --font-sport variable",
    "  --font-display: 'Oswald', 'Impact', Arial Narrow, sans-serif;",
    "  --font-sport:   'Bebas Neue', 'Oswald', 'Impact', sans-serif;\n"
    "  --font-display: 'Oswald', 'Impact', Arial Narrow, sans-serif;",
)

# FIX 2b: Add --fdh-red-vivid variable
patch(
    "FIX 2b: Added --fdh-red-vivid variable (#FF2244)",
    "  --fdh-red:        #C41230;",
    "  --fdh-red:        #C41230;\n"
    "  --fdh-red-vivid:  #FF2244;",
)

# FIX 3: Update or append .rivalry-card__manager sport font rule
if ".rivalry-card__manager" in src:
    src = re.sub(
        r'(\.rivalry-card__manager\s*\{)',
        r'\1\n  font-family: var(--font-sport);\n  text-transform: uppercase;\n  letter-spacing: .08em;',
        src,
    )
    applied.append("FIX 3: Injected sport font into existing .rivalry-card__manager rule")
else:
    src += """
/* ── Rivalry card sport-style manager names ── */
.rivalry-card__manager {
  font-family: var(--font-sport);
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: 1.15rem;
}
"""
    applied.append("FIX 3: Appended .rivalry-card__manager sport font rule")

# FIX 4: Add .rivalry-pts-stat utility class
if ".rivalry-pts-stat" not in src:
    src += """
/* ── Rivalry pts / PPG stat — vivid red so it pops ── */
.rivalry-pts-stat {
  color: var(--fdh-red-vivid) !important;
  font-weight: 700;
  font-family: var(--font-sport);
  letter-spacing: .04em;
}
"""
    applied.append("FIX 4: Added .rivalry-pts-stat class (bright red, sport font)")
else:
    skipped.append("FIX 4: .rivalry-pts-stat already present")

# FIX 5: Brighten rivalry badge border and text color
patch(
    "FIX 5: Rivalry badge border → vivid red",
    "  border: 1px solid rgba(196,18,48,.25);\n  color: var(--fdh-red-dark);",
    "  border: 1px solid rgba(255,34,68,.45);\n  color: var(--fdh-red-vivid);",
)

CSS.write_text(src, encoding="utf-8")

print(f"\n{'='*60}")
print("  CSS PATCH RESULTS")
print(f"{'='*60}")
for f in applied:
    print(f"  ✅  {f}")
for f in skipped:
    print(f"  ⚠️   {f} — check manually")
print(f"{'='*60}")
print(f"\n  Backup:  assets/{bak.name}")
print(f"  Patched: assets/css/fdh.css\n")
