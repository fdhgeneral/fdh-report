import requests

league_id = "1378834732145455104"

url = f"https://api.sleeper.app/v1/league/{1378834732145455104}"

response = requests.get(url)

print(response.json())
