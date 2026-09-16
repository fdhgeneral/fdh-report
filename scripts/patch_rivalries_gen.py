#!/usr/bin/env python3
"""
patch_rivalries_gen.py
Rewrites gen_rivalries() in generate_site.py to use rivalries_h2h.json.
Run from repo root: python3 scripts/patch_rivalries_gen.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
GS   = ROOT / "scripts" / "generate_site.py"
src  = GS.read_text()

def replace_fn(source, fn_name, new_body):
    pattern = rf'(^def {fn_name}\(.*?)(?=^def |\Z|^# ── Main)'
    return re.sub(pattern, new_body, source, flags=re.DOTALL | re.MULTILINE)

NEW_GEN_RIVALRIES = r'''def gen_rivalries(stats: dict):
    import json as _rj
    from pathlib import Path as _RP
    _D = _RP('_data')

    h2h_path = _D / 'rivalries_h2h.json'
    if not h2h_path.exists():
        print('  WARNING: rivalries_h2h.json missing -- run compute_rivalries.py first')
        write_page('rivalries.html', render('rivalries.html', {
            'TOTAL_H2H_MATCHUPS': '0', 'CLOSEST_RIVALRY_GAMES': '0',
            'MOST_DOMINANT_RIVALRY_PCT': '0', 'H2H_LOOKUP_SECTION': '',
            'TOP_RIVALRY_CARDS_FULL': '', 'H2H_TABLE_ROWS': '',
            'H2H_SCRIPT': '', 'BUILD_TS': BUILD_TS, 'YEAR': YEAR,
        }))
        return

    h2h   = _rj.loads(h2h_path.read_text())
    pairs = h2h.get('pairs', {})
    active  = h2h.get('active_managers', [])
    former  = h2h.get('former_managers', [])
    top10   = h2h.get('top_rivalries', [])
    total   = h2h.get('total_matchups', 0)

    # ── Manager dropdown options ──────────────────────────────────────────────
    blank    = '<option value="">-- Select Manager --</option>'
    act_opts = ''.join('<option value="' + m + '">' + m + '</option>' for m in active)
    fmr_opts = ''.join('<option value="' + m + '">' + m + '</option>' for m in former)
    mgr_opts = (blank
        + ('<optgroup label="Active Members">' + act_opts + '</optgroup>' if act_opts else '')
        + ('<optgroup label="Former Members">' + fmr_opts + '</optgroup>' if fmr_opts else ''))

    # ── H2H Lookup widget HTML ────────────────────────────────────────────────
    h2h_section = (
        '<div class="section-header" style="margin-top:0;">'
        '<span class="section-header__eyebrow">Interactive Lookup</span>'
        '<h2>Head-to-Head Matchup</h2>'
        '<div class="section-header__line"></div>'
        '</div>'
        '<div id="h2h-lookup-wrap">'
        '<div class="h2h-selectors">'
        '<div class="h2h-selector-side">'
        '<label class="h2h-selector-label">Manager</label>'
        '<select id="mgr-a" class="h2h-select">' + mgr_opts + '</select>'
        '</div>'
        '<div class="h2h-vs-badge">VS</div>'
        '<div class="h2h-selector-side">'
        '<label class="h2h-selector-label">Opponent</label>'
        '<select id="mgr-b" class="h2h-select">' + mgr_opts + '</select>'
        '</div>'
        '</div>'
        '<div id="h2h-result">'
        '<p class="h2h-hint">Select two managers above to see their '
        'full head-to-head history across all 6 seasons.</p>'
        '</div>'
        '</div>'
    )

    # ── Top rivalry cards ─────────────────────────────────────────────────────
    def _dots(score):
        lvl = 'high' if score >= 80 else ('med' if score >= 50 else 'low')
        n   = 3 if score >= 80 else (2 if score >= 50 else 1)
        return (
            ''.join('<span class="heat-dot heat-' + lvl + '"></span>' for _ in range(n))
            + ''.join('<span class="heat-dot heat-low"></span>' for _ in range(3 - n))
        )

    top_cards = ''
    for r in top10[:6]:
        wa = r['wins_a']; wb = r['wins_b']
        ca = 'leader' if wa > wb else ('trailer' if wa < wb else '')
        cb = 'leader' if wb > wa else ('trailer' if wb < wa else '')
        po = ('<span>&#9889; ' + str(r['playoff_meetings']) + ' playoff</span>') if r['playoff_meetings'] > 0 else ''
        top_cards += (
            '<div class="rivalry-card">'
            '<div class="rivalry-card__header">'
            '<div class="rivalry-card__manager" style="text-align:left;">' + r['a'] + '</div>'
            '<div class="rivalry-card__vs">VS</div>'
            '<div class="rivalry-card__manager" style="text-align:right;">' + r['b'] + '</div>'
            '</div>'
            '<div class="rivalry-card__score">'
            '<span class="rivalry-score__val ' + ca + '">' + str(wa) + '</span>'
            '<span class="rivalry-score__dash">&mdash;</span>'
            '<span class="rivalry-score__val ' + cb + '">' + str(wb) + '</span>'
            '</div>'
            '<div class="rivalry-card__meta">'
            '<span>&#9876; ' + str(r['meetings']) + ' meetings</span>'
            '<span>&#128197; 2020&ndash;2025</span>'
            + po
            + '<span>&#128293; ' + r['streak']['holder'] + ' ' + str(r['streak']['count']) + 'W streak</span>'
            '</div>'
            '<div class="rivalry-card__meta">'
            '<div class="rivalry-heat">' + _dots(r['rivalry_score']) + '</div>'
            '<span>Rivalry Score: ' + str(r['rivalry_score']) + '</span>'
            '</div>'
            '</div>'
        )

    # ── H2H matrix table rows ─────────────────────────────────────────────────
    h2h_rows = ''
    for pk, r in sorted(pairs.items()):
        for side in [True, False]:
            mgr  = r['a'] if side else r['b']
            opp  = r['b'] if side else r['a']
            w    = r['wins_a'] if side else r['wins_b']
            l    = r['wins_b'] if side else r['wins_a']
            n    = r['meetings']
            wpct = (str(round(w / n * 100)) + '%') if n > 0 else '&mdash;'
            last = 'W' if r['streak']['holder'] == mgr else 'L'
            h2h_rows += (
                '<tr><td><strong>' + mgr + '</strong></td><td>' + opp + '</td>'
                '<td>' + str(w) + '</td><td>' + str(l) + '</td><td>' + wpct + '</td>'
                '<td>' + str(n) + '</td><td>&mdash;</td>'
                '<td>' + str(r['playoff_meetings']) + '</td><td>' + last + '</td></tr>'
            )

    # ── Hero stats ────────────────────────────────────────────────────────────
    most_m  = max((r['meetings'] for r in pairs.values()), default=0)
    dom_r   = max(pairs.values(),
                  key=lambda x: max(x['wins_a'], x['wins_b']) / max(x['meetings'], 1),
                  default={})
    dom_pct = (str(round(max(dom_r.get('wins_a', 0), dom_r.get('wins_b', 0))
               / max(dom_r.get('meetings', 1), 1) * 100))
               if dom_r else '0')

    # ── Slim JSON data blob for embedded script ───────────────────────────────
    slim = {}
    for pk, r in pairs.items():
        slim[pk] = {
            'a': r['a'], 'b': r['b'],
            'wins_a': r['wins_a'], 'wins_b': r['wins_b'],
            'pf_a': r['pf_a'], 'pf_b': r['pf_b'],
            'ppg_a': r['ppg_a'], 'ppg_b': r['ppg_b'],
            'meetings': r['meetings'],
            'playoff_meetings': r['playoff_meetings'],
            'biggest_win': r['biggest_win'],
            'closest_game': r['closest_game'],
            'streak': r['streak'],
            'seasons': r['seasons'],
        }
    h2h_json    = _rj.dumps(slim, separators=(',', ':'))
    h2h_script  = '<script>window.FDH_H2H=' + h2h_json + ';</script>'

    replacements = {
        'TOTAL_H2H_MATCHUPS':        total,
        'CLOSEST_RIVALRY_GAMES':     most_m,
        'MOST_DOMINANT_RIVALRY_PCT': dom_pct,
        'H2H_LOOKUP_SECTION':        h2h_section,
        'TOP_RIVALRY_CARDS_FULL':    top_cards or '<p style="color:var(--fdh-text-muted)">No rivalry data yet.</p>',
        'H2H_TABLE_ROWS':            h2h_rows or '<tr><td colspan="9" style="text-align:center;">No data yet.</td></tr>',
        'H2H_SCRIPT':                h2h_script,
        'BUILD_TS': BUILD_TS, 'YEAR': YEAR,
    }
    write_page('rivalries.html', render('rivalries.html', replacements))

'''

src = replace_fn(src, "gen_rivalries", NEW_GEN_RIVALRIES)
GS.write_text(src)
print("✅ gen_rivalries() patched in generate_site.py")
print("   H2H data embedded as window.FDH_H2H — JS logic lives in template")
print("\nNext: python3 scripts/generate_site.py")
