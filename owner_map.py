import requests

league_id = "1378834732145455104"

users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"

users = requests.get(users_url).json()
rosters = requests.get(rosters_url).json()

user_lookup = {}

for user in users:
    user_lookup[user["user_id"]]= user["display_name"]

for roster in rosters:

    owner_id = roster["owner_id"]

    owner_name = user_lookup.get(
                         owner_id,
                         "Unknown Owner"

    )

    print(
        f"Roster{roster['roster_id']} -> {owner_name}"
    )


