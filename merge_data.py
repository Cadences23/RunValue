import sys
import pandas as pd
from datetime import date
from pathlib import Path

# 1. Figure out which date we're merging
#If you run: python merge_data.py 2026-5-12
# then sys.argv[1] is "2026-05-12" otherwise default to today
if len(sys.argv) > 1:
    target_date = sys.argv[1]
else:
    target_date = date.today().isoformat()

print(f"Merging data for {target_date}")

# 2. Build file paths and check that the inputs exist
games_path = Path(f"games_{target_date}.csv")
odds_path = Path(f"odds_{target_date}.csv")
output_path = Path(f"merged_{target_date}.csv")

if not games_path.exists():
    raise SystemExit(f"ERROR: {games_path} not found. Run save_games.py first.")
if not odds_path.exists():
    raise SystemExit(f"ERROR: {odds_path} not found. Run fetch_odds.py first.")

# 3. Read both CSVs
games_df = pd.read_csv(games_path)
odds_df = pd.read_csv(odds_path)

print(f"Loaded {len(games_df)} games and {len(odds_df)} odds rows")

# 4. Collapse odds: many bookmakers per game -> one row per game
odds_summary = (
    odds_df
    .groupby(["date", "away_team", "home_team"])
    .agg(
        away_ml_avg=("away_ml", "mean"),
        home_ml_avg=("home_ml", "mean"),
        away_ml_best=("away_ml", "max"),
        home_ml_best=("home_ml", "max"),
        num_books=("bookmaker", "count"),
    )
    .reset_index()
)

odds_summary["away_ml_avg"] = odds_summary["away_ml_avg"].round(1)
odds_summary["home_ml_avg"] = odds_summary["home_ml_avg"].round(1)

print(f"Collapsed odds to {len(odds_summary)} games")

# 5. Merge odds onto games
merged = pd.merge(
    games_df,
    odds_summary,
    on=["date", "away_team", "home_team"],
    how="left",
)

print(f"Merged table: {len(merged)} rows x {len(merged.columns)} columns")

# 6. Save
merged.to_csv(output_path, index=False)
print(f"Saved to {output_path}")

#7. Print a readable preview
preview_columns = [
    "away_team", "home_team",
    "away_wins", "away_losses",
    "home_wins", "home_losses",
    "away_ml_avg", "home_ml_avg",
    "away_ml_best", "home_ml_best",
    "num_books",
 ]
print()
print(merged[preview_columns].to_string(index=False))
