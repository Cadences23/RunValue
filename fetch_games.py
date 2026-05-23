import requests
from datetime import date
today = date.today() .isoformat()
url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}"

response = requests.get(url)
data = response.json()

games = data["dates"][0]["games"] if data["dates"] else []

print(f"MLB games on {today}: {len(games)} game(s)")
print("-" * 40)

for game in games:
    away = game["teams"]["away"]["team"]["name"]
    home = game["teams"]["home"]["team"]["name"]
    game_time = game["gameDate"]
    print(f"{away} @ {home}   ({game_time})")