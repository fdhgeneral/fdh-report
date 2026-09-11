#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
GS   = ROOT / "scripts" / "generate_site.py"
src  = GS.read_text()

def replace_fn(source, fn_name, new_body):
    pattern = rf'(^def {fn_name}\(.*?)(?=^def |\Z|^# ── Main)'
    return re.sub(pattern, new_body, source, flags=re.DOTALL | re.MULTILINE)

NEW_STANDINGS = r'''def gen_standings(stats: dict):
    import json as _sj
    from pathlib import Path as _SP
    _D = _SP('_data')
    NAME_MAP = {"justEATit": "BROCKBAILBONDZ", "PaulyDsWalnuts": "scheeper", "Jarrin": "Jarrin1225"}
    def _yn(n): return NAME_MAP.get(n, n)
    managers  = sorted(stats["managers"], key=lambda x: x.get("win_pct", 0), reverse=True)
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    all_rows  = "".join(standings_row(m, i+1)       for i, m in enumerate(active))
    no_div    = "<tr><td colspan='9' style='text-align:center;color:var(--fdh-text-muted);'>No managers assigned to this division yet.</td></tr>"
    n_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH North"])) or no_div
    w_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH West"]))  or no_div
    e_rows    = "".join(standings_row(m, i+1, False) for i, m in enumerate([x for x in active if x.get("division") == "FDH East"]))  or no_div
    season_rows_html = ""
    for yr in ["2020", "2021", "2022", "2023"]:
        sf = _D / f"yahoo_standings_{yr}.json"
        if not sf.exists(): continue
        rows = _sj.loads(sf.read_text())
        for r in rows:
            owner_sl = _yn(r.get("owner", ""))
            champ_flag = " 🏆" if r.get("rank") == 1 else ""
            season_rows_html += (
                "<tr>"
                f"<td>{yr}</td><td>{r.get('rank','—')}</td>"
                f"<td><strong>{owner_sl}{champ_flag}</strong></td>"
                f"<td>{r.get('team','—')}</td>"
                f"<td>{r.get('wins',0)}-{r.get('losses',0)}</td>"
                f"<td>{r.get('pointsFor',0):.1f}</td></tr>"
            )
    if not season_rows_html:
        season_rows_html = "<tr><td colspan='6' style='text-align:center;color:var(--fdh-text-muted);'>Season data populates after fetch.</td></tr>"
    replacements = {
        "TOTAL_MANAGERS": len(active),
        "TOTAL_SEASONS":  max((m.get("seasons", 0) for m in active), default=0),
        "STANDINGS_TABLE_ROWS_ALL":   all_rows,
        "STANDINGS_TABLE_ROWS_NORTH": n_rows,
        "STANDINGS_TABLE_ROWS_WEST":  w_rows,
        "STANDINGS_TABLE_ROWS_EAST":  e_rows,
        "SEASON_RESULTS_ROWS": season_rows_html,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("standings.html", render("standings.html", replacements))

'''

NEW_TRADES = r'''def gen_trades(stats: dict):
    import json as _tj
    from pathlib import Path as _TP
    from collections import defaultdict as _tdd
    _D = _TP('_data')
    NAME_MAP = {"justEATit": "BROCKBAILBONDZ", "PaulyDsWalnuts": "scheeper", "Jarrin": "Jarrin1225"}
    def _yn(n): return NAME_MAP.get(n, n)
    managers  = sorted(stats["managers"], key=lambda x: x.get("seasons", 0), reverse=True)
    active    = [m for m in managers if m.get("seasons", 0) > 0]
    trade_counts  = _tdd(int)
    season_counts = _tdd(int)
    all_cards     = []
    for yr in ["2020", "2021", "2022", "2023"]:
        tf = _D / f"yahoo_trades_{yr}.json"
        if not tf.exists(): continue
        trades = _tj.loads(tf.read_text())
        season_counts[yr] += len(trades)
        for t in trades:
            parties = [_yn(p) for p in t.get("parties", [])]
            for p in parties: trade_counts[p] += 1
            players = t.get("players", [])
            pl_str = ", ".join(f"{pl['player']} → {_yn(pl.get('to',''))}" for pl in players if pl.get("player")) or "Draft picks"
            pt_str = " ↔ ".join(parties) or "Unknown"
            all_cards.append(
                f'<div class="trade-card" data-season="{yr}">'
                f'<div class="trade-card-header"><span class="trade-season-badge">{yr}</span>'
                f'<span class="trade-week">Week {t.get("week","?")}</span></div>'
                f'<div class="trade-parties">{pt_str}</div>'
                f'<div class="trade-players">{pl_str}</div></div>'
            )
    _n2u = {m["user_id"]: m["display_name"] for m in managers}
    for yr in ["2024", "2025"]:
        tf = _D / f"trades_{yr}.json"
        if not tf.exists(): continue
        trades = _tj.loads(tf.read_text())
        season_counts[yr] += len(trades)
        for t in trades:
            adds = t.get("adds") or {}; drops = t.get("drops") or {}
            involved = set()
            for uid in list(adds.values()) + list(drops.values()):
                if uid: involved.add(_n2u.get(str(uid), str(uid)))
            for nm in involved: trade_counts[nm] += 1
            if not involved: continue
            assets = list(adds.keys())[:6] or ["Draft picks"]
            pt_str = " ↔ ".join(sorted(involved))
            pl_str = ", ".join(assets)
            wk = t.get("settings", {}).get("seq", "?") if isinstance(t.get("settings"), dict) else "?"
            all_cards.append(
                f'<div class="trade-card" data-season="{yr}">'
                f'<div class="trade-card-header"><span class="trade-season-badge">{yr}</span>'
                f'<span class="trade-week">Week {wk}</span></div>'
                f'<div class="trade-parties">{pt_str}</div>'
                f'<div class="trade-players">{pl_str}</div></div>'
            )
    total_trades = sum(season_counts.values())
    busiest_yr   = max(season_counts, key=season_counts.get) if season_counts else "—"
    busiest_cnt  = season_counts.get(busiest_yr, 0)
    most_active  = max(active, key=lambda m: trade_counts.get(m.get("display_name",""), 0), default={})
    def _tc(m): return trade_counts.get(m.get("display_name", ""), 0)
    trade_rows   = "".join(trade_leaderboard_row(m, i+1, _tc(m), m.get("seasons", 0)) for i, m in enumerate(active))
    all_seasons  = sorted(season_counts.keys())
    season_opts  = '<option value="all">All Seasons</option>' + "".join(f'<option value="{y}">{y}</option>' for y in all_seasons)
    trade_log    = "".join(all_cards) or '<p style="color:var(--fdh-text-muted);text-align:center;padding:2rem;">No trade data found.</p>'
    replacements = {
        "TOTAL_TRADES": str(total_trades), "MOST_ACTIVE_TRADER": most_active.get("display_name","—"),
        "BUSIEST_TRADE_SEASON": busiest_yr, "BUSIEST_TRADE_SEASON_COUNT": str(busiest_cnt),
        "TRADE_LEADERBOARD_ROWS": trade_rows, "TRADE_SEASON_OPTIONS": season_opts,
        "TRADE_LOG_CARDS": trade_log, "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("trades.html", render("trades.html", replacements))

'''

NEW_DRAFT = r'''def gen_draft(stats: dict):
    import json as _dj
    from pathlib import Path as _DP
    _D = _DP('_data')
    NAME_MAP = {"justEATit": "BROCKBAILBONDZ", "PaulyDsWalnuts": "scheeper", "Jarrin": "Jarrin1225"}
    def _yn(n): return NAME_MAP.get(n, n)
    managers   = sorted(stats["managers"], key=lambda x: x.get("goat_score", 0), reverse=True)
    active     = [m for m in managers if m.get("seasons", 0) > 0]
    grade_rows = "".join(draft_grade_row(m, i+1) for i, m in enumerate(active))
    tabs_html = ""; panels_html = ""; total_picks = 0; first_picks = []; tab_idx = 0
    for yr in ["2020", "2021", "2022", "2023", "2024", "2025"]:
        df = _D / f"yahoo_drafts_{yr}.json"
        if not df.exists(): continue
        draft = _dj.loads(df.read_text())
        picks = draft.get("picks", [])
        if not picks: continue
        total_picks += len(picks)
        fp = next((p for p in picks if p.get("overall") == 1), None)
        if fp and fp.get("player"): first_picks.append((fp["player"], yr))
        rnd_html = ""
        rounds = sorted(set(p["round"] for p in picks))
        for rnd in rounds[:3]:
            rnd_picks = sorted([p for p in picks if p["round"] == rnd], key=lambda x: x["pick"])
            rnd_html += f'<tr><td colspan="4" style="background:var(--fdh-bg-card);font-weight:700;padding:.4rem .75rem;">Round {rnd}</td></tr>'
            for p in rnd_picks:
                kb = ' <span style="font-size:.7rem;background:#f59e0b;color:#fff;border-radius:4px;padding:1px 5px;">K</span>' if p.get("keeper") else ""
                tb = ' <span style="font-size:.7rem;background:#6366f1;color:#fff;border-radius:4px;padding:1px 5px;">T</span>' if p.get("traded") else ""
                rnd_html += f'<tr><td>{p.get("overall","—")}</td><td><strong>{p.get("player","Unknown")}</strong>{kb}{tb}</td><td>{p.get("position","—")}</td><td>{_yn(p.get("owner","—"))}</td></tr>'
        if len(rounds) > 3:
            rnd_html += f'<tr><td colspan="4" style="text-align:center;color:var(--fdh-text-muted);font-style:italic;">+ {len(rounds)-3} more rounds</td></tr>'
        ac = " active" if tab_idx == 0 else ""
        tabs_html   += f'<button class="tab-btn{ac}" data-tab="tab-draft-{tab_idx}">{yr}</button>'
        panels_html += (f'<div id="tab-draft-{tab_idx}" class="tab-panel{ac}">'
            f'<h4 style="margin:.5rem 0;">{yr} Draft — {len(picks)} picks ({draft.get("teams","?")} teams, {draft.get("rounds","?")} rounds)</h4>'
            '<table class="hof-table"><thead><tr><th>#</th><th>Player</th><th>Pos</th><th>Owner</th></tr></thead><tbody>'
            + rnd_html + '</tbody></table></div>')
        tab_idx += 1
    if not tabs_html:
        tabs_html   = '<button class="tab-btn active" data-tab="tab-draft-0">Draft</button>'
        panels_html = '<div id="tab-draft-0" class="tab-panel active"><p style="color:var(--fdh-text-muted);padding:1rem;">Draft data unavailable.</p></div>'
    if first_picks:
        from collections import Counter as _DC
        top_player, top_count = _DC(p for p, _ in first_picks).most_common(1)[0]
        common_first = f"{top_player} ({top_count}x #1)"
    else:
        common_first = "—"
    pos_rows = "".join("<tr><td><strong>" + m["display_name"] + "</strong></td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td><td>—</td></tr>" for m in active)
    replacements = {
        "TOTAL_DRAFT_PICKS": str(total_picks) if total_picks else "—",
        "BEST_DRAFT_GRADE_MANAGER": active[0]["display_name"] if active else "—",
        "MOST_COMMON_FIRST_PICK": common_first,
        "DRAFT_SEASON_TABS": tabs_html, "DRAFT_SEASON_PANELS": panels_html,
        "DRAFT_GRADE_TABLE_ROWS": grade_rows, "DRAFT_POSITION_ROWS": pos_rows,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("draft.html", render("draft.html", replacements))

'''

NEW_RECORDS = r'''def gen_records(stats: dict):
    import json as _rj
    from pathlib import Path as _RP
    _rD = _RP('_data')
    NAME_MAP = {"justEATit": "BROCKBAILBONDZ", "PaulyDsWalnuts": "scheeper", "Jarrin": "Jarrin1225"}
    def _yn(n): return NAME_MAP.get(n, n)
    managers = stats["managers"]
    active   = [m for m in managers if m.get("seasons", 0) > 0]
    all_highs = sorted(
        [{"week": wh["week"], "season": wh.get("season","?"), "score": wh["score"], "manager": m["display_name"]}
         for m in active for wh in m.get("weekly_highs", [])],
        key=lambda x: x["score"], reverse=True)
    _REG_Y = set(range(1, 15))
    yahoo_week_highs = []
    _hi_pf=(0.0,"—","—"); _hi_pa=(0.0,"—","—"); _lo_pa=(1e9,"—","—")
    _hi_mg=(0.0,"—","—"); _lo_mg=(1e9,"—","—"); _b_reg=(0,999,"—","—")
    for _sy in ["2020","2021","2022","2023"]:
        _ymp = _rD / f"yahoo_matchups_{_sy}.json"
        if not _ymp.exists(): continue
        _games = _rj.loads(_ymp.read_text())
        _spf={}; _spa={}; _sw={}; _sl={}
        for g in _games:
            a=g["teamA"]; b=g["teamB"]
            oa=_yn(a["owner"]); ob=_yn(b["owner"])
            pa=float(a["points"]); pb=float(b["points"])
            wk=g["week"]; mg=round(abs(pa-pb),2)
            winner=_yn(g.get("winner",""))
            cx=f"Week {wk}, {_sy}"
            if mg>_hi_mg[0]: _hi_mg=(mg,winner,cx)
            if 0<mg<_lo_mg[0]: _lo_mg=(mg,winner,cx)
            if wk in _REG_Y:
                for nm,pt,op in [(oa,pa,pb),(ob,pb,pa)]:
                    if pa>0 or pb>0:
                        _spf[nm]=_spf.get(nm,0.0)+pt; _spa[nm]=_spa.get(nm,0.0)+op
                        if pt>op: _sw[nm]=_sw.get(nm,0)+1
                        elif op>pt: _sl[nm]=_sl.get(nm,0)+1
            for nm,pt in [(oa,pa),(ob,pb)]:
                if pt>0: yahoo_week_highs.append({"week":wk,"season":_sy,"score":pt,"manager":nm})
        for nm,v in _spf.items():
            if v>_hi_pf[0]: _hi_pf=(v,nm,_sy)
        for nm,v in _spa.items():
            if v>_hi_pa[0]: _hi_pa=(v,nm,_sy)
            if 0<v<_lo_pa[0]: _lo_pa=(v,nm,_sy)
        for nm,wv in _sw.items():
            lv=_sl.get(nm,0)
            if wv>_b_reg[0] or (wv==_b_reg[0] and lv<_b_reg[1]): _b_reg=(wv,lv,nm,_sy)
    _REG_S=set(range(1,15))
    _n2u={m["user_id"]:m["display_name"] for m in managers}
    for _sy in ["2024","2025"]:
        _rrp=_rD/f"rosters_{_sy}.json"; _rmp=_rD/f"matchups_{_sy}.json"
        if not(_rrp.exists() and _rmp.exists()): continue
        _r2u={r["roster_id"]:r.get("owner_id") for r in _rj.loads(_rrp.read_text())}
        _wks={}
        [_wks.setdefault(e.get("week"),[]).append(e) for e in _rj.loads(_rmp.read_text())]
        _spf={}; _spa={}; _sw={}; _sl={}
        for _wk,_ents in _wks.items():
            _prs={}
            for _me in _ents: _prs.setdefault(_me.get("matchup_id"),[]).append(_me)
            for _mid,_pr in _prs.items():
                if len(_pr)!=2: continue
                _ea,_eb=_pr
                _ua=_r2u.get(_ea["roster_id"]); _ub=_r2u.get(_eb["roster_id"])
                _pta=float(_ea.get("points") or 0); _ptb=float(_eb.get("points") or 0)
                if _pta<=0 and _ptb<=0: continue
                _mg=round(abs(_pta-_ptb),2)
                _wu=_n2u.get(_ua,"—") if _pta>=_ptb else _n2u.get(_ub,"—")
                _cx=f"Week {_wk}, {_sy}"
                if _mg>_hi_mg[0]: _hi_mg=(_mg,_wu,_cx)
                if 0<_mg<_lo_mg[0]: _lo_mg=(_mg,_wu,_cx)
                if _wk in _REG_S:
                    for _uid,_pt,_op in [(_ua,_pta,_ptb),(_ub,_ptb,_pta)]:
                        if not _uid: continue
                        nm=_n2u.get(_uid,_uid)
                        _spf[nm]=_spf.get(nm,0.0)+_pt; _spa[nm]=_spa.get(nm,0.0)+_op
                        if _pt>_op: _sw[nm]=_sw.get(nm,0)+1
                        elif _op>_pt: _sl[nm]=_sl.get(nm,0)+1
                for _uid,_pt in [(_ua,_pta),(_ub,_ptb)]:
                    nm=_n2u.get(_uid,"—")
                    if _pt>0: yahoo_week_highs.append({"week":_wk,"season":_sy,"score":_pt,"manager":nm})
        for nm,v in _spf.items():
            if v>_hi_pf[0]: _hi_pf=(v,nm,_sy)
        for nm,v in _spa.items():
            if v>_hi_pa[0]: _hi_pa=(v,nm,_sy)
            if 0<v<_lo_pa[0]: _lo_pa=(v,nm,_sy)
        for nm,wv in _sw.items():
            lv=_sl.get(nm,0)
            if wv>_b_reg[0] or (wv==_b_reg[0] and lv<_b_reg[1]): _b_reg=(wv,lv,nm,_sy)
    combined_highs = sorted(all_highs+yahoo_week_highs, key=lambda x: x["score"], reverse=True)
    high_week = combined_highs[0]  if combined_highs else {}
    low_week  = combined_highs[-1] if combined_highs else {}
    weekly_rows = "".join(
        f"<tr><td>{h.get('season','—')}</td><td>Week {h['week']}</td>"
        f"<td><strong>{h['manager']}</strong></td><td><strong>{h['score']:.1f}</strong></td><td>—</td><td>W</td></tr>"
        for h in combined_highs[:20]
    ) or "<tr><td colspan='6' style='text-align:center;color:var(--fdh-text-muted);'>No data yet.</td></tr>"
    streak_king  = max(active, key=lambda x: x.get("max_win_streak",0), default={})
    bust_king    = max(active, key=lambda x: x.get("max_lose_streak",0), default={})
    playoff_king = max(active, key=lambda x: x.get("playoff_apps",0), default={})
    champs_path  = _rD/"yahoo_champions.json"
    champ_rows   = ""
    if champs_path.exists():
        for c in sorted(_rj.loads(champs_path.read_text()), key=lambda x: x["season"]):
            champ_rows += (
                f"<tr><td><strong>{c['season']}</strong></td>"
                f"<td>🏆 <strong>{_yn(c['owner'])}</strong></td>"
                f"<td>{c.get('team','—')}</td><td>{c.get('points','—')}</td>"
                f"<td>{_yn(c.get('runner_up','—'))}</td><td>{c.get('ru_team','—')}</td>"
                f"<td>{c.get('ru_points','—')}</td><td>+{c.get('margin','—')}</td></tr>"
            )
    if not champ_rows:
        champ_rows = "<tr><td colspan='8' style='text-align:center;color:var(--fdh-text-muted);'>Champion data unavailable.</td></tr>"
    replacements = {
        "RECORD_HIGH_WEEK":            f"{high_week.get('score',0):.1f}" if high_week else "—",
        "RECORD_HIGH_WEEK_HOLDER":     high_week.get("manager","—"),
        "RECORD_HIGH_WEEK_CONTEXT":    f"Week {high_week.get('week','?')}, {high_week.get('season','?')} Season" if high_week else "",
        "RECORD_LOW_WEEK":             f"{low_week.get('score',0):.1f}" if low_week else "—",
        "RECORD_LOW_WEEK_HOLDER":      low_week.get("manager","—"),
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
        "WIN_STREAK_MAX":   streak_king.get("max_win_streak",0),
        "WIN_STREAK_HOLDER":streak_king.get("display_name","—"),
        "WIN_STREAK_CONTEXT":"",
        "LOSE_STREAK_MAX":   bust_king.get("max_lose_streak",0),
        "LOSE_STREAK_HOLDER":bust_king.get("display_name","—"),
        "LOSE_STREAK_CONTEXT":"",
        "PLAYOFF_STREAK_MAX":   playoff_king.get("playoff_apps",0),
        "PLAYOFF_STREAK_HOLDER":playoff_king.get("display_name","—"),
        "PLAYOFF_STREAK_CONTEXT":"Playoff appearances",
        "LAST_PLACE_STREAK":"—","LAST_PLACE_HOLDER":"—","LAST_PLACE_CONTEXT":"",
        "CHAMPIONS_TABLE_ROWS": champ_rows,
        "WEEKLY_HIGH_ROWS":     weekly_rows,
        "BUILD_TS": BUILD_TS, "YEAR": YEAR,
    }
    write_page("records.html", render("records.html", replacements))

'''

src = replace_fn(src, "gen_standings", NEW_STANDINGS)
src = replace_fn(src, "gen_trades",    NEW_TRADES)
src = replace_fn(src, "gen_draft",     NEW_DRAFT)
src = replace_fn(src, "gen_records",   NEW_RECORDS)
GS.write_text(src)
print("✅ generate_site.py patched.")
print("   Updated: gen_standings, gen_trades, gen_draft, gen_records")
print("\nNext: python3 scripts/generate_site.py")
