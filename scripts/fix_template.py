#!/usr/bin/env python3
"""
fix_template.py — Writes the correct templates/rivalries.html directly to disk.
Run from ~/fantasy-newsletter/:
    python3 scripts/fix_template.py
"""
from pathlib import Path

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="description" content="FDH Rivalries — head-to-head records, heated matchups, and the fiercest feuds in Fantasy Die Hards history." />
  <title>Rivalries | FDH Hall of Fame</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=Inter:wght@400;500;600&family=Fira+Code&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="assets/css/fdh.css" />
  <style>
    /* ── Existing rivalry card styles ── */
    .rivalry-card {
      background: var(--fdh-white);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-md);
      overflow: hidden;
      transition: transform .2s ease, box-shadow .2s ease;
    }
    .rivalry-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); }
    .rivalry-card__header {
      background: linear-gradient(135deg, var(--fdh-slate) 0%, var(--fdh-slate-mid) 100%);
      padding: 1.25rem;
      display: flex; align-items: center; justify-content: space-between;
      border-bottom: 3px solid var(--fdh-red);
    }
    .rivalry-card__manager {
      font-family: var(--font-display);
      font-size: 1.1rem;
      color: var(--fdh-white);
      text-align: center;
      flex: 1;
    }
    .rivalry-card__vs {
      font-family: var(--font-display);
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--fdh-red-light);
      padding: 0 1rem;
    }
    .rivalry-card__score {
      display: flex; align-items: center; justify-content: space-around;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid rgba(0,0,0,.07);
    }
    .rivalry-score__val {
      font-family: var(--font-display);
      font-size: 2rem;
      font-weight: 700;
    }
    .rivalry-score__val.leader { color: var(--fdh-red); }
    .rivalry-score__val.trailer { color: var(--fdh-slate-muted); }
    .rivalry-score__dash { font-size: 1.4rem; color: #ccc; }
    .rivalry-card__meta {
      padding: .75rem 1.25rem;
      display: flex; gap: 1rem; flex-wrap: wrap;
      font-size: .8rem; color: var(--fdh-text-muted);
    }
    .rivalry-heat { display: flex; gap: 3px; align-items: center; margin-top: .25rem; }
    .heat-dot { width: 10px; height: 10px; border-radius: 50%; }
    .heat-high { background: var(--fdh-red); }
    .heat-med  { background: var(--fdh-gold); }
    .heat-low  { background: #ddd; }

    /* ── H2H Lookup Widget ── */
    #h2h-lookup-wrap {
      background: var(--fdh-white);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-md);
      padding: 2rem;
      margin-bottom: 3rem;
    }
    .h2h-selectors {
      display: flex;
      align-items: flex-end;
      gap: 1.5rem;
      flex-wrap: wrap;
      margin-bottom: 1.75rem;
    }
    .h2h-selector-side {
      flex: 1;
      min-width: 180px;
    }
    .h2h-selector-label {
      display: block;
      font-family: var(--font-display);
      font-size: .75rem;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--fdh-text-muted);
      margin-bottom: .4rem;
    }
    .h2h-select {
      width: 100%;
      padding: .65rem 1rem;
      font-size: 1rem;
      font-family: var(--font-body);
      border: 2px solid #ddd;
      border-radius: var(--radius-md);
      background: var(--fdh-bg);
      color: var(--fdh-text);
      cursor: pointer;
      transition: border-color .2s;
    }
    .h2h-select:focus { outline: none; border-color: var(--fdh-red); }
    .h2h-vs-badge {
      font-family: var(--font-display);
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--fdh-red);
      padding-bottom: .5rem;
      flex-shrink: 0;
    }
    .h2h-hint {
      text-align: center;
      color: var(--fdh-text-muted);
      padding: 2rem 0;
      font-size: .95rem;
    }

    /* ── H2H Result Card (rendered by JS) ── */
    .h2h-result-card {
      border-radius: var(--radius-md);
      overflow: hidden;
      border: 1px solid rgba(0,0,0,.08);
    }
    .h2h-result-header {
      display: flex;
      background: linear-gradient(135deg, var(--fdh-slate) 0%, var(--fdh-slate-mid) 100%);
      border-bottom: 3px solid var(--fdh-red);
    }
    .h2h-result-side {
      flex: 1;
      padding: 1.5rem 1.25rem;
      text-align: center;
    }
    .h2h-result-center {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 1rem;
      border-left: 1px solid rgba(255,255,255,.1);
      border-right: 1px solid rgba(255,255,255,.1);
      min-width: 110px;
    }
    .h2h-result-name {
      font-family: var(--font-display);
      font-size: 1rem;
      color: rgba(255,255,255,.8);
      margin-bottom: .4rem;
    }
    .h2h-result-wins {
      font-family: var(--font-display);
      font-size: 3rem;
      font-weight: 700;
      line-height: 1;
      margin-bottom: .3rem;
    }
    .h2h-result-wins.leader  { color: var(--fdh-gold); }
    .h2h-result-wins.trailer { color: rgba(255,255,255,.4); }
    .h2h-result-wins:not(.leader):not(.trailer) { color: #fff; }
    .h2h-result-sub {
      font-size: .8rem;
      color: rgba(255,255,255,.6);
    }
    .h2h-result-vs {
      font-family: var(--font-display);
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--fdh-red-light);
    }
    .h2h-result-meta {
      font-size: .78rem;
      color: rgba(255,255,255,.65);
      margin-top: .2rem;
    }
    .h2h-result-facts {
      padding: 1rem 1.25rem;
      background: var(--fdh-bg);
      border-bottom: 1px solid rgba(0,0,0,.06);
      display: flex;
      flex-wrap: wrap;
      gap: .5rem .75rem;
    }
    .h2h-fact {
      font-size: .85rem;
      color: var(--fdh-text);
      flex: 1 1 280px;
    }
    .h2h-season-breakdown {
      padding: 1rem 1.25rem 1.25rem;
      background: var(--fdh-white);
    }
    .h2h-breakdown-title {
      font-family: var(--font-display);
      font-size: .75rem;
      letter-spacing: .08em;
      text-transform: uppercase;
      color: var(--fdh-text-muted);
      margin-bottom: .6rem;
    }
    .h2h-breakdown-table {
      width: 100%;
      border-collapse: collapse;
      font-size: .85rem;
    }
    .h2h-breakdown-table th {
      text-align: left;
      padding: .3rem .5rem;
      border-bottom: 2px solid var(--fdh-red);
      font-family: var(--font-display);
      font-size: .75rem;
      text-transform: uppercase;
      letter-spacing: .05em;
      color: var(--fdh-text-muted);
    }
    .h2h-breakdown-table td {
      padding: .35rem .5rem;
      border-bottom: 1px solid rgba(0,0,0,.05);
    }
    .h2h-breakdown-table tr:last-child td { border-bottom: none; }

    @media (max-width: 600px) {
      .h2h-selectors { flex-direction: column; gap: .75rem; }
      .h2h-vs-badge { text-align: center; padding-bottom: 0; }
      .h2h-result-header { flex-direction: column; }
      .h2h-result-center { flex-direction: row; gap: 1rem; border: none;
        border-top: 1px solid rgba(255,255,255,.1);
        border-bottom: 1px solid rgba(255,255,255,.1); }
    }
  </style>
</head>
<body>

<nav class="nav">
  <div class="container nav__inner">
    <a href="index.html" class="nav__logo"><span>FDH</span> Hall of Fame</a>
    <button class="nav__burger" aria-label="Toggle menu"><span></span><span></span><span></span></button>
    <div class="nav__links">
      <a href="index.html"     class="nav__link">Home</a>
      <a href="hof.html"       class="nav__link">Hall of Fame</a>
      <a href="standings.html" class="nav__link">Standings</a>
      <a href="rivalries.html" class="nav__link active">Rivalries</a>
      <a href="trades.html"    class="nav__link">Trades</a>
      <a href="draft.html"     class="nav__link">Draft History</a>
      <a href="records.html"   class="nav__link">Records</a>
    </div>
  </div>
</nav>

<section class="hero" style="padding:3rem 0 2.5rem;">
  <div class="container" style="position:relative;z-index:1;">
    <div class="hero__eyebrow">Head-to-Head History</div>
    <h1 class="hero__title">FDH <span>Rivalries</span></h1>
    <p class="hero__sub">Every matchup. Every grudge. Every comeback. The numbers don't lie.</p>
    <div class="hero__meta">
      <div class="hero__stat">
        <span class="hero__stat-num" data-counter data-target="{{TOTAL_H2H_MATCHUPS}}">{{TOTAL_H2H_MATCHUPS}}</span>
        <span class="hero__stat-label">Total Matchups</span>
      </div>
      <div class="hero__stat">
        <span class="hero__stat-num" data-counter data-target="{{CLOSEST_RIVALRY_GAMES}}">{{CLOSEST_RIVALRY_GAMES}}</span>
        <span class="hero__stat-label">Most Meetings</span>
      </div>
      <div class="hero__stat">
        <span class="hero__stat-num">{{MOST_DOMINANT_RIVALRY_PCT}}%</span>
        <span class="hero__stat-label">Most Dominant H2H</span>
      </div>
    </div>
  </div>
</section>

<div class="container" style="margin-top:2rem;">
  <div class="last-updated">
    <div class="last-updated__dot"></div>
    <span>Synced from Sleeper: <strong id="last-updated-ts" data-ts="{{BUILD_TS}}">{{BUILD_TS}}</strong></span>
  </div>

  <!-- ── H2H Interactive Lookup ── -->
  {{H2H_LOOKUP_SECTION}}

  <!-- ── Top Rivalries ── -->
  <div class="section-header">
    <span class="section-header__eyebrow">Fiercest Feuds</span>
    <h2>Top Rivalries</h2>
    <div class="section-header__line"></div>
  </div>
  <p style="color:var(--fdh-text-muted); margin-bottom:1.5rem;">Ranked by rivalry score — a blend of total meetings, win margin closeness, and playoff stakes.</p>
  <div class="grid-2" style="margin-bottom:3rem;">
    {{TOP_RIVALRY_CARDS_FULL}}
  </div>

  <!-- ── Full H2H Matrix ── -->
  <div class="section-header" style="margin-top:1rem;">
    <span class="section-header__eyebrow">Complete Records</span>
    <h2>Head-to-Head Matrix</h2>
    <div class="section-header__line"></div>
  </div>
  <p style="color:var(--fdh-text-muted); margin-bottom:1rem; font-size:.88rem;">
    Numbers show W-L record. Click a column header to sort. Green = winning record, red = losing record.
  </p>
  <div style="margin-bottom:1rem;">
    <input id="h2h-search" type="search" placeholder="Filter by manager name…" data-filter-table="h2h-table"
      style="padding:.5rem 1rem; border:2px solid #ddd; border-radius:4px; font-size:.9rem; width:260px;" />
  </div>
  <div class="table-wrap">
    <table id="h2h-table" class="fdh-table" data-sortable>
      <thead>
        <tr>
          <th data-sort="0">Manager</th>
          <th data-sort="1">Opponent</th>
          <th data-sort="2">W</th>
          <th data-sort="3">L</th>
          <th data-sort="4">Win %</th>
          <th data-sort="5">Meetings</th>
          <th data-sort="6">Avg Margin</th>
          <th data-sort="7">Playoff Meetings</th>
          <th data-sort="8">Last Result</th>
        </tr>
      </thead>
      <tbody>
        {{H2H_TABLE_ROWS}}
      </tbody>
    </table>
  </div>
</div>

<div style="padding:3rem 0;"></div>
<footer class="footer">
  <div class="container">
    <div class="footer__logo"><span>FDH</span> Hall of Fame</div>
    <div class="footer__links">
      <a href="index.html" class="footer__link">Home</a>
      <a href="hof.html" class="footer__link">Hall of Fame</a>
      <a href="standings.html" class="footer__link">Standings</a>
      <a href="rivalries.html" class="footer__link">Rivalries</a>
      <a href="trades.html" class="footer__link">Trades</a>
      <a href="draft.html" class="footer__link">Draft History</a>
      <a href="records.html" class="footer__link">Records</a>
    </div>
    <p class="footer__copy">&copy; {{YEAR}} Fantasy Die Hards.</p>
    <p class="footer__build">Auto-generated &middot; Build {{BUILD_TS}}</p>
  </div>
</footer>

<!-- Data blob injected by gen_rivalries() -->
{{H2H_SCRIPT}}

<!-- H2H Lookup interactive JS -->
<script>
(function () {
  var selA = document.getElementById('mgr-a');
  var selB = document.getElementById('mgr-b');
  var res  = document.getElementById('h2h-result');
  if (!selA || !selB || !res) return;

  var H2H = window.FDH_H2H || {};

  function fmt(n) { return Number(n).toFixed(1); }

  function lookup() {
    var a = selA.value, b = selB.value;
    if (!a || !b || a === b) {
      res.innerHTML = '<p class="h2h-hint">Select two different managers to see their head-to-head record.</p>';
      return;
    }
    var key = [a, b].sort().join('|');
    var d   = H2H[key];
    if (!d) {
      res.innerHTML = '<p class="h2h-hint">No matchups found between these two managers.</p>';
      return;
    }

    var flip = (d.a !== a);
    var wA   = flip ? d.wins_b : d.wins_a;
    var wB   = flip ? d.wins_a : d.wins_b;
    var pfA  = flip ? d.pf_b   : d.pf_a;
    var pfB  = flip ? d.pf_a   : d.pf_b;
    var pgA  = flip ? d.ppg_b  : d.ppg_a;
    var pgB  = flip ? d.ppg_a  : d.ppg_b;
    var clA  = wA > wB ? 'leader' : (wA < wB ? 'trailer' : '');
    var clB  = wB > wA ? 'leader' : (wB < wA ? 'trailer' : '');

    var bw = d.biggest_win;
    var cl = d.closest_game;
    var sk = d.streak;

    var sRows = '';
    var syrs  = Object.keys(d.seasons).sort();
    for (var i = 0; i < syrs.length; i++) {
      var yr = syrs[i];
      var s  = d.seasons[yr];
      var wa = flip ? s.wins_b : s.wins_a;
      var wb = flip ? s.wins_a : s.wins_b;
      sRows += '<tr>'
        + '<td>' + yr + '</td>'
        + '<td style="font-weight:600">' + wa + '\u2013' + wb + '</td>'
        + '<td style="color:var(--fdh-text-muted)">' + s.meetings + (s.meetings !== 1 ? ' games' : ' game') + '</td>'
        + '</tr>';
    }

    var playoffLine = d.playoff_meetings > 0
      ? '<div class="h2h-result-meta">&#9889; ' + d.playoff_meetings + ' playoff meeting' + (d.playoff_meetings > 1 ? 's' : '') + '</div>'
      : '';

    var scoreContext = (bw.score_w !== undefined && bw.score_l !== undefined)
      ? ' (' + fmt(bw.score_w) + '\u2013' + fmt(bw.score_l) + ', ' + bw.context + ')'
      : ' (' + bw.context + ')';

    res.innerHTML =
      '<div class="h2h-result-card">'
      + '<div class="h2h-result-header">'
        + '<div class="h2h-result-side">'
          + '<div class="h2h-result-name">
