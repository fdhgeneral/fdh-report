#!/usr/bin/env python3
"""
compute_rivalries.py
Reads all 6 seasons of Yahoo (2020-2023) + Sleeper (2024-2025) matchup data
and produces _data/rivalries_h2h.json for the interactive H2H lookup widget.
Run from repo root: python3 scripts/compute_rivalries.py
"""
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
DATA = ROOT / "_data"

NAME_MAP = {
    "justEATit":      "BROCKBAILBONDZ",
    "PaulyDsWalnuts": "scheeper",
    "Jarrin":         "Jarrin1225",
}
def yn(n): return NAME_MAP.get(str(n).strip(), str(n).strip())

# ── Load managers ─────────────────────────────────────────────────────────────
stats    = json.loads((DATA / "stats.json").read_text())
all_mgrs = stats["managers"]

active_mgrs = sorted(
    [m["display_name"] for m in all_mgrs
     if not m.get("yahoo_only", False) and m.get("seasons", 0) > 0],
    key=lambda n: -next((m.get("total_wins", 0) for m in all_mgrs if m["display_name"] == n), 0)
)
former_mgrs = sorted(
    [m["display_name"] for m in all_mgrs if m.get("yahoo_only", False)],
    key=lambda n: -next((m.get("total_wins", 0) for m in all_mgrs if m["display_name"] == n), 0)
)
all_managers_sorted = active_mgrs + former_mgrs
print(f"Managers: {len(active_mgrs)} active + {len(former_mgrs)} former = {len(all_managers_sorted)} total")

# ── Collect all games ─────────────────────────────────────────────────────────
all_games = []

def add_game(oa, pa, ob, pb, week, season, playoff=False, championship=False):
    oa = yn(oa); ob = yn(ob)
    if oa == ob: return
    if pa <= 0 and pb <= 0: return
    winner = oa if pa >= pb else ob
    all_games.append({
        "season":       str(season),
        "week":         int(week) if str(week).isdigit() else week,
        "a":            oa,
        "pts_a":        round(float(pa), 2),
        "b":            ob,
        "pts_b":        round(float(pb), 2),
        "winner":       winner,
        "margin":       round(abs(float(pa) - float(pb)), 2),
        "playoff":      bool(playoff),
        "championship": bool(championship),
    })

# Yahoo 2020-2023
for yr in ["2020", "2021", "2022", "2023"]:
    ymp = DATA / f"yahoo_matchups_{yr}.json"
    if not ymp.exists():
        print(f"  skip Yahoo {yr} (file not found)")
        continue
    games = json.loads(ymp.read_text())
    before = len(all_games)
    for g in games:
        a = g["teamA"]; b = g["teamB"]
        add_game(a["owner"], a["points"], b["owner"], b["points"],
                 g["week"], yr, g.get("playoff", False), g.get("championship", False))
    print(f"  Yahoo {yr}: +{len(all_games)-before} games")

# Sleeper 2024-2025
n2u = {m["user_id"]: m["display_name"] for m in all_mgrs}
for yr in ["2024", "2025"]:
    rrp = DATA / f"rosters_{yr}.json"
    rmp = DATA / f"matchups_{yr}.json"
    if not (rrp.exists() and rmp.exists()):
        print(f"  skip Sleeper {yr} (files not found)")
        continue
    r2u   = {r["roster_id"]: r.get("owner_id") for r in json.loads(rrp.read_text())}
    wks   = defaultdict(list)
    for e in json.loads(rmp.read_text()):
        wks[e.get("week")].append(e)
    before = len(all_games)
    for wk, ents in wks.items():
        pairs = defaultdict(list)
        for me in ents:
            pairs[me.get("matchup_id")].append(me)
        for mid, pr in pairs.items():
            if len(pr) != 2: continue
            ea, eb = pr
            ua = r2u.get(ea["roster_id"]); ub = r2u.get(eb["roster_id"])
            if not ua or not ub: continue
            na = n2u.get(ua); nb = n2u.get(ub)
            if not na or not nb: continue
            pta = float(ea.get("points") or 0)
            ptb = float(eb.get("points") or 0)
            add_game(na, pta, nb, ptb, wk, yr)
    print(f"  Sleeper {yr}: +{len(all_games)-before} games")

print(f"Total games collected: {len(all_games)}")

# ── Build H2H pair summaries ──────────────────────────────────────────────────
def pair_key(x, y): return "|".join(sorted([x, y]))

pair_games = defaultdict(list)
for g in all_games:
    pair_games[pair_key(g["a"], g["b"])].append(g)

pairs_out = {}

for pk, games in pair_games.items():
    if not games: continue
    ma, mb = pk.split("|")          # alphabetically sorted

    wins_a = sum(1 for g in games if g["winner"] == ma)
    wins_b = len(games) - wins_a

    pf_a = 0.0; pf_b = 0.0
    for g in games:
        if g["a"] == ma:
            pf_a += g["pts_a"]; pf_b += g["pts_b"]
        else:
            pf_a += g["pts_b"]; pf_b += g["pts_a"]
    pf_a = round(pf_a, 2); pf_b = round(pf_b, 2)
    n    = len(games)
    ppg_a = round(pf_a / n, 1) if n else 0.0
    ppg_b = round(pf_b / n, 1) if n else 0.0

    biggest = max(games, key=lambda x: x["margin"])
    closest = min(games, key=lambda x: x["margin"])

    def pts_for(g, name):
        return g["pts_a"] if g["a"] == name else g["pts_b"]

    bw = biggest["winner"]
    bl = mb if bw == ma else ma
    biggest_info = {
        "winner":  bw,
        "loser":   bl,
        "score_w": pts_for(biggest, bw),
        "score_l": pts_for(biggest, bl),
        "margin":  biggest["margin"],
        "context": "Week " + str(biggest["week"]) + ", " + biggest["season"],
    }
    cw = closest["winner"]
    closest_info = {
        "winner":  cw,
        "margin":  closest["margin"],
        "context": "Week " + str(closest["week"]) + ", " + closest["season"],
    }

    sorted_games  = sorted(games, key=lambda x: (x["season"], x["week"]))
    streak_holder = sorted_games[-1]["winner"]
    streak_count  = 0
    for g in reversed(sorted_games):
        if g["winner"] == streak_holder: streak_count += 1
        else: break

    seasons_bd = defaultdict(lambda: {"wins_a": 0, "wins_b": 0, "meetings": 0})
    for g in games:
        sy = g["season"]
        seasons_bd[sy]["meetings"] += 1
        if g["winner"] == ma: seasons_bd[sy]["wins_a"] += 1
        else:                  seasons_bd[sy]["wins_b"] += 1

    playoff_games = [g for g in games if g.get("playoff")]
    champ_games   = [g for g in games if g.get("championship")]

    competitiveness = 1.0 - abs(wins_a - wins_b) / max(n, 1)
    rivalry_score = round(
        n * 10 +
        competitiveness * 30 +
        len(playoff_games) * 15 +
        len(champ_games) * 20,
        1
    )

    pairs_out[pk] = {
        "a":                      ma,
        "b":                      mb,
        "wins_a":                 wins_a,
        "wins_b":                 wins_b,
        "pf_a":                   pf_a,
        "pf_b":                   pf_b,
        "ppg_a":                  ppg_a,
        "ppg_b":                  ppg_b,
        "meetings":               n,
        "playoff_meetings":       len(playoff_games),
        "championship_meetings":  len(champ_games),
        "biggest_win":            biggest_info,
        "closest_game":           closest_info,
        "streak":                 {"holder": streak_holder, "count": streak_count},
        "seasons":                {k: dict(v) for k, v in sorted(seasons_bd.items())},
        "rivalry_score":          rivalry_score,
    }

top_rivalries = sorted(pairs_out.values(), key=lambda x: x["rivalry_score"], reverse=True)

output = {
    "generated":        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "total_matchups":   len(all_games),
    "total_pairs":      len(pairs_out),
    "managers":         all_managers_sorted,
    "active_managers":  active_mgrs,
    "former_managers":  former_mgrs,
    "pairs":            pairs_out,
    "top_rivalries":    top_rivalries[:10],
}

out_path = DATA / "rivalries_h2h.json"
out_path.write_text(json.dumps(output, indent=2))
size_kb = out_path.stat().st_size // 1024

print(f"\n✅ rivalries_h2h.json saved ({size_kb} KB)")
print(f"   {len(pairs_out)} H2H pairs computed")
print(f"   {len(all_games)} total matchups processed")
print(f"\nTop 5 Rivalries by score:")
for r in top_rivalries[:5]:
    print(f"  {r['a']} vs {r['b']}: {r['wins_a']}-{r['wins_b']} "
          f"({r['meetings']} meetings, playoff={r['playoff_meetings']}, score={r['rivalry_score']})")

print("\nNext: python3 scripts/patch_rivalries_gen.py && python3 scripts/generate_site.py")
