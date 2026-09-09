import requests

league_id = "1378834732145455104"

users = requests.get(
    f"https://api.sleeper.app/v1/league/{league_id}/users"
).json()

print("\n FDH NEWSLETTER\n")

print("PRESEASON REPORT\n")

print("League Members:")

for user in users:
    print(f"-{user['display_name']}")

print("\nNo games have been played yet.")

