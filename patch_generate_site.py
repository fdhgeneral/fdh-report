#!/usr/bin/env python3
"""
patch_generate_site.py
======================
Applies all 8 fixes to scripts/generate_site.py in-place.

Run from your project root:
    python scripts/patch_generate_site.py

A .bak backup is saved before any changes are made.
"""

import shutil
import sys
from pathlib import Path

TARGET = Path(__file__).parent / "generate_site.py"

if not TARGET.exists():
    print(f"ERROR: {TARGET} not found. Run from your project root.")
    sys.exit(1)

bak = TARGET.with_suffix(".py.bak")
shutil.copy2(TARGET, bak)
print(f"✓ Backup saved → {bak.name}")

src = TARGET.read_text(encoding="utf-8")
original_lines = len(src.splitlines())
applied  = []
skipped  = []

def patch(label, old, new):
    global src
    if old in src:
        src = src.replace(old, new, 1)
        applied.append(label)
    else:
        skipped.append(label)


# ── FIX 1: Remove duplicate def merge_stats at ~line 47 ─────────────────────
lines = src.splitlines(keepends=True)
merge_idxs = [i for i, ln in enumerate(lines) if ln.strip().startswith("def merge_stats(")]

if len(merge_idxs) >= 2:
    first, second = merge_idxs[0], merge_idxs[1]
    cut_to = second
    for i in range(first + 1, second):
        if lines[i].startswith("def "):
            cut_to = i
            break
    src = "".join(lines[:first] + lines[cut_to:])
    applied.append(f"FIX 1: Removed duplicate def merge_stats (lines {first+1}–{cut_to})")
else:
    skipped.append("FIX 1: Only one def merge_stats found — no duplicate removed")


# ── FIX 2: Remove duplicate def main() stub at ~line 1083 ───────────────────
lines = src.splitlines(keepends=True)
main_idxs = [i for i, ln in enumerate(lines) if ln.rstrip() == "def main():"]

if len(main_idxs) >= 2:
    stub_start = main_idxs[0]
    real_start = main_idxs[1]
    src = "".join(lines[:stub_start] + lines[real_start:])
    applied.append(f"FIX 2: Removed stub def main() (lines {stub_start+1}–{real_start})")
else:
    skipped.append("FIX 2: Only one def main() found — no stub removed")


# ── FIX 3a: Fix unindented comment inside main() ────────────────────────────
patch(
    "FIX 3a: Fixed missing indent on '# Load merged Yahoo + Sleeper stats'",
    'def main():\n# Load merged Yahoo + Sleeper stats\n    stats = load("stats.json")',
    'def main():\n    # Load merged Yahoo + Sleeper stats\n    stats = load("stats.json")',
)


# ── FIX 3b: Move None guard BEFORE the GOAT loop in main() ──────────────────
patch(
    "FIX 3b: Moved 'if stats is None' guard before stats[\"managers\"] access",
    (
        '    # Compute GOAT scores using merged totals\n'
        '    for m in stats["managers"]:\n'
        '        wins     = m.get("total_wins", 0)\n'
        '        points   = m.get("total_points", 0)\n'
        '        titles   = m.get("championships", 0)\n'
        '        playoffs = m.get("playoff_apps", 0)\n'
        '\n'
        '        goat = (\n'
        '            wins * 2 +\n'
        '            points / 100 +\n'
        '            titles * 10 +\n'
        '            playoffs * 1\n'
        '        )\n'
        '\n'
        '        m["goat_score"] = goat\n'
        '\n'
        '    if stats is None:\n'
        '        print("\u26a0  _data/stats.json not found \u2014 generating placeholder site.")\n'
        '        stats = {"managers": [], "rivalries": [], "generated_at": BUILD_TS}'
    ),
    (
        '    if stats is None:\n'
        '        print("\u26a0  _data/stats.json not found \u2014 generating placeholder site.")\n'
        '        stats = {"managers": [], "rivalries": [], "generated_at": BUILD_TS}\n'
        '\n'
        '    # Compute GOAT scores using merged totals\n'
        '    for m in stats["managers"]:\n'
        '        wins     = m.get("total_wins", 0)\n'
        '        points   = m.get("total_points", 0)\n'
        '        titles   = m.get("championships", 0)\n'
        '        playoffs = m.get("playoff_apps", 0)\n'
        '\n'
        '        goat = (\n'
        '            wins * 2 +\n'
        '            points / 100 +\n'
        '            titles * 10 +\n'
        '            playoffs * 1\n'
        '        )\n'
        '\n'
        '        m["goat_score"] = goat'
    ),
)


# ── FIX 4: Fix Yahoo field names in merge_stats ──────────────────────────────
patch(
    "FIX 4: Fixed Yahoo field names (total_wins→wins, total_losses→losses)",
    '            "wins": y.get("total_wins", 0),\n'
    '            "losses": y.get("total_losses", 0),',
    '            "wins": y.get("wins", 0),\n'
    '            "losses": y.get("losses", 0),',
)


# ── FIX 5: Stamp total_* aliases in merge_stats before return ────────────────
patch(
    "FIX 5: Added total_* field stamping in merge_stats",
    (
        '    # Return unified stats object\n'
        '    return {\n'
        '        "managers": list(merged.values()),\n'
        '        "generated_at": sleeper.get("generated_at"),\n'
        '    }'
    ),
    (
        '    # Stamp total_* aliases so HOF / GOAT / standings / records can read them\n'
        '    managers_out = []\n'
        '    for m in merged.values():\n'
        '        m["total_wins"]    = m.get("wins", 0)\n'
        '        m["total_losses"]  = m.get("losses", 0)\n'
        '        m["total_ties"]    = m.get("ties", 0)\n'
        '        m["total_points"]  = round(m.get("pf", 0.0), 2)\n'
        '        m["total_pa"]      = round(m.get("pa", 0.0), 2)\n'
        '        m["total_seasons"] = m.get("seasons", 0)\n'
        '        m.setdefault("runner_ups", 0)\n'
        '        total_games = m["total_wins"] + m["total_losses"] + m["total_ties"]\n'
        '        m["win_pct"] = round(m["total_wins"] / total_games, 4) if total_games else 0.0\n'
        '        managers_out.append(m)\n'
        '\n'
        '    # Return unified stats object\n'
        '    return {\n'
        '        "managers": managers_out,\n'
        '        "generated_at": sleeper.get("generated_at"),\n'
        '    }'
    ),
)


# ── FIX 6: hof_card_html → use total_ fields ────────────────────────────────
patch(
    "FIX 6: hof_card_html updated to use total_wins/losses/points/seasons",
    (
        '    w, l    = m.get("wins", 0), m.get("losses", 0)\n'
        '    wp      = win_pct_str(w, l, m.get("ties", 0))\n'
        "    pf      = f\"{m.get('pf', 0):,.1f}\"\n"
        '    titles  = m.get("championships", 0)\n'
        '    goat    = m.get("goat_score", 0)\n'
        '    seasons = m.get("seasons", 0)'
    ),
    (
        '    w, l    = m.get("total_wins", 0), m.get("total_losses", 0)\n'
        '    wp      = win_pct_str(w, l, m.get("total_ties", 0))\n'
        "    pf      = f\"{m.get('total_points', 0):,.1f}\"\n"
        '    titles  = m.get("championships", 0)\n'
        '    goat    = m.get("goat_score", 0)\n'
        '    seasons = m.get("total_seasons", 0)'
    ),
)


# ── FIX 7: standings_row → use total_ fields ────────────────────────────────
patch(
    "FIX 7: standings_row updated to use total_wins/losses/ties/points/pa/seasons",
    (
        '    w, l, t  = m.get("wins", 0), m.get("losses", 0), m.get("ties", 0)\n'
        '    wp       = win_pct_str(w, l, t)\n'
        "    pf       = f\"{m.get('pf', 0):,.1f}\"\n"
        "    pa       = f\"{m.get('pa', 0):,.1f}\"\n"
        '    playoffs = m.get("playoff_apps", 0)\n'
        '    titles   = m.get("championships", 0)\n'
        '    seasons  = m.get("seasons", 0)'
    ),
    (
        '    w, l, t  = m.get("total_wins", 0), m.get("total_losses", 0), m.get("total_ties", 0)\n'
        '    wp       = win_pct_str(w, l, t)\n'
        "    pf       = f\"{m.get('total_points', 0):,.1f}\"\n"
        "    pa       = f\"{m.get('total_pa', 0):,.1f}\"\n"
        '    playoffs = m.get("playoff_apps", 0)\n'
        '    titles   = m.get("championships", 0)\n'
        '    seasons  = m.get("total_seasons", 0)'
    ),
)


# ── FIX 8: division_card → use total_ fields for win % ──────────────────────
patch(
    "FIX 8: division_card updated to use total_wins/total_losses for win %",
    'f\'{win_pct_str(m.get("wins",0), m.get("losses",0))} W%</span></li>\'',
    'f\'{win_pct_str(m.get("total_wins",0), m.get("total_losses",0))} W%</span></li>\'',
)


# ── Write ────────────────────────────────────────────────────────────────────
TARGET.write_text(src, encoding="utf-8")
new_lines = len(src.splitlines())

print(f"\n{'='*62}")
print(f"  PATCH RESULTS  ({new_lines} lines, was {original_lines})")
print(f"{'='*62}")
for fix in applied:
    print(f"  ✅  {fix}")
for fix in skipped:
    print(f"  ⚠️   {fix}")
    print(f"       └─ Pattern not found — apply this fix manually.")
print(f"{'='*62}")
print(f"\n  Backup:  scripts/{bak.name}")
print(f"  Patched: scripts/generate_site.py")
print()
print("  Next steps:")
print("    1. python scripts/patch_stats.py       ← stamp total_* into stats.json")
print("    2. python scripts/generate_site.py     ← regenerate the site")
print()
