"""Paper trading simulation.

Takes the predictions log (predictions.csv) and results log (results.csv),
simulates flat-stake bets where the model has positive edge vs market,
and tracks bankroll over time.

Outputs:
- bets.csv: every bet placed with full details and P&L
- bankroll.csv: end-of-day bankroll snapshots
- Consle summary scorecard per model version

Configuration is at top of the script
"""
import pandas as pd
from pathlib import Path


# ===Configuration===
STARTING_BANKROLL = 10_000
BET_SIZE = 100
EDGE_THRESHOLD = 0.03 # only bet when | model_prob - market prob | >=3%

def bet_payout(stake, moneyline, won):
    """
    Compute P&L for a single bet.

    stake:      dollars risked
    moneyline:  American odds (ex. -150 or +110)
    won:        True if the bet won
    """
    if not won:
        return -stake
    if moneyline > 0:
        return stake * (moneyline / 100)
    else:
        return stake * (100 / abs(moneyline))


# === Load and prepare data ===
preds = pd.read_csv("predictions.csv")
results = pd.read_csv("results.csv")

print(f"Loaded {len(preds)} predictions and {len(results)} results")

# Join on game_pk
graded = pd.merge(
    preds,
    results[["game_pk", "home_won"]],
    on="game_pk",
    how="inner",
)

print(f"{len(graded)} predictions have matching results")

# Sort chronologically so the bankroll evolves in time order
graded = graded.sort_values(["date", "game_pk"]).reset_index(drop=True)

# === Simulate bets per model version ===
all_bets = []

for version, group in graded.groupby("model_version"):
    print(f"\n--- Simulating:   {version} ---")

    bankroll = STARTING_BANKROLL
    bets_for_version = []

    for _, row in group.iterrows():
        # Edge Check
        edge = row["edge"]
        if pd.isna(edge) or abs(edge) < EDGE_THRESHOLD:
            continue
      
        # Need best odds to bet
        if pd.isna(row["home_ml_best"]) or pd.isna(row["away_ml_best"]):
            continue

        # Decide which side: positive edge -> bet home; negative -> bet away
        if edge > 0:
            side = "home"
            moneyline= row["home_ml_best"]
            won = bool(row["home_won"])
        else:
            side = "away"
            moneyline = row["away_ml_best"]
            won = not bool(row["home_won"])

        pnl = bet_payout(BET_SIZE, moneyline, won)
        bankroll += pnl

        bets_for_version.append({
            "date": row["date"],
            "model_version": version,
            "game_pk": row["game_pk"],
            "away_team": row["away_team"],
            "home_team": row["home_team"],
            "side_bet": side,
            "moneyline": moneyline,
            "model_prob": round(row["model_home_prob"] if side == "home" else 1 - row["model_home_prob"], 4),
            "market_prob": round(row["market_home_prob"] if side == "home" else 1 - row["market_home_prob"], 4),
            "edge": round(abs(edge), 4),
            "stake": BET_SIZE,
            "won": won,
            "pnl": round(pnl, 2),
            "bankroll_after": round(bankroll, 2),
        })

    all_bets.extend(bets_for_version)

     # Summary for this version
    if not bets_for_version:
        print("No bets placed (no qualifying edges).")
        continue

    n_bets = len(bets_for_version)
    n_wins = sum(1 for b in bets_for_version if b["won"])
    total_pnl = bankroll - STARTING_BANKROLL
    roi = total_pnl / (n_bets * BET_SIZE)

    print(f" Bets Placed:       {n_bets} of {len(group)} graded games")
    print(f" Win/ Losses:       {n_wins} / {n_bets - (n_wins)}")
    print(f" Win Rate:          {n_wins / n_bets:.1%} ({n_wins} of {n_bets})")
    print(f" Starting Bankroll: ${STARTING_BANKROLL:,.2f}")
    print(f" Ending Bankroll:   ${bankroll:,.2f}")
    print(f" Total P&L:         ${total_pnl:+,.2f}")
    print(f" ROI:               {roi:+.1%}")

# === Save bets.csv ===
if all_bets:
    bets_df = pd.DataFrame(all_bets)
    bets_df.to_csv("bets.csv", index=False)
    print(f"\nSaved {len(bets_df)} bets to bets.csv")

    # End-of-day bankroll snapshots per model version
    bankroll_snapshots = (
        bets_df
        .groupby(["model_version", "date"])
        .agg(bankroll_eod=("bankroll_after", "last"),
            bets_that_day=("game_pk", "count"),
            pnl_that_day=("pnl", "sum"))
        .reset_index()
    )
    bankroll_snapshots.to_csv("bankroll.csv", index=False)
    print(f"Saved {len(bankroll_snapshots)} daily snapshots to bankroll.csv")
else:
    print("\nNo bets to save.")
