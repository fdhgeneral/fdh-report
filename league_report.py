import json

# Load data files
import requests

league_id = "1378834732145455104"

users_url = f"https://api.sleeper.app/v1/league/{league_id}/users"
rosters_url = f"https://api.sleeper.app/v1/league/{league_id}/rosters"

users = requests.get(users_url).json()
rosters = requests.get(rosters_url).json()

#Create quick lookup of users by user_id
user_lookup = {
    user["user_id"]: user
    for user in users

}

league_report = []

for roster in rosters:

    owner_id = roster["owner_id"]

    user = user_lookup.get(owner_id, {})

    team = {
        "team_name": user.get(
            "metadata",
            {}
        ).get(
            "team_name",
            user.get("display_name", "Unknown")
        ),

        "owner": user.get(
            "display_name",
            "Unknown"
        ),

        "wins": roster["settings"].get(
            "wins",
            0
        ),

        "losses": roster["settings"].get(
            "losses",
            0
        ),

        "points_for": roster["settings"].get(
            "fpts",
            0
        )
    }
    
    league_report.append(team)

# Sort by standings
league_report.sort(
    key=lambda x: (
        x["wins"],
        x["points_for"]
    ),
    reverse=True
)

# Print standings
print("\n=== LEAGUE STANDINGS ===\n")

for rank, team in enumerate(
    league_report,
    start=1
):
    print(
        f"{rank}. {team['team_name']} "
        f"({team['owner']}) "
        f"{team['wins']}-{team['losses']} "
        f"PF: {team['points_for']}"
    )
all_zero = all(
    team["wins"] == 0 and
    team["losses"] == 0 and
    team["points_for"] == 0
    for team in league_report
)

if all_zero:
   print("\n PRESEASON: No games have been played yet.\n")

