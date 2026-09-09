#!/bin/bash
cd /home/fendrbendr9/fantasy-newsletter

export FDH_TEST_MODE=false
export SLEEPER_LEAGUE_ID=1378834732145455104
export SMTP_USER=fendrbendr9@gmail.com
export SMTP_PASS=cwmeggxyvooexdyl
export FDH_FROM=fendrbendr9@gmail.com
export FDH_RECIPIENTS=fendrbendr9@outlook.com,gdmerkt3@yahoo.com,carlosggggggg@gmail.com

python3 send_newsletter.py >> newsletter.log 2>&1
