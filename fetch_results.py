"""
Fetch Completed MLB game results for a given date and append to results.csv.
Indempotent: re-running for the same date will refresh those row, not duplicate
"""
import sys
import requests
import pandas as pd
from datetime import date, timedelta
from pathlib import Path


# 1. Figure out which date to fetch results for.
# Default: yesterday (since todays games usually arent finished yet).
if len(sys.argv) > 1:
    target_date = sys.argv[1]
else:
    target_date = (date.today() - timedelta(days=1)).isoformat()

print(f"Fetching reults for {target_date}")

# 2. Hit the MLB Stats API
url =f"https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&date={target_date}"
response = requests.get(url)
data = response.json()

games = data["dates"][0]["games"] if data["dates"] else[]
print(f"API returned {len(games)} games for {target_date}")

# 3. Keep only finished games and extract results
rows = []
for game in games:
    status = game["status"]["detailedState"]
    if status != "Final":
        continue #skip games still in progress, postposted, etc.

    away = game["teams"]["away"]
    home = game["teams"]["home"]
    home_won = home.get("isWinner", False)

    rows.append({
        "date": target_date,
        "game_pk" : game["gamePk"],
        "away_team": away["team"]["name"],
        "home_team" : home["team"]["name"],
        "away_score": away.get("score"),
        "home_score": home.get("score"),
        "home_won": home_won,
        "winner": home["team"]["name"] if home_won else away["team"]["name"],
        "status": status,
    })

results_df = pd.DataFrame(rows)
print(f"Found {len(results_df)} completed games")

if len(results_df) == 0:
    raise SystemExit ("No completed games to save. Exiting")

# 4. Append to growing results log, idempotently
log_path = Path("results.csv")
if log_path.exists():
    existing = pd.read_csv(log_path)
    mask = existing["date"] == target_date
    rows_removed = mask.sum()
    if rows_removed > 0:
        print(f"Removing {rows_removed} existing rows for {target_date}")
    existing = existing[~mask]
    combined = pd.concat([existing, results_df], ignore_index=True)
else:
    combined = results_df

combined.to_csv(log_path, index=False)
print(f"Saved {len(results_df)} results to {log_path} (total rows: {len(combined)})")
print()
print(results_df[["away_team", "home_team", "away_score", "home_score", "winner"]].to_string(index=False))