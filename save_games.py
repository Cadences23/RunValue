import requests
import pandas as pd
from datetime import date

# 1. Fetch today's games from the MLB Stats API
today = date.today() .isoformat()
url = f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={today}"

response = requests.get(url)
data = response.json()

games = data["dates"][0]["games"] if data["dates"] else []

# 2. Pull out fields we care about into a list of dictionaries
rows = []
for game in games:
    away = game["teams"]["away"]
    home = game["teams"]["home"]
    rows.append({
        "date": today,
        "game_pk": game["gamePk"],
        "game_time_utc": game["gameDate"],
        "status": game["status"]["detailedState"],
        "away_team": away["team"]["name"],
        "away_wins": away["leagueRecord"]["wins"],
        "away_losses": away["leagueRecord"]["losses"],
        "away_pct": float(away["leagueRecord"]["pct"]),
        "away_score": away.get("score"),
        "home_team": home["team"]["name"],
        "home_wins": home["leagueRecord"]["wins"],
        "home_losses": home["leagueRecord"]["losses"],
        "home_pct": float(home["leagueRecord"]["pct"]),
        "home_score": home.get("score"),
        "venue": game["venue"]["name"],

    })

# 3. Convert to a pandas DataFrame
df = pd.DataFrame(rows)

# 4. Save to a CSV named with today's date
output_path = f"games_{today}.csv"
df.to_csv(output_path, index=False)

# 5. Confirm
print(f"Saved {len(df)} games to {output_path}")
print()
print(df)