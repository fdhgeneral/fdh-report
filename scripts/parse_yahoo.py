#!/usr/bin/env python3
"""
parse_yahoo.py — Convert Yahoo Fantasy Hall of Fame export into FDH _data format.
"""
import json, sys
from pathlib import Path
from collections import defaultdict

ROOT  = Path(__file__).parent.parent
DATA  = ROOT / "_data"
SRC   = DATA / "yahoo_history.json"
YAHOO_SEASONS = {"2020", "2021", "2022", "2023"}

def load():
    if not SRC.exists():
        sys.exit(f"ERROR: {SRC} not found. Run: git pull")
    return json.loads(SRC.read_text())

def save(path, data):
    path.write_text(json.dumps(data, indent=2))
    print(f"  ✓ {path.name}")

def parse_matchups(raw):
    by_season = defaultdict(list)
    for m in raw.get("matchups", []):
        season = m["season"]
        if season not in YAHOO_SEASONS or m.get("status") != "postevent":
            continue
        a, b = m["teamA"], m["teamB"]
        winner = a["owner"] if m.get("winnerTeamId") == a["teamId"] else b["owner"]
        by_season[season].append({
            "week":         m["week"],
            "playoff":      m.get("playoffs", False),
            "consolation":  m.get("consolation", False),
            "championship": m.get("championship", False),
            "teamA":        {"owner": a["owner"], "team": a["team"], "points": a["points"]},
            "teamB":        {"owner": b["owner"], "team": b["team"], "points": b["points"]},
            "winner":       winner,
            "margin":       round(abs(a["points"] - b["points"]), 2),
        })
    print("\n── Matchups ──")
    for season in sorted(YAHOO_SEASONS):
        games = sorted(by_season[season], key=lambda x: x["week"])
        save(DATA / f"yahoo_matchups_{season}.json", games)
        reg  = sum(1 for g in games if not g["playoff"] and not g["consolation"])
        play = sum(1 for g in games if g["playoff"])
        print(f"     {season}: {reg} regular + {play} playoff games")

def parse_standings(raw):
    print("\n── Standings ──")
    for s in raw.get("seasons", []):
        season = s["season"]
        if season not in YAHOO_SEASONS:
            continue
        rows = s.get("finalStandings", [])
        save(DATA / f"yahoo_standings_{season}.json", rows)
        print(f"     {season}: {len(rows)} teams")

def parse_trades(raw):
    by_season = defaultdict(list)
    for t in raw.get("transactions", []):
        if t.get("type") != "trade" or t.get("status") != "successful":
            continue
        season = t["season"]
        if season not in YAHOO_SEASONS:
            continue
        parties = [p.get("owner", str(p)) if isinstance(p, dict) else str(p) for p in t.get("parties", [])]
        players = [{"player": p.get("name", p.get("playerKey", "")), "to": p.get("destinationOwner", "")} for p in t.get("players", []) if isinstance(p, dict)]
        by_season[season].append({"id": t["id"], "week": t.get("week"), "timestamp": t.get("timestamp"), "parties": parties, "players": players})
    print("\n── Trades ──")
    for season in sorted(YAHOO_SEASONS):
        trades = by_season.get(season, [])
        save(DATA / f"yahoo_trades_{season}.json", trades)
        print(f"     {season}: {len(trades)} trades")

def parse_drafts(raw):
    print("\n── Drafts ──")
    for draft in raw.get("drafts", []):
        season = draft["season"]
        if season not in YAHOO_SEASONS:
            continue
        picks = draft.get("picks", [])
        out = {
            "season": season, "type": draft.get("type", "snake"),
            "rounds": draft.get("rounds"), "teams": draft.get("teams"),
            "picks": [{"round": p["round"], "pick": p["roundPick"], "overall": p["overall"],
                       "owner": p["owner"], "team": p["team"], "player": p.get("player"),
                       "position": p.get("position"), "keeper": p.get("keeper", False),
                       "traded": p.get("traded", False)} for p in picks]
        }
        save(DATA / f"yahoo_drafts_{season}.json", out)
        keepers = sum(1 for p in picks if p.get("keeper"))
        print(f"     {season}: {len(picks)} picks ({keepers} keepers)")

def parse_champions(raw):
    print("\n── Champions ──")
    champs = []
    for c in sorted(raw.get("champions", []), key=lambda x: x["season"]):
        champs.append({"season": c["season"], "owner": c["owner"], "team": c["team"],
                       "points": c["points"], "runner_up": c["runnerUp"]["owner"],
                       "ru_team": c["runnerUp"]["team"], "ru_points": c["runnerUp"]["points"],
                       "margin": c["margin"], "week": c.get("finalsWeek")})
        print(f"     {c['season']}: {c['owner']}  ({c['points']} pts, +{c['margin']} margin)")
    save(DATA / "yahoo_champions.json", champs)

def patch_stats(raw):
    print("\n── Patching stats.json ──")
    stats_path = DATA / "stats.json"
    stats = json.loads(stats_path.read_text())
    ats = {row["owner"]: row for row in raw.get("allTimeStandings", [])}
    updated = 0
    for m in stats.get("managers", []):
        name = m.get("display_name", "")
        if name not in ats:
            continue
        y = ats[name]
        m["total_wins"]    = y["wins"]
        m["total_losses"]  = y["losses"]
        m["total_pf"]      = round(y["pointsFor"], 2)
        m["total_pa"]      = round(y["pointsAgainst"], 2)
        m["win_pct"]       = round(y["winPct"], 4)
        m["championships"] = y["championships"]
        m["runner_ups"]    = y.get("runnerUps", 0)
        m["seasons"]       = y["seasons"]
        updated += 1
        flag = f"  {y['championships']} champ(s)" if y["championships"] else ""
        print(f"     {name}: {y['wins']}W-{y['losses']}L  PF={y['pointsFor']:.1f}{flag}")
    existing = {m.get("display_name") for m in stats.get("managers", [])}
    added = 0
    for name, y in ats.items():
        if name in existing or y.get("hidden", False):
            continue
        stats["managers"].append({
            "display_name": name, "user_id": y.get("ownerId", ""),
            "total_wins": y["wins"], "total_losses": y["losses"],
            "total_pf": round(y["pointsFor"], 2), "total_pa": round(y["pointsAgainst"], 2),
            "win_pct": round(y["winPct"], 4), "championships": y["championships"],
            "runner_ups": y.get("runnerUps", 0), "seasons": y["seasons"], "yahoo_only": True,
        })
        added += 1
        print(f"     + Former member added: {name}")
    stats_path.write_text(json.dumps(stats, indent=2))
    print(f"\n  ✓ stats.json  ({updated} enriched, {added} former members added)")

def main():
    print("=== parse_yahoo.py — FDH League History Import ===\n")
    raw    = load()
    counts = raw.get("counts", {})
    print(f"Source: {counts.get('seasons')} seasons | {counts.get('matchups')} matchups | {counts.get('transactions')} transactions | {counts.get('drafts')} drafts")
    parse_matchups(raw)
    parse_standings(raw)
    parse_trades(raw)
    parse_drafts(raw)
    parse_champions(raw)
    patch_stats(raw)
    print("\n✅ Yahoo import complete. Run generate_site.py next.")

if __name__ == "__main__":
    main()
