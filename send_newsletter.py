#!/usr/bin/env python3
"""
FDH Newsletter Engine — send_newsletter.py
Live Sleeper integration: real team names, scores, streaks, dynamic week.
Theme: FDH Red (#C8102E) + Slate (#1E2A38)
"""

from __future__ import annotations

import os
import random
import smtplib
import textwrap
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import requests

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
# Your Sleeper league — hardcoded so you never have to set an env var
LEAGUE_ID: str = os.getenv("SLEEPER_LEAGUE_ID", "1378834732145455104")

# Set FDH_TEST_MODE=false in your terminal to send live data
TEST_MODE: bool = os.getenv("FDH_TEST_MODE", "true").lower() in ("1", "true", "yes")

# Override week manually if needed; 0 = auto-detect from Sleeper
MANUAL_WEEK: int = int(os.getenv("FDH_WEEK", "0"))
SEASON:      str = os.getenv("FDH_SEASON", "2026")

# SMTP / Gmail settings
SMTP_HOST:    str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT:    int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER:    str = os.getenv("SMTP_USER", "")
SMTP_PASS:    str = os.getenv("SMTP_PASS", "")
FROM_ADDRESS: str = os.getenv("FDH_FROM", SMTP_USER)
REPLY_TO:     str = os.getenv("FDH_REPLY_TO", FROM_ADDRESS)

RECIPIENTS: list[str] = [
    addr.strip()
    for addr in os.getenv("FDH_RECIPIENTS", "").split(",")
    if addr.strip()
]

# ─────────────────────────────────────────────
# THEME
# ─────────────────────────────────────────────
THEME = {
    "red":         "#C8102E",
    "red_dark":    "#9B0C23",
    "slate":       "#1E2A38",
    "slate_mid":   "#2C3E50",
    "slate_light": "#3D5166",
    "gold":        "#F4C542",
    "silver":      "#A8AAAD",
    "bronze":      "#CD7F32",
    "green":       "#27AE60",
    "danger":      "#E74C3C",
    "white":       "#FFFFFF",
    "off_white":   "#F5F6FA",
    "text_dark":   "#1A1A2E",
    "text_muted":  "#6C757D",
    "card_bg":     "#FFFFFF",
    "border":      "#E0E4EB",
}

SECTION_AWARDS    = "This Week's Legends & Letdowns"
SECTION_STANDINGS = "Where Everyone Sits"
SECTION_HEATCHECK = "FDH Heat Check"
LOGO_TEXT         = "FDH"

# ─────────────────────────────────────────────
# STUB DATA (TEST_MODE only)
# ─────────────────────────────────────────────
STUB_MANAGERS: list[dict[str, Any]] = [
    {"name": "Gridiron Goat",   "record": (7, 2), "pts_for": 1342.8, "pts_against": 1198.4, "streak": "W3"},
    {"name": "Blitz Kingdom",   "record": (6, 3), "pts_for": 1289.6, "pts_against": 1211.0, "streak": "W1"},
    {"name": "Turf Titans",     "record": (6, 3), "pts_for": 1271.2, "pts_against": 1240.8, "streak": "L1"},
    {"name": "End Zone Elites", "record": (5, 4), "pts_for": 1255.4, "pts_against": 1263.6, "streak": "W2"},
    {"name": "Pocket Passers",  "record": (5, 4), "pts_for": 1230.0, "pts_against": 1258.2, "streak": "L2"},
    {"name": "Red Zone Rebels", "record": (4, 5), "pts_for": 1188.6, "pts_against": 1244.4, "streak": "W1"},
    {"name": "Salary Cap Sins", "record": (4, 5), "pts_for": 1176.2, "pts_against": 1233.8, "streak": "L3"},
    {"name": "Waiver Wire Wiz", "record": (3, 6), "pts_for": 1144.4, "pts_against": 1301.0, "streak": "L1"},
    {"name": "Bench Warmers",   "record": (3, 6), "pts_for": 1122.8, "pts_against": 1285.4, "streak": "W1"},
    {"name": "Dead Cap Dave",   "record": (2, 7), "pts_for": 1088.6, "pts_against": 1312.2, "streak": "L4"},
]

STUB_MATCHUPS: list[dict[str, Any]] = [
    {"home": "Gridiron Goat",   "away": "Dead Cap Dave",   "home_pts": 148.6, "away_pts": 92.2},
    {"home": "Blitz Kingdom",   "away": "Bench Warmers",   "home_pts": 134.4, "away_pts": 118.8},
    {"home": "Turf Titans",     "away": "Waiver Wire Wiz", "home_pts": 122.0, "away_pts": 143.6},
    {"home": "End Zone Elites", "away": "Salary Cap Sins", "home_pts": 139.2, "away_pts": 101.4},
    {"home": "Pocket Passers",  "away": "Red Zone Rebels", "home_pts": 116.8, "away_pts": 127.4},
]

# ─────────────────────────────────────────────
# SLEEPER API HELPERS
# ─────────────────────────────────────────────
SLEEPER_BASE = "https://api.sleeper.app/v1"


def _get(url: str, timeout: int = 10) -> Any:
    """Fetch a Sleeper API endpoint; returns None on any failure."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        print(f"[WARN] API fetch failed → {url}\n       {exc}")
        return None


def auto_detect_week() -> int:
    """
    Read the current week from Sleeper's league endpoint (settings.leg).
    Falls back to MANUAL_WEEK or 1 if API is unavailable.
    """
    if MANUAL_WEEK > 0:
        print(f"[INFO] Using manually set week: {MANUAL_WEEK}")
        return MANUAL_WEEK
    data = _get(f"{SLEEPER_BASE}/league/{LEAGUE_ID}")
    if data:
        week = data.get("settings", {}).get("leg", 1)
        print(f"[INFO] Auto-detected week from Sleeper: {week}")
        return int(week)
    print("[WARN] Could not detect week from Sleeper — defaulting to 1")
    return 1


def fetch_league_users() -> dict[str, dict]:
    """
    Returns {user_id: {"display": str, "team": str, "label": str}}
    Team name priority: metadata.team_name > display_name
    """
    data = _get(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/users")
    if not data:
        return {}
    result = {}
    for u in data:
        uid   = u.get("user_id", "")
        disp  = u.get("display_name", f"User_{uid[-4:]}")
        team  = (u.get("metadata") or {}).get("team_name", "").strip()
        label = team if team else disp
        result[uid] = {"display": disp, "team": team, "label": label}
    return result


def fetch_rosters() -> list[dict]:
    data = _get(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/rosters")
    return data or []


def fetch_week_matchups(week: int) -> list[dict]:
    data = _get(f"{SLEEPER_BASE}/league/{LEAGUE_ID}/matchups/{week}")
    return data or []


def _pair_matchups(raw: list[dict]) -> list[tuple[dict, dict]]:
    """Group raw Sleeper matchup entries into (home, away) pairs."""
    by_mid: dict[int, list[dict]] = {}
    for m in raw:
        mid = m.get("matchup_id")
        if mid is not None:
            by_mid.setdefault(mid, []).append(m)
    pairs = []
    for mid, group in sorted(by_mid.items()):
        if len(group) == 2:
            pairs.append((group[0], group[1]))
    return pairs


def compute_streaks(week: int) -> dict[int, str]:
    """
    Fetch matchup results for all completed weeks (1 → week).
    Returns {roster_id: "W2" | "L3" | "—"}.
    Week N is only included if both teams have scored > 0
    (guards against in-progress weeks showing partial data).
    """
    history: dict[int, list[str]] = {}  # roster_id → ["W","L","W",...]

    for w in range(1, week + 1):
        raw = fetch_week_matchups(w)
        if not raw:
            continue
        for a, b in _pair_matchups(raw):
            pts_a = float(a.get("points") or 0)
            pts_b = float(b.get("points") or 0)
            # Skip if week isn't scored yet
            if pts_a == 0 and pts_b == 0:
                continue
            rid_a = a["roster_id"]
            rid_b = b["roster_id"]
            history.setdefault(rid_a, [])
            history.setdefault(rid_b, [])
            if pts_a > pts_b:
                history[rid_a].append("W")
                history[rid_b].append("L")
            elif pts_b > pts_a:
                history[rid_b].append("W")
                history[rid_a].append("L")
            else:
                history[rid_a].append("T")
                history[rid_b].append("T")

    streaks: dict[int, str] = {}
    for rid, results in history.items():
        if not results:
            streaks[rid] = "—"
            continue
        last  = results[-1]
        count = sum(1 for _ in iter(lambda: results.pop() == last if results else False, False))
        # Recalculate properly
        count = 0
        for r in reversed(results):
            if r == last:
                count += 1
            else:
                break
        streaks[rid] = f"{last}{count}"

    return streaks


def build_managers_from_api(week: int) -> list[dict[str, Any]]:
    """
    Pull live team names, records, and points from Sleeper.
    Calculates current streaks from matchup history.
    Falls back to stub data if the API is unavailable.
    """
    users   = fetch_league_users()
    rosters = fetch_rosters()

    if not users or not rosters:
        print("[INFO] Falling back to stub managers (API unavailable).")
        return STUB_MANAGERS

    print(f"[INFO] Fetched {len(users)} users and {len(rosters)} rosters from Sleeper.")
    streaks = compute_streaks(week)

    managers: list[dict[str, Any]] = []
    for r in rosters:
        rid = r.get("roster_id")
        uid = r.get("owner_id", "")
        s   = r.get("settings") or {}

        # Team name: custom team name → Sleeper display name → fallback
        name = users.get(uid, {}).get("label") or f"Team {rid}"

        wins   = s.get("wins", 0)
        losses = s.get("losses", 0)
        ties   = s.get("ties", 0)

        # Sleeper stores points split across two fields
        pts_for     = round(s.get("fpts", 0) + s.get("fpts_decimal", 0) / 100, 2)
        pts_against = round(s.get("fpts_against", 0) + s.get("fpts_against_decimal", 0) / 100, 2)

        streak = streaks.get(rid, "—")

        managers.append({
            "name":        name,
            "record":      (wins, losses),
            "ties":        ties,
            "pts_for":     pts_for,
            "pts_against": pts_against,
            "streak":      streak,
            "roster_id":   rid,
        })

    return managers


def build_matchups_from_api(week: int, managers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Pull live week matchups and resolve roster IDs to real team names.
    Falls back to stub matchups if unavailable.
    """
    raw = fetch_week_matchups(week)
    if not raw:
        print("[INFO] Falling back to stub matchups (API unavailable).")
        return STUB_MATCHUPS

    # Build a quick roster_id → name lookup from the already-fetched managers list
    rid_to_name = {m["roster_id"]: m["name"] for m in managers if "roster_id" in m}

    matchups: list[dict[str, Any]] = []
    for a, b in _pair_matchups(raw):
        name_a = rid_to_name.get(a["roster_id"], f"Team {a['roster_id']}")
        name_b = rid_to_name.get(b["roster_id"], f"Team {b['roster_id']}")
        pts_a  = float(a.get("points") or 0)
        pts_b  = float(b.get("points") or 0)
        matchups.append({
            "home":      name_a,
            "away":      name_b,
            "home_pts":  pts_a,
            "away_pts":  pts_b,
        })

    return matchups


# ─────────────────────────────────────────────
# HYBRID POWER RANKINGS
# ─────────────────────────────────────────────
def compute_power_rankings(managers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """60 % win-pct + 40 % points-for percentile → hybrid score."""
    max_pts   = max((m["pts_for"] for m in managers), default=1.0) or 1.0
    min_pts   = min((m["pts_for"] for m in managers), default=0.0)
    pts_range = max_pts - min_pts or 1.0

    for m in managers:
        wins, losses = m["record"]
        gp      = wins + losses or 1
        win_pct = wins / gp
        pts_pct = (m["pts_for"] - min_pts) / pts_range
        m["pr_score"] = round(0.60 * win_pct * 100 + 0.40 * pts_pct * 100, 1)

    ranked = sorted(managers, key=lambda x: x["pr_score"], reverse=True)

    for i, m in enumerate(ranked):
        m["rank"] = i + 1
        streak = m.get("streak", "—")
        try:
            streak_num = int(streak[1:]) if len(streak) > 1 else 1
        except ValueError:
            streak_num = 1
        if streak.startswith("W") and streak_num >= 2:
            m["trend"] = "📈"
        elif streak.startswith("L") and streak_num >= 2:
            m["trend"] = "📉"
        elif m["pr_score"] >= 75:
            m["trend"] = "🔥"
        else:
            m["trend"] = "➡️"

    return ranked


# ─────────────────────────────────────────────
# GOTW
# ─────────────────────────────────────────────
def pick_gotw(matchups: list[dict[str, Any]]) -> dict[str, Any]:
    if not matchups:
        return {"home": "TBD", "away": "TBD", "home_pts": 0.0, "away_pts": 0.0}
    if TEST_MODE:
        return random.choice(matchups)
    # Live mode: closest margin = most dramatic game
    return min(matchups, key=lambda m: abs(m["home_pts"] - m["away_pts"]))


# ─────────────────────────────────────────────
# AWARDS
# ─────────────────────────────────────────────
def compute_awards(managers: list[dict[str, Any]], matchups: list[dict[str, Any]]) -> dict[str, Any]:
    all_scores: list[tuple[str, float]] = []
    for m in matchups:
        all_scores.append((m["home"], m["home_pts"]))
        all_scores.append((m["away"], m["away_pts"]))

    if not all_scores:
        return {
            "legend":  {"name": "—", "pts": 0.0, "blurb": "No data yet."},
            "letdown": {"name": "—", "pts": 0.0, "blurb": "No data yet."},
            "closest": {"teams": "—", "margin": 0.0},
            "blowout": {"teams": "—", "margin": 0.0},
        }

    top_scorer = max(all_scores, key=lambda x: x[1])
    low_scorer = min(all_scores, key=lambda x: x[1])

    margins = [
        (f"{m['home']} vs {m['away']}", abs(m["home_pts"] - m["away_pts"]))
        for m in matchups
    ]
    closest = min(margins, key=lambda x: x[1])
    blowout = max(margins, key=lambda x: x[1])

    legend_blurbs = [
        "Absolutely cooked this week. Untouchable.",
        "Put the league on notice. Numbers don't lie.",
        "The ceiling has been raised. What a performance.",
        "Scoreboard went brrr. The rest of the league watched.",
    ]
    letdown_blurbs = [
        "The roster had other plans. Rough one, chief.",
        "Left points on the bench and takes on the field.",
        "Somewhere, a waiver wire is crying for you.",
        "It's giving 'I benched the wrong guy' energy.",
    ]

    return {
        "legend":  {"name": top_scorer[0], "pts": top_scorer[1], "blurb": random.choice(legend_blurbs)},
        "letdown": {"name": low_scorer[0], "pts": low_scorer[1], "blurb": random.choice(letdown_blurbs)},
        "closest": {"teams": closest[0], "margin": round(closest[1], 2)},
        "blowout": {"teams": blowout[0], "margin": round(blowout[1], 2)},
    }


# ─────────────────────────────────────────────
# HYPE INTROS
# ─────────────────────────────────────────────
HYPE_INTROS: list[str] = [
    "The dust has settled, the trash talk is archived, and the standings don't lie. "
    "Welcome back to the only fantasy football newsletter that hits harder than a Derrick Henry stiff-arm.",
    "Another week in the books. Another week of questionable lineup decisions, kamikaze waiver moves, "
    "and championship dreams hanging by a thread. This is FDH — and we document it all.",
    "Wins were earned. Losses were painful. Excuses were plentiful. "
    "Here's the unfiltered breakdown of Week {week} in all its chaotic glory.",
    "The scoreboard has spoken and it had a lot to say. Buckle up — it's time for the FDH Week {week} "
    "debrief. No feelings were spared in the making of this newsletter.",
    "Your roster either came through or it didn't. Either way, you're reading this, so let's get into it. "
    "FDH Week {week} — the good, the bad, and the ugly.",
]


def pick_intro(week: int) -> str:
    return random.choice(HYPE_INTROS).format(week=week)


# ─────────────────────────────────────────────
# HTML SECTION RENDERERS
# ─────────────────────────────────────────────

def _section_header(title: str, subtitle: str = "") -> str:
    sub = (
        f'<p style="margin:6px 0 0;font-size:17px;color:{THEME["text_muted"]};'
        f'letter-spacing:0.5px;">{subtitle}</p>'
        if subtitle else ""
    )
    return (
        f'<div style="border-left:5px solid {THEME["red"]};padding:10px 0 10px 18px;margin:0 0 28px;">'
        f'<h2 style="margin:0;font-size:22px;font-weight:800;color:{THEME["slate"]};'
        f'letter-spacing:-0.3px;text-transform:uppercase;">{title}</h2>{sub}</div>'
    )


def render_intro(week: int, gotw: dict[str, Any]) -> str:
    intro_text = pick_intro(week)
    winner     = gotw["home"] if gotw["home_pts"] >= gotw["away_pts"] else gotw["away"]
    loser      = gotw["away"] if gotw["home_pts"] >= gotw["away_pts"] else gotw["home"]
    winner_pts = max(gotw["home_pts"], gotw["away_pts"])
    loser_pts  = min(gotw["home_pts"], gotw["away_pts"])
    margin     = round(winner_pts - loser_pts, 2)

    # In-progress games show 0.00 — handle gracefully
    gotw_line = (
        f"{winner_pts:.2f} – {loser_pts:.2f} &nbsp;|&nbsp; Won by {margin:.2f} pts"
        if winner_pts > 0
        else "Game in progress — check back later"
    )

    return f"""
    <div style="background:linear-gradient(135deg,{THEME['slate']} 0%,{THEME['slate_mid']} 100%);
                border-radius:14px;padding:36px 32px;margin-bottom:32px;position:relative;overflow:hidden;">
      <div style="position:absolute;top:-20px;right:-20px;width:140px;height:140px;
                  border-radius:50%;background:{THEME['red']};opacity:0.12;"></div>
      <div style="position:absolute;bottom:-30px;left:-30px;width:180px;height:180px;
                  border-radius:50%;background:{THEME['red']};opacity:0.08;"></div>
      <p style="margin:0 0 8px;font-size:19px;font-weight:700;letter-spacing:2px;
                color:{THEME['red']};text-transform:uppercase;">Week {week} · {SEASON} Season</p>
      <p style="margin:0 0 24px;font-size:19px;color:rgba(255,255,255,0.80);line-height:1.7;">{intro_text}</p>
      <div style="background:rgba(200,16,46,0.18);border:1px solid rgba(200,16,46,0.40);
                  border-radius:10px;padding:16px 20px;box-sizing:border-box;">
        <p style="margin:0 0 4px;font-size:22px;font-weight:700;letter-spacing:2px;
                  color:{THEME['gold']};text-transform:uppercase;">🏆 Game of the Week</p>
        <p style="margin:0;font-size:20px;font-weight:800;color:{THEME['white']};">
          {winner} <span style="color:{THEME['red']};">def.</span> {loser}
        </p>
        <p style="margin:4px 0 0;font-size:17px;color:rgba(255,255,255,0.65);">{gotw_line}</p>
      </div>
    </div>"""


def render_awards(awards: dict[str, Any]) -> str:
    legend  = awards["legend"]
    letdown = awards["letdown"]
    closest = awards["closest"]
    blowout = awards["blowout"]

    def award_card(emoji, label, name, pts, blurb, accent) -> str:
        pts_str = f"{pts:.2f}" if pts > 0 else "—"
        return (
            f'<div style="background:{THEME["card_bg"]};border-radius:12px;border:1px solid {THEME["border"]};'
            f'padding:22px 24px;flex:1;min-width:220px;box-sizing:border-box;border-top:4px solid {accent};">'
            f'<p style="margin:0 0 6px;font-size:22px;font-weight:700;letter-spacing:2px;'
            f'color:{accent};text-transform:uppercase;">{emoji} {label}</p>'
            f'<p style="margin:0 0 4px;font-size:22px;font-weight:800;color:{THEME["text_dark"]};line-height:1.2;">{name}</p>'
            f'<p style="margin:0 0 10px;font-size:24px;font-weight:900;color:{accent};">{pts_str} '
            f'<span style="font-size:17px;font-weight:500;color:{THEME["text_muted"]};">pts</span></p>'
            f'<p style="margin:0;font-size:17px;color:{THEME["text_muted"]};line-height:1.5;font-style:italic;">"{blurb}"</p>'
            f'</div>'
        )

    def stat_card(emoji, label, teams, margin, accent) -> str:
        margin_str = f"±{margin:.2f}" if margin > 0 else "—"
        return (
            f'<div style="background:{THEME["card_bg"]};border-radius:12px;border:1px solid {THEME["border"]};'
            f'padding:22px 24px;flex:1;min-width:220px;box-sizing:border-box;">'
            f'<p style="margin:0 0 6px;font-size:22px;font-weight:700;letter-spacing:2px;'
            f'color:{accent};text-transform:uppercase;">{emoji} {label}</p>'
            f'<p style="margin:0 0 6px;font-size:19px;font-weight:700;color:{THEME["text_dark"]};line-height:1.3;">{teams}</p>'
            f'<p style="margin:0;font-size:22px;font-weight:900;color:{accent};">{margin_str} '
            f'<span style="font-size:17px;font-weight:500;color:{THEME["text_muted"]};">margin</span></p>'
            f'</div>'
        )

    return f"""
    <div style="margin-bottom:40px;">
      {_section_header(SECTION_AWARDS, "Weekly hardware — earned and embarrassing.")}
      <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px;">
        {award_card("👑", "Legend of the Week", legend["name"], legend["pts"], legend["blurb"], THEME["gold"])}
        {award_card("💀", "Letdown of the Week", letdown["name"], letdown["pts"], letdown["blurb"], THEME["danger"])}
      </div>
      <div style="display:flex;gap:16px;flex-wrap:wrap;">
        {stat_card("⚡", "Closest Match", closest["teams"], closest["margin"], THEME["slate_mid"])}
        {stat_card("💣", "Biggest Blowout", blowout["teams"], blowout["margin"], THEME["red"])}
      </div>
    </div>"""


def render_standings(managers: list[dict[str, Any]]) -> str:
    sorted_mgrs = sorted(managers, key=lambda m: (m["record"][0], m["pts_for"]), reverse=True)

    def place_bg(i: int) -> tuple[str, str]:
        if i == 0: return THEME["gold"],        THEME["text_dark"]
        if i == 1: return THEME["silver"],      THEME["text_dark"]
        if i == 2: return THEME["bronze"],      THEME["white"]
        return THEME["slate_light"], THEME["white"]

    rows = ""
    for i, m in enumerate(sorted_mgrs):
        w, l     = m["record"]
        ties_str = f"-{m.get('ties', 0)}" if m.get("ties", 0) else ""
        record   = f"{w}-{l}{ties_str}"
        streak   = m.get("streak", "—")
        s_color  = (
            THEME["green"]   if streak.startswith("W") else
            THEME["danger"]  if streak.startswith("L") else
            THEME["text_muted"]
        )
        bg, fg = place_bg(i)
        cut    = f'border-top:2px dashed {THEME["red"]};' if i == 6 else ""
        alt_bg = f'background:#F9FAFB;' if i % 2 == 1 else ""
        rows += (
            f'<tr style="{cut}{alt_bg}">'
            f'<td style="padding:12px 14px;vertical-align:middle;">'
            f'<span style="display:inline-flex;align-items:center;justify-content:center;'
            f'width:28px;height:28px;border-radius:6px;font-size:20px;font-weight:800;'
            f'background:{bg};color:{fg};">{i+1}</span></td>'
            f'<td style="padding:12px 8px;font-size:22px;font-weight:700;color:{THEME["text_dark"]};vertical-align:middle;">{m["name"]}</td>'
            f'<td style="padding:12px 8px;font-size:22px;font-weight:600;color:{THEME["slate_mid"]};text-align:center;vertical-align:middle;">{record}</td>'
            f'<td style="padding:12px 8px;font-size:17px;color:{THEME["text_muted"]};text-align:right;vertical-align:middle;">{m["pts_for"]:.1f}</td>'
            f'<td style="padding:12px 14px;text-align:right;vertical-align:middle;">'
            f'<span style="font-size:20px;font-weight:700;color:{s_color};">{streak}</span></td>'
            f'</tr>'
        )

    return f"""
    <div style="margin-bottom:40px;">
      {_section_header(SECTION_STANDINGS, "The table of truth. No revisionist history here.")}
      <div style="background:{THEME['card_bg']};border-radius:12px;border:1px solid {THEME['border']};overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;font-family:inherit;">
          <thead>
            <tr style="background:{THEME['slate']};color:{THEME['white']};">
              <th style="padding:12px 14px;font-size:19px;font-weight:700;letter-spacing:1px;text-align:left;text-transform:uppercase;">#</th>
              <th style="padding:12px 8px;font-size:19px;font-weight:700;letter-spacing:1px;text-align:left;text-transform:uppercase;">Team</th>
              <th style="padding:12px 8px;font-size:19px;font-weight:700;letter-spacing:1px;text-align:center;text-transform:uppercase;">W-L</th>
              <th style="padding:12px 8px;font-size:19px;font-weight:700;letter-spacing:1px;text-align:right;text-transform:uppercase;">PF</th>
              <th style="padding:12px 14px;font-size:19px;font-weight:700;letter-spacing:1px;text-align:right;text-transform:uppercase;">Streak</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
        <div style="padding:10px 18px;background:{THEME['off_white']};border-top:1px solid {THEME['border']};">
          <p style="margin:0;font-size:19px;color:{THEME['text_muted']};">✂️ <em>Dashed line marks the playoff cut. Top 6 advance.</em></p>
        </div>
      </div>
    </div>"""


def render_heat_check(ranked: list[dict[str, Any]]) -> str:
    def tier(rank: int, total: int) -> tuple[str, str]:
        p = rank / total
        if p <= 0.20: return "🔥 ELITE",       THEME["gold"]
        if p <= 0.40: return "📈 CONTENDER",   THEME["green"]
        if p <= 0.60: return "➡️ MID-PACK",    THEME["slate_mid"]
        if p <= 0.80: return "📉 BUBBLE",      THEME["text_muted"]
        return "💀 DANGER ZONE", THEME["danger"]

    total     = len(ranked)
    max_score = ranked[0]["pr_score"] if ranked else 100.0
    rows      = ""

    for m in ranked:
        t_label, t_color = tier(m["rank"], total)
        bar = int((m["pr_score"] / max_score) * 100) if max_score else 0
        rows += (
            f'<div style="background:{THEME["card_bg"]};border-radius:10px;border:1px solid {THEME["border"]};'
            f'padding:16px 20px;margin-bottom:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
            f'<div style="min-width:36px;text-align:center;">'
            f'<span style="font-size:19px;font-weight:800;color:{THEME["slate_mid"]};">#{m["rank"]}</span></div>'
            f'<div style="flex:1;min-width:160px;">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">'
            f'<span style="font-size:22px;font-weight:700;color:{THEME["text_dark"]};">{m["name"]}</span>'
            f'<span style="font-size:20px;font-weight:700;color:{t_color};">{t_label}</span></div>'
            f'<div style="background:{THEME["off_white"]};border-radius:100px;height:6px;width:100%;">'
            f'<div style="background:linear-gradient(90deg,{THEME["red"]},{THEME["gold"]});'
            f'border-radius:100px;height:6px;width:{bar}%;"></div></div></div>'
            f'<div style="text-align:right;min-width:60px;">'
            f'<span style="font-size:22px;font-weight:900;color:{THEME["slate"]};">{m["pr_score"]:.1f}</span>'
            f'<span style="display:block;font-size:20px;">{m.get("trend", "➡️")}</span></div></div>'
        )

    note = (
        "(TEST MODE — scores are illustrative)"
        if TEST_MODE
        else f"Hybrid score: 60% win% + 40% points-for percentile. Week {ranked[0].get('rank', '?')} updated."
    )
    return f"""
    <div style="margin-bottom:40px;">
      {_section_header(SECTION_HEATCHECK, "Hybrid power rankings — record meets raw output.")}
      {rows}
      <p style="margin:12px 0 0;font-size:19px;color:{THEME['text_muted']};font-style:italic;">{note}</p>
    </div>"""


def render_matchup_results(matchups: list[dict[str, Any]], week: int) -> str:
    cards = ""
    for m in matchups:
        home_win  = m["home_pts"] >= m["away_pts"]
        in_prog   = m["home_pts"] == 0 and m["away_pts"] == 0

        def sc(win: bool) -> str:
            return f"font-size:20px;font-weight:900;color:{THEME['red'] if win else THEME['text_muted']};"

        score_display = (
            '<span style="font-size:17px;color:#6C757D;font-style:italic;">In progress…</span>'
            if in_prog else
            f'<span style="{sc(home_win)}">{m["home_pts"]:.2f}</span>'
            f'<span style="font-size:20px;color:{THEME["text_muted"]};margin:0 4px;">–</span>'
            f'<span style="{sc(not home_win)}">{m["away_pts"]:.2f}</span>'
        )

        cards += (
            f'<div style="background:{THEME["card_bg"]};border:1px solid {THEME["border"]};border-radius:10px;'
            f'padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;'
            f'justify-content:space-between;gap:8px;flex-wrap:wrap;">'
            f'<span style="font-size:17px;font-weight:{"800" if home_win and not in_prog else "500"};'
            f'color:{THEME["text_dark"] if home_win and not in_prog else THEME["text_muted"]};flex:1;">{m["home"]}</span>'
            f'<div style="text-align:center;min-width:110px;">{score_display}</div>'
            f'<span style="font-size:17px;font-weight:{"800" if not home_win and not in_prog else "500"};'
            f'color:{THEME["text_dark"] if not home_win and not in_prog else THEME["text_muted"]};flex:1;text-align:right;">{m["away"]}</span>'
            f'</div>'
        )

    return f"""
    <div style="margin-bottom:40px;">
      {_section_header(f"Week {week} Scoreboard", "Final results — no excuses accepted.")}
      {cards}
    </div>"""


# ─────────────────────────────────────────────
# MAGAZINE HTML TEMPLATE
# ─────────────────────────────────────────────
def build_email_html(
    intro_html:      str,
    awards_html:     str,
    standings_html:  str,
    heatcheck_html:  str,
    scoreboard_html: str,
    week:            int,
) -> str:
    year     = datetime.now(timezone.utc).year
    mode_tag = (
        ' <span style="background:#F4C542;color:#1A1A2E;font-size:17px;font-weight:700;'
        'padding:2px 6px;border-radius:4px;letter-spacing:1px;vertical-align:middle;">TEST</span>'
        if TEST_MODE else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>FDH Report — Week {week}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    body,table,td,a{{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}}
    table,td{{mso-table-lspace:0pt;mso-table-rspace:0pt;}}
    img{{-ms-interpolation-mode:bicubic;border:0;outline:none;text-decoration:none;}}
    body{{margin:0;padding:0;background-color:{THEME['off_white']};font-family:'Inter',Arial,sans-serif;}}
    a{{color:{THEME['red']};text-decoration:none;}}
    a:hover{{text-decoration:underline;}}
    @media only screen and (max-width:620px){{
      .wrapper{{padding:0 8px!important;}}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:{THEME['off_white']};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
       style="background-color:{THEME['off_white']};">
  <tr><td align="center" style="padding:24px 0 40px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
           style="max-width:640px;width:100%;" class="wrapper">
      <tr><td style="padding:0 16px;">

        <!-- HEADER -->
        <div style="background:{THEME['slate']};border-radius:16px 16px 0 0;padding:12px 28px 0;">
          <!-- Week badge top-right -->
          <div style="display:flex;justify-content:flex-end;margin-bottom:2px;">
            <div style="text-align:right;">
              <span style="background:{THEME['red']};color:{THEME['white']};font-size:19px;font-weight:800;
                           letter-spacing:1.5px;padding:6px 14px;border-radius:100px;text-transform:uppercase;">
                Week {week}{mode_tag}
              </span>
              <p style="margin:6px 0 0;font-size:19px;color:rgba(255,255,255,0.45);">
                {datetime.now(timezone.utc).strftime('%B %d, %Y')}
              </p>
            </div>
          </div>
          <!-- Centered: THE / shield / REPORT -->
          <div style="text-align:center;padding:2px 0 0;">
            <img src="cid:fdh_logo"
                 alt="FDH Fantasy Football Shield"
                 width="4680" height="4680"
                 style="display:inline-block;border:0;outline:none;text-decoration:none;object-fit:contain;max-width:100%;height:auto;" />
          </div>
        </div>
        <!-- BODY -->
        <div style="background:{THEME['off_white']};padding:28px 24px;">
          {intro_html}
          {scoreboard_html}
          {awards_html}
          {standings_html}
          {heatcheck_html}
        </div>

        <!-- FOOTER -->
        <div style="background:{THEME['slate']};border-radius:0 0 16px 16px;
                    padding:20px 28px;text-align:center;">
          <p style="margin:0 0 6px;font-size:22px;font-weight:900;color:{THEME['white']};letter-spacing:-0.5px;">
            {LOGO_TEXT}<span style="color:{THEME['red']};">.</span>
          </p>
          <p style="margin:0 0 12px;font-size:19px;color:rgba(255,255,255,0.45);
                    letter-spacing:2px;text-transform:uppercase;">Fantasy · Data · Hype</p>
          <p style="margin:0;font-size:19px;color:rgba(255,255,255,0.30);">
            © {year} FDH League &nbsp;|&nbsp; You're receiving this because you're in the league.
          </p>
        </div>

      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ─────────────────────────────────────────────
# PREVIEW SAVE
# ─────────────────────────────────────────────
def save_preview(html: str, week: int) -> str:
    path = f"fdh_week{week}_preview.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[INFO] Preview saved → {path}")
    return path



# ─────────────────────────────────────────────
# WEB / GITHUB PAGES OUTPUT
# ─────────────────────────────────────────────
def build_web_html(email_html: str, logo_path: str = "") -> str:
    """Swap CID image reference for base64 data URI so the page works in browsers."""
    import base64 as _b64
    html = email_html
    if logo_path and os.path.isfile(logo_path):
        with open(logo_path, "rb") as f:
            b64 = _b64.b64encode(f.read()).decode()
        html = html.replace('src="cid:fdh_logo"', f'src="data:image/png;base64,{b64}"')
    return html


def save_web_index(html: str, output_dir: str = "docs") -> str:
    """Write browser-ready HTML to docs/index.html for GitHub Pages hosting."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "index.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[INFO] Web version saved → {path}")
    return path


# ─────────────────────────────────────────────
# EMAIL SEND
# ─────────────────────────────────────────────
def send_email(html_body: str, subject: str, recipients: list[str], week: int = 1, logo_path: str = "") -> None:
    if not recipients:
        print("[WARN] No recipients set. Add FDH_RECIPIENTS=email1,email2 to your command.")
        return

    msg = MIMEMultipart("related")
    alt = MIMEMultipart("alternative")
    msg["Subject"]  = subject
    msg["From"]     = FROM_ADDRESS
    msg["To"]       = ", ".join(recipients)
    msg["Reply-To"] = REPLY_TO

    plain = textwrap.dedent(f"""\
        FDH Report — Week {week}
        ================================
        Open in a modern email client to see the full magazine layout.
    """)
    alt.attach(MIMEText(plain, "plain"))
    alt.attach(MIMEText(html_body, "html"))
    msg.attach(alt)

    # Attach logo as inline CID image so it renders in Gmail/Outlook
    if logo_path and os.path.isfile(logo_path):
        from email.mime.image import MIMEImage
        with open(logo_path, "rb") as img_file:
            logo_img = MIMEImage(img_file.read())
        logo_img.add_header("Content-ID", "<fdh_logo>")
        logo_img.add_header("Content-Disposition", "inline", filename="fdh_logo.png")
        msg.attach(logo_img)
        print("[INFO] Logo attached as inline CID image.")
    else:
        if logo_path:
            print(f"[WARN] Logo file not found at: {logo_path}")

    print(f"[INFO] Connecting to {SMTP_HOST}:{SMTP_PORT} …")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_ADDRESS, recipients, msg.as_string())
    print(f"[INFO] Email sent to {len(recipients)} recipient(s): {', '.join(recipients)}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main() -> None:
    # Detect current week
    CURRENT_WEEK = auto_detect_week()

    # Logo path — fdh_logo.png must be in the same folder as this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path  = os.path.join(script_dir, "fdh_logo.png")
    if not os.path.isfile(logo_path):
        print(f"[WARN] No logo found at {logo_path} — email will send without it.")

    print("=" * 54)
    print(f"  FDH Newsletter Engine — Week {CURRENT_WEEK} · {SEASON}")
    print(f"  League  : {LEAGUE_ID}")
    print(f"  TEST_MODE = {TEST_MODE}")
    print("=" * 54)

    # 1. Fetch data
    if TEST_MODE:
        print("[INFO] TEST_MODE active — using stub data.")
        managers = STUB_MANAGERS
        matchups = STUB_MATCHUPS
    else:
        print("[INFO] Fetching live data from Sleeper …")
        managers = build_managers_from_api(CURRENT_WEEK)
        matchups = build_matchups_from_api(CURRENT_WEEK, managers)

    # 2. Compute
    gotw   = pick_gotw(matchups)
    awards = compute_awards(managers, matchups)
    ranked = compute_power_rankings(managers)

    # 3. Render
    intro_html      = render_intro(CURRENT_WEEK, gotw)
    scoreboard_html = render_matchup_results(matchups, CURRENT_WEEK)
    awards_html     = render_awards(awards)
    standings_html  = render_standings(managers)
    heatcheck_html  = render_heat_check(ranked)

    # 4. Assemble
    html_body = build_email_html(
        intro_html, awards_html, standings_html,
        heatcheck_html, scoreboard_html, week=CURRENT_WEEK,
    )

    # 5. Save preview + web version
    preview_file = save_preview(html_body, CURRENT_WEEK)

    # Also write docs/index.html for GitHub Pages
    web_html = build_web_html(html_body, logo_path=logo_path)
    save_web_index(web_html, output_dir=os.path.join(script_dir, "docs"))

    # 6. Send
    subject = f"🏈 FDH Report — Week {CURRENT_WEEK} | {SEASON} Season"

    if TEST_MODE:
        print(f"[INFO] TEST_MODE — skipping send. Open '{preview_file}' in a browser.")
    else:
        if not SMTP_USER or not SMTP_PASS:
            print("[ERROR] Set SMTP_USER and SMTP_PASS before sending.")
            return
        send_email(html_body, subject, RECIPIENTS, week=CURRENT_WEEK, logo_path=logo_path)

    print("[DONE]")


if __name__ == "__main__":
    main()
