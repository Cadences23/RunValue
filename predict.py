"""
v1 mode: predict home win probability from team records alone.
home_prob = home_pct / (home + away_pct)
"""
import sys
import pandas as pd
from datetime import date
from pathlib import Path

from odds_utils import moneyline_to_prob, strip_vig

MODEL_VERSION = "v1_team_records"

def predict_v1(row):
    """
    Predict home team win proabability for a single game (one row of the Dataframe).
    Return a float between 0 and 1, or None if data is missing.
    """
    home_pct = row["home_pct"]
    away_pct = row["away_pct"]
    if pd.isna(home_pct) or pd.isna(away_pct):
        return None
    total = home_pct + away_pct
    if total == 0:
        return 0.5 # edge case: bot team teams 0-0
    return home_pct / total 

# 1. Figure out which date to predict
if len(sys.argv) > 1:
    target_date = sys.argv[1]
else:
    target_date = date.today().isoformat()

print(f"Predicting games for {target_date} using model: {MODEL_VERSION}")

# 2. Load the merged date
merged_path = Path(f"merged_{target_date}.csv")
if not merged_path.exists():
    raise SystemExit(f"ERROR: {merged_path} not found. Run merge_data.py first.")

df = pd.read_csv(merged_path)
print(f"Loaded {len(df)} games")

# 3. Compute predictions and market probabilities
predictions = []
for _, row in df.iterrows():
    model_home_prob = predict_v1(row)

    away_implied = moneyline_to_prob(row.get("away_ml_avg"))
    home_implied = moneyline_to_prob(row.get("home_ml_avg"))
    market_away_fair, market_home_fair = strip_vig(away_implied, home_implied)

    predictions.append({
      "date": target_date,
      "game_pk": row["game_pk"], 
      "model_version": MODEL_VERSION,
      "away_team": row["away_team"],
      "home_team": row["home_team"],
      "away_wins": row["away_wins"],
      "away_losses": row["away_losses"],
      "home_wins": row["home_wins"],
      "home_losses": row["home_losses"],
      "model_home_prob": model_home_prob,
      "market_home_prob": market_home_fair,
      "edge": (model_home_prob - market_home_fair) if model_home_prob is not None and market_home_fair is not None else None,
      "away_ml_avg": row.get("away_ml_avg"),
      "home_ml_avg": row.get("home_ml_avg"),
    })

predictions_df = pd.DataFrame(predictions)

# 4. Round for readability
for col in ["model_home_prob", "market_home_prob", "edge"]:
    predictions_df[col] = predictions_df[col].round(3)

# 5. Print Scorecard
print()
print("Today's predictions:")
print(predictions_df[[
    "away_team", "home_team",
    "model_home_prob", "market_home_prob", "edge",
]].to_string(index=False))

# 6. Append to the growing prediction log
log_path = Path("predictions.csv")
if log_path.exists():
    existing = pd.read_csv(log_path)
    combined = pd.concat([existing, predictions_df], ignore_index=True)
else:
    combined= predictions_df

combined.to_csv(log_path, index=False)
print()
print(f"Appended {len(predictions_df)} predictions to {log_path} (total rows: {len(combined)})")