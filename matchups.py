import requests

league_id = "1378834732145455104"
week = 1

url = f"https://api.sleeper.app/v1/league/{league_id}/matchups/{week}"

response = requests.get(url)

matchups = response.json()

for team in matchups:
    print(
        f"Roster ID: {team['roster_id']}  | "
                             f"Points:{team['points']}"
                                          )

