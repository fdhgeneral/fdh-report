html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FDH Weekly Recap - {week_label}</title>

<style>
  body {{
    margin: 0;
    padding: 0;
    background: #f5f5f5;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}

  .newsletter-wrapper {{
    max-width: 800px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }}

  .header {{
    background: linear-gradient(135deg, #b22222, #222831);
    color: #ffffff;
    padding: 24px 32px;
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .header-logo {{
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: rgba(0,0,0,0.25);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 22px;
  }}

  .header-text-main {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}

  .header-text-sub {{
    font-size: 14px;
    opacity: 0.85;
  }}

  .content {{
    padding: 24px 32px 32px;
  }}

  .section {{
    margin-bottom: 28px;
  }}

  .section-title {{
    font-size: 18px;
    font-weight: 700;
    color: #222831;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .section-title-pill {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    background: #f6c453;
    color: #222831;
    padding: 2px 8px;
    border-radius: 999px;
  }}

  .section-subtitle {{
    font-size: 13px;
    color: #666666;
    margin-bottom: 12px;
  }}

  .intro-text {{
    font-size: 14px;
    color: #333333;
    line-height: 1.5;
  }}

  .highlight-card {{
    border-radius: 10px;
    background: #fff7e6;
    border: 1px solid #f6c453;
    padding: 16px 18px;
    margin-top: 8px;
  }}

  .highlight-title {{
    font-size: 15px;
    font-weight: 600;
    color: #222831;
    margin-bottom: 6px;
  }}

  .highlight-body {{
    font-size: 13px;
    color: #444444;
    line-height: 1.5;
  }}

  .awards-grid {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }}

  .award-card {{
    border-radius: 10px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 10px 12px;
  }}

  .award-label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: #b22222;
    margin-bottom: 4px;
  }}

  .award-team {{
    font-size: 14px;
    font-weight: 600;
    color: #222831;
  }}

  .award-detail {{
    font-size: 12px;
    color: #555555;
    margin-top: 2px;
  }}

  .standings-wrapper {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }}

  .division-card {{
    border-radius: 10px;
    background: #f8f9fa;
    border: 1px solid #e1e4ea;
    overflow: hidden;
  }}

  .division-header {{
    background: #222831;
    color: #ffffff;
    padding: 8px 10px;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .division-header-pill {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    background: #b22222;
    padding: 2px 6px;
    border-radius: 999px;
  }}

  .division-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}

  .division-table thead {{
    background: #e9edf5;
  }}

  .division-table th,
  .division-table td {{
    padding: 6px 8px;
    text-align: left;
    border-bottom: 1px solid #e1e4ea;
  }}

  .division-table th {{
    font-weight: 600;
    color: #333333;
  }}

  .division-table tr:last-child td {{
    border-bottom: none;
  }}

  .team-name-cell {{
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .team-avatar {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #d1d5db;
    overflow: hidden;
  }}

  .team-avatar img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
  }}

  .power-rank-list {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}

  .power-rank-item {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    margin-bottom: 6px;
    font-size: 13px;
  }}

  .power-rank-left {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .power-rank-position {{
    width: 22px;
    height: 22px;
    border-radius: 999px;
    background: #b22222;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: 600;
  }}

  .power-rank-team {{
    font-weight: 600;
    color: #222831;
  }}

  .power-rank-movement {{
    font-size: 11px;
    color: #16a34a;
  }}

  .power-rank-comment {{
    font-size: 11px;
    color: #555555;
    max-width: 55%;
    text-align: right;
  }}

  .footer {{
    padding: 14px 32px 18px;
    font-size: 11px;
    color: #777777;
    background: #f5f5f5;
    text-align: center;
  }}

  .footer-cta {{
    font-size: 11px;
    color: #b22222;
    margin-top: 4px;
  }}

  @media only screen and (max-width: 600px) {{
    .newsletter-wrapper {{
      border-radius: 0;
    }}
    .content {{
      padding: 18px 16px 24px;
    }}
    .standings-wrapper {{
      grid-template-columns: 1fr;
    }}
    .awards-grid {{
      grid-template-columns: 1fr;
    }}
  }}
</style>
</head>

<body>
  <div class="newsletter-wrapper">

    <div class="header">
      <div class="header-logo">FDH</div>
      <div>
        <div class="header-text-main">Fantasy Die Hards Weekly Recap</div>
        <div class="header-text-sub">{week_label}</div>
      </div>
    </div>

    <div class="content">

      <div class="section">
        <div class="section-title">
          <span>Opening Kickoff</span>
          <span class="section-title-pill">Commissioner’s Note</span>
        </div>
        <div class="section-subtitle">Quick hits, vibes, and storylines from this week in FDH.</div>
        <div class="intro-text">{intro_text}</div>
      </div>

      <div class="section">
        <div class="section-title">
          <span>Game of the Week</span>
          <span class="section-title-pill">Spotlight</span>
        </div>
        <div class="section-subtitle">The matchup everyone was watching.</div>
        <div class="highlight-card">
          <div class="highlight-title">{gotw_title}</div>
          <div class="highlight-body">{gotw_body}</div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">
          <span>Weekly Awards</span>
          <span class="section-title-pill">Hardware</span>
        </div>
        <div class="section-subtitle">Who showed up, who disappeared, and who stole the headlines.</div>
        <div class="awards-grid">
          {awards_html}
        </div>
      </div>

      <div class="section">
        <div class="section-title">
          <span>Division Standings</span>
          <span class="section-title-pill">Table Talk</span>
        </div>
        <div class="section-subtitle">Where everyone sits after this week’s chaos.</div>
        <div class="standings-wrapper">
          {standings_html}
        </div>
      </div>

      <div class="section">
        <div class="section-title">
          <span>Power Rankings</span>
          <span class="section-title-pill">Heat Check</span>
        </div>
        <div class="section-subtitle">Who’s rising, who’s falling, and who’s pretending.</div>
        <ul class="power-rank-list">
          {power_rankings_html}
        </ul>
      </div>

    </div>

    <div class="footer">
      Sent automatically by the FDH Weekly Recap engine.
      <div class="footer-cta">Reply with your own trash talk or hot takes to be featured next week.</div>
    </div>

  </div>
</body>
</html>
"""
