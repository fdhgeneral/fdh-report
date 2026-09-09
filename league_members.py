import requests

league_id = "1378834732145455104"

users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"

users = requests.get(users_url).json()

for user in users:
    print(user["display_name"])

