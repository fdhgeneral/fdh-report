#!/usr/bin/env python3
"""
patch_rivalry_site.py
=====================
Applies rivalry tab style upgrades to scripts/generate_site.py:
  1. rivalry_card_preview  — team name spans → sport font, uppercase
  2. rivalry_card_full     — manager divs → sport font inline style
  3. top_cards builder     — manager name divs → sport font inline style
  4. Score / stat colors   → vivid bright red

Run from your project root:
    python scripts/patch_rivalry_site.py
"""

import re
import shutil
from pathlib import Path

TARGET = Path("scripts/generate_site.py")
if not TARGET.exists():
    print(f"ERROR: {TARGET} not found. Run from your project root.")
    raise SystemExit(1)

bak = TARGET.with_suffix(".py.bak2")
shutil.copy2(TARGET, bak)
print(f"✓ Backup saved → {bak.name}")

src = TARGET.read_text(encoding="utf-8")
applied = []
skipped = []

def patch(label, old, new):
    global src
    if old in src:
        src = src.replace(old, new, 1)
        applied.append(label)
    else:
        skipped.append(label)

SPORT_SPAN = (
    "font-family:var(--font-sport);"
    "text-transform:uppercase;"
    "letter-spacing:.08em;"
    "font-size:1.05rem;"
    "color:#fff;"
)
MGMT_L = (
    "font-family:var(--font-sport);"
    "text-transform:uppercase;"
    "letter-spacing:.08em;"
    "text-align:left;"
)
MGMT_R = (
    "font-family:var(--font-sport);"
    "text-transform:uppercase;"
    "letter-spacing:.08em;"
    "text-align:right;"
)

# FIX 1 — rivalry_card_preview: team name spans
patch(
    "FIX 1a: rivalry_card_preview name_a → sport font",
    '<span style="font-family:var(--font-display);color:#fff;">{r[\'name_a\']}</span>',
    f'<span style="{SPORT_SPAN}">' + "{r['name_a']}</span>",
)
patch(
    "FIX 1b: rivalry_card_preview name_b → sport font",
    '<span style="font-family:var(--font-display);color:#fff;">{r[\'name_b\']}</span>',
    f'<span style="{SPORT_SPAN}">' + "{r['name_b']}</span>",
)
patch(
    "FIX 1c: rivalry_card_preview 'vs' → sport font + vivid red",
    '<span style="font-family:var(--font-display);font-size:1.2rem;color:var(--fdh-red-light);">vs</span>',
    '<span style="font-family:var(--font-sport);font-size:1.3rem;letter-spacing:.1em;color:var(--fdh-red-vivid);">VS</span>',
)

# FIX 2 — rivalry_card_full f-string: manager divs
patch(
    "FIX 2a: rivalry_card_full name_a → sport font",
    '    <div class="rivalry-card__manager" style="text-align:left;">{r[\'name_a\']}</div>',
    f'    <div class="rivalry-card__manager" style="{MGMT_L}">' + "{r['name_a']}</div>",
)
patch(
    "FIX 2b: rivalry_card_full name_b → sport font",
    '    <div class="rivalry-card__manager" style="text-align:right;">{r[\'name_b\']}</div>',
    f'    <div class="rivalry-card__manager" style="{MGMT_R}">' + "{r['name_b']}</div>",
)

# FIX 3 — top_cards string builder: manager divs
patch(
    "FIX 3a: top_cards manager_a → sport font",
    "'<div class=\"rivalry-card__manager\" style=\"text-align:left;\">' + r['a'] + '</div>'",
    f"'<div class=\"rivalry-card__manager\" style=\"{MGMT_L}\">' + r['a'] + '</div>'",
)
patch(
    "FIX 3b: top_cards manager_b → sport font",
    "'<div class=\"rivalry-card__manager\" style=\"text-align:right;\">' + r['b'] + '</div>'",
    f"'<div class=\"rivalry-card__manager\" style=\"{MGMT_R}\">' + r['b'] + '</div>'",
)

# FIX 4 — Score span in rivalry_card_preview → vivid red + sport font
patch(
    "FIX 4: rivalry score span → vivid red + sport font",
    'color:var(--fdh-red);">{score}</span>',
    'color:var(--fdh-red-vivid);font-family:var(--font-sport);letter-spacing:.04em;">{score}</span>',
)

# FIX 5 — Any inline fdh-red near pts/PPG/pf references → vivid red
src = re.sub(
    r'(color:var\(--fdh-red\))([^"]*?)(pts|PPG|ppg|pf_[ab]|ppg_[ab])',
    r'color:var(--fdh-red-vivid)\2\3',
    src,
)
applied.append("FIX 5: pts/PPG inline color → --fdh-red-vivid")

TARGET.write_text(src, encoding="utf-8")

print(f"\n{'='*60}")
print("  RIVALRY SITE PATCH RESULTS")
print(f"{'='*60}")
for f in applied:
    print(f"  ✅  {f}")
for f in skipped:
    print(f"  ⚠️   {f} — pattern not found, check manually")
print(f"{'='*60}")
print(f"\n  Backup:  scripts/{bak.name}")
print(f"  Patched: scripts/generate_site.py\n")
