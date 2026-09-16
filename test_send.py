from send_newsletter import send_email

send_email(
    html_body="<h2>FDH Newsletter Test</h2><p>Checking the new logo.</p>",
    subject="FDH Logo Test",
    recipients=["fendrbendr9@outlook.com"],
    week=1,
    logo_path="assets/fdh_logo.png"
)

