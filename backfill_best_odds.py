"""
One-off backfill: adds away_ml_best and home_ml_best to predictions.csv
by looking them up from merged_*.csv files.

Safe to re-run; idempotent.
"""
import glob
import pandas as pd

# 1. Read current predictions
preds = pd.read_csv("predictions.csv")
print(f"Before: {len(preds)} predictions")
print(f"Columns: {preds.columns.tolist()}")

# 2. Read every merged CSV, keep just the columns we need
merged_files = sorted(glob.glob("merged_*.csv"))
print(f"\nFound {len(merged_files)} merged files")

lookups = []
for f in merged_files:
    m = pd.read_csv(f)
    lookups.append(m[["date", "game_pk", "away_ml_best", "home_ml_best"]])

lookup_df = pd.concat(lookups, ignore_index=True).drop_duplicates(
    subset=["date", "game_pk"]
)
print(f"Lookup table: {len(lookup_df)} unique (date, game_pk) rows")

# 3. Drop existing _best columns if present, then merge
preds = preds.drop(columns=["away_ml_best", "home_ml_best"], errors="ignore")
preds = pd.merge(preds, lookup_df, on=["date", "game_pk"], how="left")

# 4. Diagnostics and save
matched = preds["away_ml_best"].notna().sum()
print(f"\nAfter: {len(preds)} predictions, {matched} have best odds populated")

preds.to_csv("predictions.csv", index=False)
print("Saved predictions.csv with best odds backfilled.")