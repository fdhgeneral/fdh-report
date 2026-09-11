import re, pathlib

p = pathlib.Path("docs/hof/rivalries.html")
html = p.read_text(encoding="utf-8")

# ── 1. Inject CSS colour fixes before </head> ─────────────────────────────
CSS = """<style>
/* H2H result card text colours */
.h2h-result-name  { color: rgba(255,255,255,.88) !important; }
.h2h-wins         { color: #fff !important; }
.h2h-wins.win     { color: var(--fdh-gold,  #f5a623) !important; }
.h2h-wins.lose    { color: rgba(255,255,255,.30) !important; }
.h2h-wins.tied    { color: #fff !important; }
.h2h-pts          { color: rgba(255,255,255,.65) !important; }
.h2h-center-vs    { color: var(--fdh-red-light, #ff6b6b) !important; }
.h2h-center-meta  { color: rgba(255,255,255,.65) !important; }
</style>"""

if "H2H result card text colours" not in html:
    html = html.replace("</head>", CSS + "\n</head>", 1)
    print("CSS colour fixes injected")
else:
    print("CSS already present")

# ── 2. Remove Complete Records / H2H Matrix section ───────────────────────
pattern = re.compile(
    r'<!--\s*Full H2H Matrix\s*-->.*?<div class="table-wrap">.*?</div>\s*</div>',
    re.DOTALL
)
html, n = pattern.subn("", html)
if n:
    print(f"H2H matrix removed ({n} block)")
else:
    pattern2 = re.compile(
        r'<div class="section-header"[^>]*>.*?Complete Records.*?</div>\s*'
        r'<p[^>]*>All-time.*?</p>\s*'
        r'<div[^>]*>.*?</div>\s*'
        r'<div class="table-wrap">.*?</div>\s*</div>',
        re.DOTALL
    )
    html, n = pattern2.subn("", html)
    print(f"H2H matrix removed via fallback ({n} block)" if n else "Matrix not found — check HTML")

p.write_text(html, encoding="utf-8")
print(f"Done: {p.stat().st_size:,} bytes")
print('Next: git add -A && git commit -m "fix H2H text colours, remove matrix table" && git push')
