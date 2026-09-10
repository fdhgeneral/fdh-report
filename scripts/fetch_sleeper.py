#!/usr/bin/env python3
"""
FDH Hall of Fame — Sleeper API Data Fetcher
============================================
Pulls all league data from the Sleeper API and writes structured JSON
to _data/ for the site generator to consume.

Usage:
    python scripts/fetch_sleeper.py

Outputs (all written to _data/):
    league.json         — league metadata
    users.json          — manager roster & display names
    rosters.json        — current rosters
    matchups_<season>.json — weekly matchup scores per season
    trades_<season>.json   — trade history per season
    drafts_<season>.json   — draft picks per season
    stats.json          — computed all-time stats (wins, pct, h2h, etc.)
"""

import json
import time
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# ── Config ─────────────────────────────────────────────────────────────────
LEAGUE_ID   = "1378834732145455104"
BASE_URL    = "https://api.sleeper.app/v1"
DATA_DIR    = Path(__file__).parent.parent / "_data"
LOG_LEVEL   = logging.INFO
RATE_LIMIT  = 0.35          # seconds between requests (Sleeper allows ~1000/min)

# ── Divisions mapping — update as needed ───────────────────────────────────
DIVISION_MAP = {
    # "sleeper_user_id": "FDH North" | "FDH West" | "FDH East"
    # Populated automatically from roster.metadata.division if available,
    # otherwise falls back to this manual map.
}

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("fdh-fetch")


# ── HTTP helpers ────────────────────────────────────────────────────────────

def get(endpoint: str, retries: int = 3) -> dict | list | None:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "FDH-HallOfFame/1.0"})
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            time.sleep(RATE_LIMIT)
            return data
        except HTTPError as e:
            log.warning(f"HTTP {e.code} on {url} (attempt {attempt+1})")
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
        except URLError as e:
            log.warning(f"URL error on {url}: {e.reason} (attempt {attempt+1})")
            time.sleep(2 * (attempt + 1))
    log.error(f"Failed after {retries} attempts: {url}")
    return None


def save(filename: str, data) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log.info(f"Saved {path} ({os.path.getsize(path):,} bytes)")


# ── League discovery ─────────────────────────────────────────────────────────

def fetch_league_chain(league_id: str) -> list[str]:
    """Walk the previous_league_id chain to get all historical league IDs."""
    ids = []
    lid = league_id
    while lid:
        league = get(f"/league/{lid}")
        if not league:
            break
        ids.append(lid)
        lid = league.get("previous_league_id")
    ids.reverse()
    return ids


def fetch_all_seasons(league_ids: list[str]) -> dict:
    """Return {league_id: league_metadata} for all seasons."""
    seasons = {}
    for lid in league_ids:
        data = get(f"/league/{lid}")
        if data:
            seasons[lid] = data
    return seasons


# ── Users & Rosters ──────────────────────────────────────────────────────────

def fetch_users(league_id: str) -> list[dict]:
    return get(f"/league/{league_id}/users") or []


def fetch_rosters(league_id: str) -> list[dict]:
    return get(f"/league/{league_id}/rosters") or []


def build_user_map(all_season_users: dict) -> dict:
    """
    Aggregate users across all seasons.
    Returns {user_id: {display_name, avatar, team_names: [...]}}
    """
    user_map = {}
    for lid, users in all_season_users.items():
        for u in users:
            uid = u["user_id"]
            if uid not in user_map:
                user_map[uid] = {
                    "user_id":      uid,
                    "display_name": u.get("display_name", "Unknown"),
                    "avatar":       u.get("avatar"),
                    "team_names":   [],
                    "metadata":     u.get("metadata", {}),
                }
            team_name = u.get("metadata", {}).get("team_name", "")
            if team_name and team_name not in user_map[uid]["team_names"]:
                user_map[uid]["team_names"].append(team_name)
    return user_map


# ── Matchups ─────────────────────────────────────────────────────────────────

def fetch_matchups(league_id: str, season_type: str, max_weeks: int = 18) -> list[dict]:
    """Fetch all weekly matchups for a league."""
    matchups = []
    for week in range(1, max_weeks + 1):
        data = get(f"/league/{league_id}/matchups/{week}")
        if not data:
            break
        # Check if any team scored (empty weeks return null scores)
        has_scores = any(m.get("points", 0) for m in data)
        if not has_scores:
            break
        for m in data:
            m["week"] = week
            m["league_id"] = league_id
        matchups.extend(data)
    return matchups


# ── Trades ───────────────────────────────────────────────────────────────────

def fetch_transactions(league_id: str, max_rounds: int = 18) -> list[dict]:
    """Fetch all transactions (trades, waivers, FA) for a league."""
    transactions = []
    for week in range(1, max_rounds + 1):
        data = get(f"/league/{league_id}/transactions/{week}")
        if not data:
            break
        for t in data:
            t["week"] = week
            t["league_id"] = league_id
        transactions.extend(data)
    return transactions


# ── Drafts ───────────────────────────────────────────────────────────────────

def fetch_drafts(league_id: str) -> list[dict]:
    drafts = get(f"/league/{league_id}/drafts") or []
    full = []
    for draft in drafts:
        did = draft["draft_id"]
        picks = get(f"/draft/{did}/picks") or []
        full.append({"draft": draft, "picks": picks})
    return full


# ── Stats computation ─────────────────────────────────────────────────────────

def compute_stats(
    all_matchups: dict,      # {league_id: [matchup, ...]}
    all_rosters: dict,       # {league_id: [roster, ...]}
    all_users: dict,         # {league_id: [user, ...]}
    user_map: dict,          # {user_id: {...}}
    seasons_meta: dict,      # {league_id: league_metadata}
) -> dict:
    """
    Build comprehensive all-time stats for every manager.
    Returns a dict ready to be serialised and consumed by the generator.
    """
    # roster_id -> user_id map per league
    roster_to_user = {}
    for lid, rosters in all_rosters.items():
        roster_to_user[lid] = {}
        for r in rosters:
            roster_to_user[lid][r["roster_id"]] = r.get("owner_id")

    # Initialise per-user stats
    stats = {}
    for uid, u in user_map.items():
        stats[uid] = {
            "user_id":       uid,
            "display_name":  u["display_name"],
            "latest_team":   u["team_names"][-1] if u["team_names"] else "",
            "all_team_names":u["team_names"],
            "avatar":        u.get("avatar"),
            "seasons":       0,
            "wins":          0,
            "losses":        0,
            "ties":          0,
            "pf":            0.0,
            "pa":            0.0,
            "playoff_apps":  0,
            "championships": 0,
            "weekly_highs":  [],   # {week, league_id, score}
            "win_streak":    0,
            "lose_streak":   0,
            "max_win_streak":0,
            "max_lose_streak":0,
            "season_records":[],   # [{league_id, season, w, l, t, pf, pa, playoff, champ}]
            "h2h":           {},   # {opponent_uid: {w, l, pf, pa, meetings}}
            "division":      DIVISION_MAP.get(uid, ""),
        }

    # Season-level helper
    seen_seasons = set()

    for lid, matchups in all_matchups.items():
        ru_map = roster_to_user.get(lid, {})
        season_year = seasons_meta.get(lid, {}).get("season", "?")
        playoff_start = seasons_meta.get(lid, {}).get("settings", {}).get("playoff_week_start", 15)

        # Aggregate per-roster weekly results
        roster_week = {}   # {(roster_id, week): {points, matchup_id}}
        for m in matchups:
            key = (m["roster_id"], m["week"])
            roster_week[key] = {"points": m.get("points", 0), "matchup_id": m.get("matchup_id")}

        # Group by week → matchup_id to pair opponents
        week_groups = {}
        for m in matchups:
            wk = m["week"]
            mid = m.get("matchup_id")
            if mid is None:
                continue
            week_groups.setdefault((wk, mid), []).append(m)

        # Track per-roster season aggregates
        roster_season = {}

        for (wk, mid), pair in week_groups.items():
            if len(pair) != 2:
                continue
            a, b = pair
            uid_a = ru_map.get(a["roster_id"])
            uid_b = ru_map.get(b["roster_id"])
            pts_a = a.get("points", 0) or 0
            pts_b = b.get("points", 0) or 0
            is_playoff = wk >= playoff_start

            for uid, pts, opp_uid, opp_pts in [
                (uid_a, pts_a, uid_b, pts_b),
                (uid_b, pts_b, uid_a, pts_a),
            ]:
                if uid not in stats:
                    continue
                s = stats[uid]
                s["pf"] += pts
                s["pa"] += opp_pts

                # Win / Loss
                if pts > opp_pts:
                    s["wins"] += 1
                    s["win_streak"] += 1
                    s["lose_streak"] = 0
                elif pts < opp_pts:
                    s["losses"] += 1
                    s["lose_streak"] += 1
                    s["win_streak"] = 0
                else:
                    s["ties"] += 1
                    s["win_streak"] = 0
                    s["lose_streak"] = 0

                s["max_win_streak"]  = max(s["max_win_streak"],  s["win_streak"])
                s["max_lose_streak"] = max(s["max_lose_streak"], s["lose_streak"])

                # H2H
                if opp_uid and opp_uid in stats:
                    h = s["h2h"].setdefault(opp_uid, {"w": 0, "l": 0, "pf": 0.0, "pa": 0.0, "meetings": 0, "playoff_meetings": 0})
                    h["meetings"] += 1
                    h["pf"] += pts
                    h["pa"] += opp_pts
                    if is_playoff:
                        h["playoff_meetings"] += 1
                    if pts > opp_pts:
                        h["w"] += 1
                    elif pts < opp_pts:
                        h["l"] += 1

                # Roster season tracker
                rst = a["roster_id"] if uid == uid_a else b["roster_id"]
                rs = roster_season.setdefault((uid, rst), {"w": 0, "l": 0, "t": 0, "pf": 0.0, "pa": 0.0})
                if pts > opp_pts:
                    rs["w"] += 1
                elif pts < opp_pts:
                    rs["l"] += 1
                else:
                    rs["t"] += 1
                rs["pf"] += pts
                rs["pa"] += opp_pts

                # Weekly high
                stats[uid]["weekly_highs"].append({"week": wk, "league_id": lid, "score": pts, "season": season_year})

        # Mark seasons for users who appeared in this league's roster map
        for rid, uid in ru_map.items():
            if uid and uid in stats:
                season_key = (uid, lid)
                if season_key not in seen_seasons:
                    seen_seasons.add(season_key)
                    stats[uid]["seasons"] += 1

    # Win percentage
    for uid, s in stats.items():
        total = s["wins"] + s["losses"] + s["ties"]
        s["win_pct"] = round(s["wins"] / total, 4) if total else 0.0
        s["pf"]      = round(s["pf"], 2)
        s["pa"]      = round(s["pa"], 2)

        # GOAT score (0-100)
        win_pts   = s["win_pct"] * 35
        title_pts = min(s["championships"] * 10, 30)
        total_games = s["wins"] + s["losses"] + s["ties"]
        playoff_pct = s["playoff_apps"] / max(s["seasons"], 1)
        playoff_pts = playoff_pct * 20
        # PF percentile done after all managers computed
        s["goat_raw"] = {"win": win_pts, "title": title_pts, "playoff": playoff_pts}

    # PF percentile component
    pf_vals = [s["pf"] for s in stats.values() if s["seasons"] > 0]
    if pf_vals:
        pf_min, pf_max = min(pf_vals), max(pf_vals)
        for uid, s in stats.items():
            pct = (s["pf"] - pf_min) / (pf_max - pf_min) if pf_max > pf_min else 0
            s["goat_raw"]["pf"] = round(pct * 15, 2)
            s["goat_score"] = round(
                s["goat_raw"]["win"] + s["goat_raw"]["title"] +
                s["goat_raw"]["playoff"] + s["goat_raw"]["pf"], 2
            )

    # Sort H2H into rivalry list
    rivalries = []
    seen_pairs = set()
    for uid_a, s in stats.items():
        for uid_b, h in s["h2h"].items():
            if uid_b not in stats:
                continue
            pair = tuple(sorted([uid_a, uid_b]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            h_b = stats[uid_b]["h2h"].get(uid_a, {"w": 0, "l": 0, "meetings": 0, "playoff_meetings": 0, "pf": 0, "pa": 0})
            total_meetings = h["meetings"]
            if total_meetings < 2:
                continue
            win_diff = abs(h["w"] - h["l"])
            closeness = 1 - (win_diff / total_meetings)
            rivalry_score = round(total_meetings * 2 + closeness * 10 + h["playoff_meetings"] * 5, 2)
            rivalries.append({
                "manager_a":       uid_a,
                "name_a":          stats[uid_a]["display_name"],
                "manager_b":       uid_b,
                "name_b":          stats[uid_b]["display_name"],
                "wins_a":          h["w"],
                "wins_b":          h_b["w"],
                "total_meetings":  total_meetings,
                "playoff_meetings":h["playoff_meetings"],
                "rivalry_score":   rivalry_score,
                "pf_a":            round(h["pf"], 2),
                "pf_b":            round(h_b["pf"], 2),
            })
    rivalries.sort(key=lambda x: x["rivalry_score"], reverse=True)

    return {
        "managers":       list(stats.values()),
        "rivalries":      rivalries,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    log.info("=== FDH Sleeper Fetcher ===")
    log.info(f"League ID: {LEAGUE_ID}")

    # 1. Discover all historical league IDs
    log.info("Discovering league chain...")
    league_ids = fetch_league_chain(LEAGUE_ID)
    log.info(f"Found {len(league_ids)} seasons: {league_ids}")

    seasons_meta = fetch_all_seasons(league_ids)
    save("league.json", seasons_meta)

    # 2. Per-season data
    all_users    = {}
    all_rosters  = {}
    all_matchups = {}
    all_trades   = {}
    all_drafts   = {}

    for lid in league_ids:
        meta = seasons_meta.get(lid, {})
        season = meta.get("season", lid)
        status = meta.get("status", "unknown")
        log.info(f"  Season {season} ({lid}) — status: {status}")

        users   = fetch_users(lid)
        rosters = fetch_rosters(lid)
        all_users[lid]   = users
        all_rosters[lid] = rosters

        if status in ("complete", "in_season"):
            matchups = fetch_matchups(lid, meta.get("season_type", "regular"))
            all_matchups[lid] = matchups
            save(f"matchups_{season}.json", matchups)

            txns = fetch_transactions(lid)
            trades = [t for t in txns if t.get("type") == "trade"]
            all_trades[lid] = trades
            save(f"trades_{season}.json", trades)

        drafts = fetch_drafts(lid)
        all_drafts[lid] = drafts
        save(f"drafts_{season}.json", drafts)

        save(f"users_{season}.json", users)
        save(f"rosters_{season}.json", rosters)

    # 3. Build consolidated user map
    user_map = build_user_map(all_users)
    save("users.json", user_map)

    # 4. Compute all-time stats
    log.info("Computing all-time stats...")
    stats = compute_stats(all_matchups, all_rosters, all_users, user_map, seasons_meta)
    save("stats.json", stats)

    log.info("=== Fetch complete ===")
    log.info(f"Generated at: {stats['generated_at']}")


if __name__ == "__main__":
    main()
