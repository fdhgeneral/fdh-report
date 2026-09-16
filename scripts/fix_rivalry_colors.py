#!/usr/bin/env python3
"""
fix_rivalry_colors.py
=====================
Directly injects sport font + vivid red into assets/css/fdh.css
by prepending the Google Fonts import and appending CSS overrides.
No pattern matching — guaranteed to apply.

Run from your project root:
    python scripts/fix_rivalry_colors.py
"""
import shutil
from pathlib import Path

CSS = Path("assets/css/fdh.css")
if not CSS.exists():
    print(f"ERROR: {CSS} not found.")
    raise SystemExit(1)

shutil.copy2(CSS, CSS.with_suffix(".css.bak"))
print(f"✓ Backup saved")

src = CSS.read_text(encoding="utf-8")

# 1. Prepend Google Fonts import (must be at top to load)
IMPORT = "@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');\n\n"
if "Bebas+Neue" not in src:
    src = IMPORT + src
    print("✓ Added Bebas Neue font import")
else:
    print("- Bebas Neue already imported")

# 2. Append override block at bottom (wins via !important over inline styles)
OVERRIDES = """

/* ══════════════════════════════════════════
   FDH RIVALRY SPORT OVERRIDES
   ══════════════════════════════════════════ */

:root {
  --font-sport:    'Bebas Neue', 'Oswald', 'Impact', sans-serif;
  --fdh-red-vivid: #FF2244;
}

/* Manager / team names on rivalry cards */
.rivalry-card__manager {
  font-family: var(--font-sport) !important;
  text-transform: uppercase !important;
  letter-spacing: .09em !important;
  font-size: 1.15rem !important;
}

/* Points and PPG stat values */
.rivalry-card__meta span,
.rivalry-pts-stat,
[class*="rivalry"] .stat-val,
[class*="rivalry"] .ppg,
[class*="rivalry"] .pts {
  color: var(--fdh-red-vivid) !important;
}

/* Win/loss score values */
.rivalry-score__val {
  color: var(--fdh-red-vivid) !important;
}
.rivalry-score__val.leader {
  color: var(--fdh-red-vivid) !important;
  font-weight: 700;
}

/* Rivalry badge — brighter border */
.rivalry-badge {
  border-color: rgba(255, 34, 68, .5) !important;
  color: var(--fdh-red-vivid) !important;
}
"""

if "FDH RIVALRY SPORT OVERRIDES" not in src:
    src += OVERRIDES
    print("✓ Appended rivalry sport override CSS block")
else:
    print("- Override block already present (updating it)")
    # Replace existing block
    start = src.find("/* ══════════════════════════════════════════\n   FDH RIVALRY SPORT OVERRIDES")
    if start != -1:
        src = src[:start] + OVERRIDES
        print("✓ Refreshed existing override block")

CSS.write_text(src, encoding="utf-8")
print(f"\n✅ Done — assets/css/fdh.css updated")
print("   Run: python scripts/generate_site.py")
