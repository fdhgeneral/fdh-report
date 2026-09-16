import requests

league_id = "1378834732145455104"

url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"

response = requests.get(url)

rosters = response.json()

for roster in rosters: 
    print(f"Roster ID:{roster['roster_id']}")

    if "settings" in roster:
        print(f"Wins:{roster['settings'].get('wins',0)}")

        print(f"Losses: {roster['settings'].get('losses',0)}")

    print("-------------------")





