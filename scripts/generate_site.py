DIVISION_MAP = {
    # FDH North
    "1032906633749307392": "FDH North",   # Prettygrlrck
    "1114330483623694336": "FDH North",   # RedZoneGuru
    "1120105892286025728": "FDH North",   # justEATit
    "1116252821541830656": "FDH North",   # BigKens
    # FDH West
    "1034350371830968320": "FDH West",    # PaulyDsWalnuts
    "1034270560295006208": "FDH West",    # 2headedblindsquirrel
    "1116173850477277184": "FDH West",    # LeftofCenter25
    "201958586610356224":  "FDH West",    # theFFChef
    # FDH East
    "1128420934681079808": "FDH East",    # TheRealTea
    "887435530135252992":  "FDH East",    # Jarrin
    "1088314152050929664": "FDH East",    # Delvineo
    "1119830811148156928": "FDH East",    # BangBang4949
}



#!/usr/bin/env python3
"""
FDH Hall of Fame — Static Site Generator
=========================================
Reads _data/stats.json (+ per-season JSON files) and renders all HTML pages
into docs/hof/ by filling {{PLACEHOLDER}} tokens in templates/*.html.

The repo already uses Jekyll to build docs/ → docs/_site/ for GitHub Pages.
Plain HTML files placed in docs/hof/ are passed through by Jekyll unchanged,
so the HOF site appears at:
    https://fdhgeneral.github.io/fdh-report/hof/

Usage:
    python scripts/generate_site.py
    python scripts/generate_site.py --out docs/hof     (explicit override)

Output: docs/hof/  (Jekyll picks it up automatically)
"""

import json
import math
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "_data"
TMPL_DIR = ROOT / "templates"

# Output inside Jekyll source so it gets deployed alongside existing site
# Override with --out <path> if needed
if "--out" in sys.argv:
    SITE_DIR = Path(sys.argv[sys.argv.index("--out") + 1])
else:
    SITE_DIR = ROOT / "docs" / "hof"

ASSET_SRC = ROOT / "assets"   # our fdh.css / fdh.js source

BUILD_TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
YEAR     = datetime.now(timezone.utc).year

DIVISIONS = ["FDH North", "FDH West", "FDH East"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def load(filename: str):
    p = DATA_DIR / filename
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def render(template_name: str, replacements: dict) -> str:
    tmpl = (TMPL_DIR / template_name).read_text(encoding="utf-8")
    for key, val in replacements.items():
        tmpl = tmpl.replace("{{" + key + "}}", str(val))
    return tmpl


def write_page(filename: str, content: str):
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / filename).write_text(content, encoding="utf-8")
    size = len(content)
    print(f"  ✓ {SITE_DIR.name}/{filename} ({size:,} bytes)")


def pct(n, d):
    return f"{(n/d*100):.1f}" if d else "0.0"


def win_pct_str(w, l, t=0):
    total = w + l + t
    return f"{(w/total):.3f}" if total else ".000"


def rank_badge_class(rank: int) -> str:
    return {1: "rank-gold", 2: "rank-silver", 3: "rank-bronze"}.get(rank, "rank-other")


def initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper()


# ── Component builders ────────────────────────────────────────────────────────

def hof_card_html(m: dict, rank: int) -> str:
    badge   = rank_badge_class(rank)
    ini     = initials(m["display_name"])
    team    = m.get("latest_team") or m["display_name"]
    div     = m.get("division") or "FDH"
    w, l    = m.get("wins", 0), m.get("losses", 0)
    wp      = win_pct_str(w, l, m.get("ties", 0))
    pf      = f"{m.get('pf', 0):,.1f}"
    titles  = m.get("championships", 0)
    goat    = m.get("goat_score", 0)
    seasons = m.get("seasons", 0)
    return f"""
<div class="hof-card">
  <div class="hof-card__rank-badge {badge}">{rank}</div>
  <div class="hof-card__banner"></div>
  <div class="hof-card__avatar">{ini}</div>
  <div class="hof-card__name">{m['display_name']}</div>
  <div class="hof-card__team">{team} &middot; {div}</div>
  <div class="hof-card__stats">
    <div class="hof-stat">
      <span class="hof-stat__val" data-counter data-target="{w}">{w}</span>
      <span class="hof-stat__key">Wins</span>
    </div>
    <div class="hof-stat">
      <span class="hof-stat__val">{wp}</span>
      <span class="hof-stat__key">Win %</span>
    </div>
    <div class="hof-stat">
      <span class="hof-stat__val">{titles}</span>
      <span class="hof-stat__key">Titles</span>
    </div>
  </div>
  <div style="padding:.75rem 1.25rem;border-top:1px solid rgba(0,0,0,.07);display:flex;justify-content:space-between;align-items:center;">
    <span style="font-size:.78rem;color:var(--fdh-text-muted);">{seasons} season{'s' if seasons!=1 else ''} &middot; {pf} PF</span>
    <span class="badge badge--red">GOAT {goat:.1f}</span>
  </div>
</div>"""


def hof_table_row(m: dict, rank: int) -> str:
    w, l, t  = m.get("wins", 0), m.get("losses", 0), m.get("ties", 0)
    wp       = win_pct_str(w, l, t)
    pf       = f"{m.get('pf', 0):,.1f}"
    playoffs = m.get("playoff_apps", 0)
    titles   = m.get("championships", 0)
    goat     = m.get("goat_score", 0)
    div      = m.get("division") or "—"
    seasons  = m.get("seasons", 0)
    team     = m.get("latest_team") or "—"
    return (f"<tr>"
            f"<td class='rank'>{rank}</td>"
            f"<td><strong>{m['display_name']}</strong></td>"
            f"<td>{team}</td><td>{div}</td><td>{seasons}</td>"
            f"<td>{w}</td><td>{l}</td>"
            f"<td class='win-pct'>{wp}</td>"
            f"<td>{'🏆 ' * titles if titles else '—'}</td>"
            f"<td>{playoffs}</td><td>{pf}</td>"
            f"<td><strong>{goat:.1f}</strong></td>"
            f"</tr>")


def accolade_block(label: str, holder: str, icon: str = "🏅") -> str:
    return f"""
<div class="stat-block">
  <div class="stat-block__num">{icon}</div>
  <div class="stat-block__label">{label}</div>
  <div style="margin-top:.4rem;font-family:var(--font-display);color:var(--fdh-slate);">{holder}</div>
</div>"""


def rivalry_card_preview(r: dict) -> str:
    wins_a, wins_b = r["wins_a"], r["wins_b"]
    leader = r["name_a"] if wins_a >= wins_b else r["name_b"]
    score  = f"{wins_a}–{wins_b}"
    return f"""
<div class="card">
  <div class="card__header">
    <div style="display:flex;align-items:center;justify-content:space-between;">
      <span style="font-family:var(--font-display);color:#fff;">{r['name_a']}</span>
      <span style="font-family:var(--font-display);font-size:1.2rem;color:var(--fdh-red-light);">vs</span>
      <span style="font-family:var(--font-display);color:#fff;">{r['name_b']}</span>
    </div>
  </div>
  <div class="card__body">
    <div style="text-align:center;margin-bottom:.75rem;">
      <span style="font-family:var(--font-display);font-size:2rem;color:var(--fdh-red);">{score}</span>
    </div>
    <div style="display:flex;gap:.5rem;flex-wrap:wrap;justify-content:center;">
      <span class="rivalry-badge">⚡ {r['total_meetings']} meetings</span>
      {f'<span class="rivalry-badge">🏆 {r["playoff_meetings"]} playoff</span>' if r["playoff_meetings"] else ''}
    </div>
  </div>
  <div class="card__footer">
    <span style="font-size:.82rem;color:var(--fdh-text-muted);">Series leader: <strong>{leader}</strong></span>
    <span class="badge badge--red">Score {r['rivalry_score']:.0f}</span>
  </div>
</div>"""


def rivalry_card_full(r: dict) -> str:
    wins_a, wins_b = r["wins_a"], r["wins_b"]
    a_lead = wins_a > wins_b
    b_lead = wins_b > wins_a
    return f"""
<div class="rivalry-card">
  <div class="rivalry-card__header">
    <div class="rivalry-card__manager" style="text-align:left;">{r['name_a']}</div>
    <div class="rivalry-card__vs">VS</div>
    <div class="rivalry-card__manager" style="text-align:right;">{r['name_b']}</div>
  </div>
  <div class="rivalry-card__score">
    <span class="rivalry-score__val {'leader' if a_lead else 'trailer'}">{wins_a}</span>
    <span class="rivalry-score__dash">—</span>
    <span class="rivalry-score__val {'leader' if b_lead else 'trailer'}">{wins_b}</span>
  </div>
  <div class="rivalry-card__meta">
    <span>⚡ {r['total_meetings']} total meetings</span>
    {f'<span>🏆 {r["playoff_meetings"]} in playoffs</span>' if r["playoff_meetings"] else ''}
    <span>Rivalry score: <strong>{r['rivalry_score']:.0f}</strong></span>
  </div>
</div>"""


def h2h_table_row(r: dict, from_a: bool) -> str:
    if from_a:
        mgr, opp, w, l = r["name_a"], r["name_b"], r["wins_a"], r["wins_b"]
        pf, pa = r["pf_a"], r["pf_b"]
    else:
        mgr, opp, w, l = r["name_b"], r["name_a"], r["wins_b"], r["wins_a"]
        pf, pa = r["pf_b"], r["pf_a"]
    wp       = win_pct_str(w, l)
    meetings = r["total_meetings"]
    avg_margin = round((pf - pa) / meetings, 1) if meetings else 0
    sign = "+" if avg_margin >= 0 else ""
    return (f"<tr>"
            f"<td><strong>{mgr}</strong></td><td>{opp}</td>"
            f"<td>{w}</td><td>{l}</td>"
            f"<td class='win-pct'>{wp}</td>"
            f"<td>{meetings}</td>"
            f"<td>{sign}{avg_margin}</td>"
            f"<td>{r['playoff_meetings']}</td>"
            f"<td>—</td></tr>")


def champion_timeline_item(season: str, champion: str, record: str = "") -> str:
    return f"""
<div class="timeline__item">
  <div class="timeline__dot"></div>
  <div class="timeline__year">{season} Season</div>
  <div class="timeline__title">🏆 {champion}</div>
  <div class="timeline__desc">{record}</div>
</div>"""


def division_card(div_name: str, managers: list) -> str:
    manager_list = "".join(
        f'<li style="padding:.3rem 0;border-bottom:1px solid rgba(0,0,0,.06);">'
        f'<strong>{m["display_name"]}</strong>'
        f'<span style="float:right;font-size:.82rem;color:var(--fdh-text-muted);">'
        f'{win_pct_str(m.get("wins",0), m.get("losses",0))} W%</span></li>'
        for m in sorted(managers, key=lambda x: x.get("goat_score", 0), reverse=True)
    )
    return f"""
<div class="card">
  <div class="card__header--red card__header">
    <h3 style="color:#fff;margin:0;">{div_name}</h3>
  </div>
  <div class="card__body">
    <ul style="list-style:none;">{manager_list or '<li style="color:var(--fdh-text-muted);font-size:.88rem;">No managers assigned yet — update DIVISION_MAP in fetch_sleeper.py</li>'}</ul>
  </div>
</div>"""


def standings_row(m: dict, rank: int, show_division: bool = True) -> str:
    w, l, t  = m.get("wins", 0), m.get("losses", 0), m.get("ties", 0)
    wp       = win_pct_str(w, l, t)
    pf       = f"{m.get('pf', 0):,.1f}"
    pa       = f"{m.get('pa', 0):,.1f}"
    playoffs = m.get("playoff_apps", 0)
    titles   = m.get("championships", 0)
    seasons  = m.get("seasons", 0)
    team     = m.get("latest_team") or "—"
    div      = m.get("division") or "—"
    cols = f"<td class='rank'>{rank}</td><td><strong>{m['display_name']}</strong></td><td>{team}</td>"
    if show_division:
        cols += f"<td>{div}</td><td>{seasons}</td>"
    cols += (f"<td>{w}</td><td>{l}</td><td>{t}</td>"
             f"<td class='win-pct'>{wp}</td>"
             f"<td>{pf}</td><td>{pa}</td>"
             f"<td>{playoffs}</td>"
             f"<td>{'🏆' * titles if titles else '—'}</td>")
    return f"<tr>{cols}</tr>"


def trade_leaderboard_row(m: dict, rank: int, trade_count: int, seasons: int) -> str:
    rate = f"{trade_count/seasons:.1f}" if seasons else "0"
    return (f"<tr><td class='rank'>{rank}</td>"
            f"<td><strong>{m['display_name']}</strong></td>"
            f"<td>{trade_count}</td><td>{seasons}</td>"
            f"<td>{rate}</td><td>—</td><td>—</td><td>—</td></tr>")


def draft_grade_row(m: dict, rank: int) -> str:
    return (f"<tr><td class='rank'>{rank}</td>"
            f"<td><strong>{m['display_name']}</strong></td>"
            f"<td>{m.get('seasons', 0)}</td>"
            f"<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>")


# ── Page generators ───────────────────────────────────────────────────────────

def gen_index(stats: dict):
    managers = sorted(stats["managers"], key=lambda x: x.get("goat_score", 0), reverse=True)
    active   = [m for m in managers if m.get("seasons", 0) > 0]
    for _m in managers:  # apply DIVISION_MAP to every manager dict
        _m["division"] = DIVISION_MAP.get(str(_m.get("user_id", "")), "")

    goat_cards    = "".join(hof_card_html(m, i+1) for i, m in enumerate(active[:3]))
    win_leader    = active[0] if active else {}
    _pp = [m for m in active if m.get("wins", 0) + m.get("losses", 0) >= 8]
    pct_leader    = max(_pp or active, key=lambda x: x.get("win_pct", 0), default={})
    title_king    = max(active, key=lambda x: x.get("championships", 0), default={})
    top_rivals    = stats.get("rivalries", [])[:2]
    rivalry_cards = "".join(rivalry_card_preview(r) for r in top_rivals)
    champions_tl  = champion_timeline_item("2025", win_leader.get("display_name", "TBD"), "Data populates after fetch")

    div_cards = ""
    for div in DIVISIONS:
        members = [m for m in active if m.get("division") == div]
        div_cards += division_card(div, members)

    # Compute most trades in one season
    import json as _tj
    from pathlib import Path as _TP
    _tD = _TP('_data')
    _tn, _tu = 0, None
    for _ty in ['2024', '2025', '2026']:
        _rp  = _tD / ('rosters_' + _ty + '.json')
        _tp2 = _tD / ('trades_'  + _ty + '.json')
        if not (_rp.exists() and _tp2.exists()): continue
        _rm = {r['roster_id']: r.get('owner_id') for r in _tj.loads(_rp.read_text())}
        _tl = _tj.loads(_tp2.read_text())
        if not isinstance(_tl, list): continue
        _sc = {}
        for _tr in _tl:
            for _ri in (_tr.get('roster_ids') or []):
                _ui = _rm.get(_ri)
                if _ui: _sc[_ui] = _sc.get(_ui, 0) + 1
        for _ui, _c in _sc.items():
            if _c > _tn: _tn, _tu = _c, _ui
    _un = {m['user_id']: m['display_name'] for m in managers}
    _tk = _un.get(_tu, '-') if _tu else '-'
    replacements = {
        "LEAGUE_FOUNDED":            "2019",
        "TOTAL_MANAGERS":            len(active),
        "TOTAL_SEASONS":             max((m.get("seasons", 0) for m in active), default=0),
        "TOTAL_GAMES":               sum(m.get("wins", 0) + m.get("losses", 0) for m in active) // 2,
        "TOTAL_TRADES":              "—",
        "GOAT_CARDS":                goat_cards,
        "ALL_TIME_WIN_LEADER_WINS":  win_leader.get("wins", "—"),
        "ALL_TIME_WIN_LEADER":       win_leader.get("display_name", "—"),
        "BEST_WIN_PCT":              f"{pct_leader.get('win_pct', 0)*100:.1f}" if pct_leader else "—",
        "BEST_WIN_PCT_OWNER":        pct_leader.get("display_name", "—"),
        "MOST_CHAMPIONSHIPS":        title_king.get("championships", 0),
        "CHAMPIONSHIP_KING":         title_king.get("display_name", "—"),
        "MOST_TRADES_SINGLE":        str(_tn) if _tn else "0",
        "TRADE_KING":                _tk,
        "TOP_RIVALRY_CARDS":         rivalry_cards,
        "CHAMPIONS_TIMELINE":        champions_tl,
        "DIVISION_CARDS":            div_cards,
        "BUILD_TS":                  BUILD_TS,
        "YEAR":                      YEAR,
    }
    write_page("index.html", render("index.html", replacements))


def gen_hof(stats: dict):
    managers = sorted(stats["managers"], key=lambda x: x.get("goat_score", 0), reverse=True)
    active   = [m for m in managers if m.get("seasons", 0) > 0]
    cards    = "".join(hof_card_html(m, i+1)  for i, m in enumerate(active))
    rows     = "".join(hof_table_row(m, i+1)  for i, m in enumerate(active))
    win_king = active[0] if active else {}
    _pl = [m for m in active if m.get("wins", 0) + m.get("losses", 0) >= 8]
    pct_l    = max(_pl or active, key=lambda x: x.get("win_pct", 0), default={})
    title_k  = max(active, key=lambda x: x.get("championships", 0), default={})
    po_k     = max(active, key=lambda x: x.get("playoff_apps", 0) / max(x.get("seasons", 1), 1), default={})
    accolades = (accolade_block("GOAT Champion",    win_king.get("display_name", "—"), "🐐") +
                 accolade_block("Best Win %",        pct_l.get("display_name", "—"),   "📊") +
                 accolade_block("Most Titles",       title_k.get("display_name", "—"), "🏆") +
                 accolade_block("Best Playoff %",    po_k.get("display_name", "—"),    "🎯"))
    replacements = {
        "HOF_CARDS": cards, "HOF_TABLE_ROWS": rows, "ACCOLADE_BLOCKS": accolades,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("hof.html", render("hof.html", replacements))


def gen_standings(stats: dict):
    managers  = sorted(stats["managers"], key=lambda x: x.get("win_pct", 0), reverse=True)
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    all_rows  = "".join(standings_row(m, i+1)       for i, m in enumerate(active))
    no_div    = "<tr><td colspan='9' style='text-align:center;color:var(--fdh-text-muted);'>No managers assigned to this division yet — update DIVISION_MAP in fetch_sleeper.py</td></tr>"
    n_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH North"])) or no_div
    w_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH West"]))  or no_div
    e_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH East"]))  or no_div
    replacements = {
        "TOTAL_MANAGERS": len(active),
        "TOTAL_SEASONS":  max((m.get("seasons", 0) for m in active), default=0),
        "STANDINGS_TABLE_ROWS_ALL":   all_rows,
        "STANDINGS_TABLE_ROWS_NORTH": n_rows,
        "STANDINGS_TABLE_ROWS_WEST":  w_rows,
        "STANDINGS_TABLE_ROWS_EAST":  e_rows,
        "SEASON_RESULTS_ROWS": "<tr><td colspan='6' style='text-align:center;color:var(--fdh-text-muted);'>Season data populates after fetch.</td></tr>",
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("standings.html", render("standings.html", replacements))


def gen_rivalries(stats: dict):
    rivalries = stats.get("rivalries", [])
    top_full  = "".join(rivalry_card_full(r) for r in rivalries[:6])
    h2h_rows  = "".join(h2h_table_row(r, True) + h2h_table_row(r, False) for r in rivalries)
    most_m    = rivalries[0]["total_meetings"] if rivalries else 0
    dom_r     = max(rivalries, key=lambda x: max(x["wins_a"], x["wins_b"]) / max(x["total_meetings"], 1), default={})
    dom_pct   = f"{max(dom_r.get('wins_a',0), dom_r.get('wins_b',0)) / max(dom_r.get('total_meetings',1),1) * 100:.0f}" if dom_r else "—"
    replacements = {
        "TOTAL_H2H_MATCHUPS":         len(rivalries),
        "CLOSEST_RIVALRY_GAMES":      most_m,
        "MOST_DOMINANT_RIVALRY_PCT":  dom_pct,
        "TOP_RIVALRY_CARDS_FULL":     top_full,
        "H2H_TABLE_ROWS":             h2h_rows or "<tr><td colspan='9' style='text-align:center;'>No data yet.</td></tr>",
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("rivalries.html", render("rivalries.html", replacements))


def gen_trades(stats: dict):
    managers  = sorted(stats["managers"], key=lambda x: x.get("seasons", 0), reverse=True)
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    trade_rows= "".join(trade_leaderboard_row(m, i+1, 0, m.get("seasons", 0)) for i, m in enumerate(active))
    replacements = {
        "TOTAL_TRADES":               "—",
        "MOST_ACTIVE_TRADER":         active[0]["display_name"] if active else "—",
        "BUSIEST_TRADE_SEASON":       "—",
        "BUSIEST_TRADE_SEASON_COUNT": "—",
        "TRADE_LEADERBOARD_ROWS":     trade_rows,
        "TRADE_SEASON_OPTIONS":       "<option>All Seasons</option>",
        "TRADE_LOG_CARDS":            '<p style="color:var(--fdh-text-muted);text-align:center;padding:2rem;">Trade log populates from Sleeper API. Run the fetch script to populate.</p>',
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("trades.html", render("trades.html", replacements))


def gen_draft(stats: dict):
    managers  = sorted(stats["managers"], key=lambda x: x.get("goat_score", 0), reverse=True)
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    grade_rows= "".join(draft_grade_row(m, i+1) for i, m in enumerate(active))
    pos_rows  = "".join(
        f"<tr><td><strong>{m['display_name']}</strong></td>"
        "<td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>"
        for m in active
    )
    replacements = {
        "TOTAL_DRAFT_PICKS":        "—",
        "BEST_DRAFT_GRADE_MANAGER": active[0]["display_name"] if active else "—",
        "MOST_COMMON_FIRST_PICK":   "—",
        "DRAFT_SEASON_TABS":        '<button class="tab-btn active" data-tab="tab-draft-0">Latest Season</button>',
        "DRAFT_SEASON_PANELS":      '<div id="tab-draft-0" class="tab-panel active"><p style="color:var(--fdh-text-muted);padding:1rem;">Draft board populates from Sleeper API. Run fetch script to populate.</p></div>',
        "DRAFT_GRADE_TABLE_ROWS":   grade_rows,
        "DRAFT_POSITION_ROWS":      pos_rows,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("draft.html", render("draft.html", replacements))


def gen_records(stats: dict):
    managers  = stats["managers"]
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    all_highs = sorted(
        [{"week": wh["week"], "season": wh.get("season","?"), "score": wh["score"], "manager": m["display_name"]}
         for m in active for wh in m.get("weekly_highs", [])],
        key=lambda x: x["score"], reverse=True
    )
    high_week   = all_highs[0]  if all_highs else {}
    low_week    = all_highs[-1] if all_highs else {}
    high_season = max(active, key=lambda x: x.get("pf", 0), default={})
    streak_king = max(active, key=lambda x: x.get("max_win_streak", 0), default={})
    bust_king   = max(active, key=lambda x: x.get("max_lose_streak", 0), default={})
    playoff_king= max(active, key=lambda x: x.get("playoff_apps", 0), default={})
    weekly_rows = "".join(
        f"<tr><td>{h.get('season','—')}</td><td>Week {h['week']}</td>"
        f"<td><strong>{h['manager']}</strong></td>"
        f"<td><strong>{h['score']:.1f}</strong></td>"
        f"<td>—</td><td>W</td></tr>"
        for h in all_highs[:20]
    ) or "<tr><td colspan='6' style='text-align:center;color:var(--fdh-text-muted);'>No data yet.</td></tr>"

    def v(d, key, fmt=None):
        val = d.get(key, "—") if d else "—"
        return fmt.format(val) if fmt and val != "—" else str(val)

    # Compute matchup-based records (completed seasons only)
    import json as _rj; from pathlib import Path as _RP
    _rD=_RP('_data'); _REG=set(range(1,15)); _DONE=['2024','2025']
    _hi_pf=(0.0,'—','—'); _hi_pa=(0.0,'—','—')
    _lo_pa=(1e9,'—','—'); _hi_mg=(0.0,'—','—')
    _lo_mg=(1e9,'—','—'); _b_reg=(0,999,'—','—')
    for _sy in _DONE:
        _rrp=_rD/f'rosters_{_sy}.json'; _rmp=_rD/f'matchups_{_sy}.json'
        if not(_rrp.exists() and _rmp.exists()): continue
        _n2u={m['user_id']:m['display_name'] for m in managers}
        _r2u={r['roster_id']:r.get('owner_id') for r in _rj.loads(_rrp.read_text())}
        _wks={}; [_wks.setdefault(e.get('week'),[]).append(e) for e in _rj.loads(_rmp.read_text())]
        _spf={}; _spa={}; _sw={}; _sl={}
        for _wk,_ents in _wks.items():
            _prs={}
            for _me in _ents: _prs.setdefault(_me.get('matchup_id'),[]).append(_me)
            for _mid,_pr in _prs.items():
                if len(_pr)!=2: continue
                _ea,_eb=_pr
                _ua=_r2u.get(_ea['roster_id']); _ub=_r2u.get(_eb['roster_id'])
                _pta=float(_ea.get('points') or 0); _ptb=float(_eb.get('points') or 0)
                if _pta<=0 and _ptb<=0: continue
                _mg=round(abs(_pta-_ptb),2); _wu=_ua if _pta>=_ptb else _ub
                _cx=f'Week {_wk}, {_sy}'
                if _mg>_hi_mg[0]: _hi_mg=(_mg,_n2u.get(_wu,'—'),_cx)
                if 0<_mg<_lo_mg[0]: _lo_mg=(_mg,_n2u.get(_wu,'—'),_cx)
                if _wk in _REG:
                    for _uid,_pt,_op in [(_ua,_pta,_ptb),(_ub,_ptb,_pta)]:
                        if not _uid: continue
                        _spf[_uid]=_spf.get(_uid,0.0)+_pt; _spa[_uid]=_spa.get(_uid,0.0)+_op
                        if _pt>_op: _sw[_uid]=_sw.get(_uid,0)+1
                        elif _op>_pt: _sl[_uid]=_sl.get(_uid,0)+1
        for _uid,_v in _spf.items():
            _nm=_n2u.get(_uid,'—')
            if _v>_hi_pf[0]: _hi_pf=(_v,_nm,_sy)
        for _uid,_v in _spa.items():
            _nm=_n2u.get(_uid,'—')
            if _v>_hi_pa[0]: _hi_pa=(_v,_nm,_sy)
            if 0<_v<_lo_pa[0]: _lo_pa=(_v,_nm,_sy)
        for _uid,_wv in _sw.items():
            _nm=_n2u.get(_uid,'—'); _lv=_sl.get(_uid,0)
            if _wv>_b_reg[0] or(_wv==_b_reg[0] and _lv<_b_reg[1]): _b_reg=(_wv,_lv,_nm,_sy)


    replacements = {
        "RECORD_HIGH_WEEK":            f"{high_week.get('score',0):.1f}" if high_week else "—",
        "RECORD_HIGH_WEEK_HOLDER":     high_week.get("manager", "—"),
        "RECORD_HIGH_WEEK_CONTEXT":    f"Week {high_week.get('week','?')}, {high_week.get('season','?')} Season" if high_week else "",
        "RECORD_LOW_WEEK":             f"{low_week.get('score',0):.1f}" if low_week else "—",
        "RECORD_LOW_WEEK_HOLDER":      low_week.get("manager", "—"),
        "RECORD_LOW_WEEK_CONTEXT":     f"Week {low_week.get('week','?')}, {low_week.get('season','?')} Season" if low_week else "",
        "RECORD_HIGH_SEASON":          f"{_hi_pf[0]:.1f}" if _hi_pf[0] else "—",
        "RECORD_HIGH_SEASON_HOLDER":   _hi_pf[1],
        "RECORD_HIGH_SEASON_CONTEXT":  f"Best single-season PF • {_hi_pf[2]} season",
        "RECORD_HIGH_MARGIN":          f"{_hi_mg[0]:.2f}" if _hi_mg[0] else "—",
        "RECORD_HIGH_MARGIN_HOLDER":   _hi_mg[1],
        "RECORD_HIGH_MARGIN_CONTEXT":  _hi_mg[2],
        "RECORD_CLOSE_MARGIN":         f"{_lo_mg[0]:.2f}" if _lo_mg[0]<1e9 else "—",
        "RECORD_CLOSE_MARGIN_HOLDER":  _lo_mg[1],
        "RECORD_CLOSE_MARGIN_CONTEXT": _lo_mg[2],
        "RECORD_HIGH_AGAINST":         f"{_hi_pa[0]:.1f}" if _hi_pa[0] else "—",
        "RECORD_HIGH_AGAINST_HOLDER":  _hi_pa[1],
        "RECORD_HIGH_AGAINST_CONTEXT": f"{_hi_pa[2]} season",
        "RECORD_LOW_AGAINST":          f"{_lo_pa[0]:.1f}" if _lo_pa[0]<1e9 else "—",
        "RECORD_LOW_AGAINST_HOLDER":   _lo_pa[1],
        "RECORD_LOW_AGAINST_CONTEXT":  f"{_lo_pa[2]} season",
        "RECORD_BEST_REGULAR_RECORD":  f"{_b_reg[0]}-{_b_reg[1]}" if _b_reg[0] else "—",
        "RECORD_BEST_REGULAR_HOLDER":  _b_reg[2],
        "RECORD_BEST_REGULAR_CONTEXT": f"{_b_reg[2]} • {_b_reg[3]} season",
        "WIN_STREAK_MAX":              streak_king.get("max_win_streak", 0),
        "WIN_STREAK_HOLDER":           streak_king.get("display_name", "—"),
        "WIN_STREAK_CONTEXT":          "",
        "LOSE_STREAK_MAX":             bust_king.get("max_lose_streak", 0),
        "LOSE_STREAK_HOLDER":          bust_king.get("display_name", "—"),
        "LOSE_STREAK_CONTEXT":         "",
        "PLAYOFF_STREAK_MAX":          playoff_king.get("playoff_apps", 0),
        "PLAYOFF_STREAK_HOLDER":       playoff_king.get("display_name", "—"),
        "PLAYOFF_STREAK_CONTEXT":      "Playoff appearances",
        "LAST_PLACE_STREAK":           "—", "LAST_PLACE_HOLDER": "—", "LAST_PLACE_CONTEXT": "",
        "CHAMPIONS_TABLE_ROWS":        "<tr><td colspan='8' style='text-align:center;color:var(--fdh-text-muted);'>Season data populates after fetch.</td></tr>",
        "WEEKLY_HIGH_ROWS":            weekly_rows,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("records.html", render("records.html", replacements))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n=== FDH Site Generator — {BUILD_TS} ===")
    print(f"    Output dir: {SITE_DIR.resolve()}\n")

    stats = load("stats.json")
    if stats is None:
        print("⚠  _data/stats.json not found — generating placeholder site.")
        stats = {"managers": [], "rivalries": [], "generated_at": BUILD_TS}

    # Copy our fdh.css + fdh.js assets into docs/hof/assets/
    # (keeps them scoped to the HOF section, won't conflict with Jekyll theme)
    asset_dest = SITE_DIR / "assets"
    if ASSET_SRC.exists():
        if asset_dest.exists():
            shutil.rmtree(asset_dest)
        shutil.copytree(ASSET_SRC, asset_dest)
        print(f"  ✓ assets/ → {asset_dest.relative_to(ROOT)}")
    else:
        print(f"  ⚠  assets/ not found at {ASSET_SRC} — CSS/JS will be missing")

    print("\nGenerating pages:")
    gen_index(stats)
    gen_hof(stats)
    gen_standings(stats)
    gen_rivalries(stats)
    gen_trades(stats)
    gen_draft(stats)
    gen_records(stats)

    # .nojekyll is NOT needed here — we're inside a Jekyll site intentionally
    # Jekyll will pass our plain HTML files through unchanged

    html_files = list(SITE_DIR.rglob("*.html"))
    print(f"\n✅ Done — {len(html_files)} HTML pages in {SITE_DIR.relative_to(ROOT)}/")
    print(f"   Live at: https://fdhgeneral.github.io/fdh-report/hof/")


if __name__ == "__main__":
    main()
