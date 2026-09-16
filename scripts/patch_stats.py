#!/usr/bin/env python3
"""
patch_stats.py
==============
Stamps total_wins, total_losses, total_ties, total_points, total_pa,
and total_seasons onto every manager record in _data/stats.json.

Run ONCE from your project root to repair the existing file so that
HOF, GOAT, standings, and records sections can read total_ fields
immediately — even before a full Yahoo re-merge.

Usage:
    python scripts/patch_stats.py
    python scripts/patch_stats.py --file path/to/stats.json
"""

import json
import sys
from pathlib import Path

# ── Locate stats.json ────────────────────────────────────────────
if "--file" in sys.argv:
    stats_path = Path(sys.argv[sys.argv.index("--file") + 1])
else:
    stats_path = Path(__file__).parent.parent / "_data" / "stats.json"

if not stats_path.exists():
    print(f"ERROR: Could not find {stats_path}")
    sys.exit(1)

print(f"Patching: {stats_path}")

with open(stats_path, encoding="utf-8") as f:
    data = json.load(f)

managers = data.get("managers", [])
print(f"  Found {len(managers)} manager records")

for m in managers:
    w  = m.get("wins", 0)
    l  = m.get("losses", 0)
    t  = m.get("ties", 0)
    pf = m.get("pf", 0.0)
    pa = m.get("pa", 0.0)
    s  = m.get("seasons", 0)

    m["total_wins"]    = w
    m["total_losses"]  = l
    m["total_ties"]    = t
    m["total_points"]  = round(pf, 2)
    m["total_pa"]      = round(pa, 2)
    m["total_seasons"] = s
    m.setdefault("runner_ups", 0)  # guard against KeyError in merge

    total_games = w + l + t
    m["win_pct"] = round(w / total_games, 4) if total_games else 0.0

    print(f"  ✓ {m.get('display_name', '?'):30s}  "
          f"total_wins={w:>3}  total_losses={l:>3}  "
          f"total_points={pf:>8.2f}  total_seasons={s}")

with open(stats_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ Patched {len(managers)} managers → {stats_path}")
print("   Fields added: total_wins, total_losses, total_ties,")
print("                 total_points, total_pa, total_seasons, win_pct")
print("   runner_ups key guaranteed on all records.")
