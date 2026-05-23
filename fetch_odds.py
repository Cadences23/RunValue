import os
import requests
import pandas as pd
from datetime import date
from dotenv import load_dotenv

# 1. Load the API key from .env
load_dotenv()
api_key = os.getenv("ODDS_API_KEY")

if not api_key:
    raise SystemExit("ERROR: ODDS_API_KEY not found in .env file")

# 2. Build the URl and fetch odds
today = date.today().isoformat()
url = (
    "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
    f"?apiKey={api_key}"
    "&regions=us"
    "&markets=h2h"
    "&oddsFormat=american"
)

response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"Requests remaining this month: {response.headers.get('x-requests-remaining')}")

if response.status_code != 200:
    print("Response body:", response.text)
    raise SystemExit("Request failed")

games = response.json()

# Filter to only today's games (in local date) to match games_*.csv
from datetime import datetime, timezone

local_today = date.today()
filtered_games = []
for g in games:
    # Commence_time looks like "2026-05,14T22:11:00Z"
    commence_dt_utc = datetime.fromisoformat(g["commence_time"].replace("Z", "+00:00"))
    commence_local_date = commence_dt_utc.astimezone().date()
    if commence_local_date == local_today:
        filtered_games.append(g)
print(f"Filtered {len(games)} total games down to {len(filtered_games)} for  today ({local_today})")
games = filtered_games

# 3. Flatten into rows (one row per game per bookmaker)
rows = []
for game in games:
    home_team = game["home_team"]
    away_team = game["away_team"]
    commence_time = game["commence_time"]

    for bookmaker in game["bookmakers"]:
        book_name = bookmaker["key"]
        # The h2h market has one outcome per team
        h2h_market = next(
            (m for m in bookmaker["markets"] if m["key"] == "h2h"),
            None,
        )
        if h2h_market is None:
            continue

        home_price = None
        away_price = None
        for outcome in h2h_market["outcomes"]:
            if outcome["name"] == home_team:
                home_price = outcome["price"]
            elif outcome["name"] == away_team:
                away_price = outcome["price"]

        rows.append({
            "date": today,
            "commence_time_utc": commence_time,
            "away_team": away_team,
            "home_team": home_team,
            "bookmaker": book_name,
            "away_ml": away_price,
            "home_ml": home_price,
        })

# 4. Save to CSV
df = pd.DataFrame(rows)
output_path = f"odds_{today}.csv"
df.to_csv(output_path, index=False)

print(f"Saved {len(df)} rows ({df["away_team"].nunique()} games x {df['bookmaker'].nunique()} bookmakers) to {output_path}")
print()
print(df.head(10))