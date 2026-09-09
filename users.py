import requests

league_id = "1378834732145455104"

url = f"https://api.sleeper.app/v1/league/{league_id}/users"

response = requests.get(url)

users = response.json()

for user in users:
    print(f"Team Owner:{user['display_name']}")










