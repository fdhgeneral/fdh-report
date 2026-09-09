def build_newsletter_html(
    opening_segment,
    top_performers,
    underperformers,
    injury_roundup,
    waiver_wire,
    buy_sell_hold,
    matchup_spotlight,
    start_sit,
    breakout_watch,
    roster_cleanup,
    standings,
    commissioners_corner,
    matchup_of_the_week,
    closing_note
):

    html_template = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Fantasy Die Hards Weekly Recap</title>
<style>
  body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 20px; }}
  h1, h2 {{ color: #222222; }}
  .section {{ margin-bottom: 20px; }}
  .footer {{ font-size: 12px; color: #777777; text-align: center; margin-top: 30px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }}
</style>
</head>
<body>
<div class="container">

<h1>Fantasy Die Hards Weekly Recap</h1>

<div class="section">
  <h2>Opening Segment</h2>
  {opening_segment}
</div>

<div class="section">
  <h2>Top Performers</h2>
  {top_performers}
</div>

<div class="section">
  <h2>Underperformers</h2>
  {underperformers}
</div>

<div class="section">
  <h2>Injury Roundup</h2>
  {injury_roundup}
</div>

<div class="section">
  <h2>Waiver Wire Targets</h2>
  {waiver_wire}
</div>

<div class="section">
  <h2>Buy / Sell / Hold</h2>
  {buy_sell_hold}
</div>

<div class="section">
  <h2>Matchup Spotlight</h2>
  {matchup_spotlight}
</div>

<div class="section">
  <h2>Start / Sit</h2>
  {start_sit}
</div>

<div class="section">
  <h2>Breakout Watch</h2>
  {breakout_watch}
</div>

<div class="section">
  <h2>Roster Cleanup</h2>
  {roster_cleanup}
</div>

<div class="section">
  <h2>League Standings</h2>
  {standings}
</div>

<div class="section">
  <h2>Commissioner's Corner</h2>
  {commissioners_corner}
</div>

<div class="section">
  <h2>Matchup of the Week</h2>
  {matchup_of_the_week}
</div>

<div class="footer">
  {closing_note}
</div>

</div>
</body>
</html>
"""

