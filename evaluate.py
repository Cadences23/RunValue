"""
Evaluate prediction performance by joining predictions.csv to results.csv
Computes accuracy, log loss, and Brier score per model version.
"""
import math
import pandas as pd
from pathlib import Path
from datetime import date

def log_loss_one(prob,actual):
    """
    Log loss for a single prediciton.
    prob: predicted probability of the positive class (here: home wins)
    actual: 1 if home won, 0 if away won
    """
    # Clip prob slightly away from 0 and 1 to avoid log(0)
    eps = 1e-15
    prob = max(eps, min(1 - eps,prob))
    return -(actual * math.log(prob) + (1 - actual) * math.log(1 - prob))


def brier_one(prob,actual):
    """Brier score (squared error) for a single prediciton."""
    return (prob - actual) ** 2

# 1. Load Both files
preds_path = Path("predictions.csv")
results_path = Path("results.csv")

if not preds_path.exists():
    raise SystemExit("ERROR: predictions.csv not found.")
if not results_path.exists():
    raise SystemExit("ERROR: results.csv not found.")

preds = pd.read_csv(preds_path)
results = pd.read_csv(results_path)

print(f"Loaded {len(preds)} predictions and {len(results)} results")

# 2. Join predictions to results on game_pk
# Use an inner join: only keep predictions that have matching results
graded = pd.merge(
    preds,
    results[["game_pk", "home_won", "away_score", "home_score", "winner"]],
    on="game_pk",
    how="inner",
)

print(f"{len(graded)} predictions have matching results")

if len(graded) == 0:
    raise SystemExit("No graded predictions yet. Run fetch_results.py first.")

# 3. Compute per-row metrics
# home_won comes from results.csv as True/False; convert to 1/0 for math.
graded["home_won_int"] = graded["home_won"].astype(int)
graded["model_correct"] = (
    (graded["model_home_prob"] >= 0.5) == (graded["home_won_int"] == 1) 
)
graded["log_loss"] = graded.apply(
    lambda r: log_loss_one(r["model_home_prob"], r["home_won_int"]), axis=1
)
graded["brier"] = graded.apply(
    lambda r: brier_one(r["model_home_prob"], r["home_won_int"]), axis=1
)

# 4. Aggregate by model version
print()
print("=" * 60)
print("SCORECARD")
print("=" * 60)

for version, group in graded.groupby("model_version"):
    n = len(group)
    accuracy = group["model_correct"].mean()
    logloss = group["log_loss"].mean()
    brier = group["brier"].mean()

    print(f"\nModel: {version}")
    print(f" Games graded: {n}")
    print(f" Accuracy: {accuracy:.3f} (baseline 0.500)")
    print(f" Log Loss: {logloss:.3f} (baseline 0.693)")
    print(f" Brier score: {brier:.3f} (baseline.250)")
    
# 5. Baseline: always pick the home team
home_baseline_accuracy = graded["home_won_int"].mean()
print(f"\nBaseline (always pick home team): accuracy {home_baseline_accuracy:.3f}")

# 6. Optional: market scorecard (only on games with market probability)
market_rows = graded.dropna(subset=["market_home_prob"])
if len(market_rows) > 0:
    market_correct = (
        (market_rows["market_home_prob"] >=0.5) == (market_rows["home_won_int"] == 1)
    )
    market_logloss = market_rows.apply(
        lambda r: log_loss_one(r["market_home_prob"], r["home_won_int"]), axis=1
    ).mean()
    market_brier = market_rows.apply(
        lambda r: brier_one(r["market_home_prob"], r["home_won_int"]), axis=1
    ).mean()

    print(f"\nMarket (sportsbook consenus, vig-stripped): on {len(market_rows)} games")
    print(f" Accuracy: {market_correct.mean():.3f}")
    print(f" Loss loss: {market_logloss:.3f}")
    print(f" Brier score: {market_brier:.3f}")

# 7. Save the graded predictions for later inspection
graded_out = Path("graded.csv")
graded.to_csv(graded_out, index=False)
print(f"\nSaved detailed graded predictions to {graded_out}")

# 8. Append a row to the scorehard history
scorecard_rows = []
for version, group in graded.groupby("model_version"):
    scorecard_rows.append({
        "date_evaluated": date.today().isoformat(),
        "model_version": version,
        "n_games": len(group),
        "accuracy": round(group["model_correct"].mean(), 4),
        "log_loss": round(group["log_loss"].mean(), 4),
        "brier": round(group["brier"].mean(), 4),
    })

scorecard_df = pd.DataFrame(scorecard_rows)

history_path = Path("scorecard_history.csv")
if history_path.exists():
    existing_history = pd.read_csv(history_path)
    combined_history = pd.concat([existing_history, scorecard_df], ignore_index=True)
else:
    combined_history =scorecard_df

combined_history.to_csv(history_path, index=False)
print (f"Appended scorecard snapshot to {history_path} (total snapshots: {len(combined_history)})")