""""
Generate visualization cahrts from the paper trading results.

Reads bets.csv (one row per simulated bet) and produces:
- Equity curve: Bankroll over time
- P&L Distribution: Histogram of per bet outcomes
- Edge vs P&L scatter: did bigger edges produce bigger wins?
- Cumulative P&L by date: smoother daily view of the equity curve

All charts are saved as PNG files in the charts/ foler.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Load the bets data
bets_path = Path("bets.csv")
if not bets_path.exists():
    raise SystemExit("ERROR: bets.csv not found. Run simulate_bets.py first.")

bets= pd.read_csv(bets_path)
print(f"Loaded {len(bets)} bets across {bets["model_version"].nunique()} model version(s)")

# Make sure the charts folder exists
charts_dir = Path("charts")
charts_dir.mkdir(exist_ok=True)

# 2. Build one set of charts per model version
for version, group in bets.groupby("model_version"):
    print(f"\nGenerating charts for: {version}")
    group = group.sort_values(["date", "game_pk"]).reset_index(drop=True)
    group["bet_number"] = range(1, len(group) + 1)

    starting_bankroll = group["bankroll_after"].iloc[0] - group["pnl"].iloc[0]
    ending_bankroll = group["bankroll_after"].iloc[-1]
    total_pnl = ending_bankroll - starting_bankroll
    roi = total_pnl / (len(group) * group["stake"].iloc[0])
    n_wins = group["won"].sum()
    win_rate = n_wins / len(group)

    # --- Chart 1: Equity curve (bankroll per bet) ---
    fig, ax = plt.subplots(figsize=(12, 6))

    # Color points green if the bet won, red if it loss
    colors = ["#2e8b57" if won else "#c0392b" for won in group["won"]]

    ax.plot(group["bet_number"], group["bankroll_after"],
            color="#333333", linewidth=1, alpha=0.6, zorder=1)
    ax.scatter(group["bet_number"], group["bankroll_after"],
               c=colors, s=20, zorder=2, edgecolors="none")
    ax.axhline(y=starting_bankroll, color="#999999", linestyle="--",
               linewidth=1, label=f"Starting bankroll (${starting_bankroll:,.0f})")
    
    ax.set_title(
        f"Equity Curve - {version}\n"
        f"{len(group)} bets · {win_rate:.1%} win rate · "
        f"${total_pnl:+,.2f} P&L · {roi:+.2%} ROI",
        fontsize=13,
    )
    ax.set_xlabel("Bet number (chronological)")
    ax.set_ylabel("Bankroll ($)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()

    out = charts_dir / f"equity_curve_{version}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f" Saved {out}")

    # --- Chart 2: P&L distribution (histogram) ---
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(group["pnl"], bins=30, color="#4a90c2", edgecolor="white")
    ax.axvline(x=0, color="#333333", linestyle="--", linewidth=1)
    ax.set_title(f"P&L per Bet - {version}", fontsize=13)
    ax.set_xlabel("P&L ($)")
    ax.set_ylabel("Number of bets")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()

    out = charts_dir / f"pnl_histogram_{version}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f" Saved {out}")

    # --- Chart 3: Edge vs P&L scatter ---
    fig, ax = plt.subplots(figsize=(10, 6))
    win_mask = group["won"] == True
    ax.scatter(
        group.loc[win_mask, "edge"], group.loc[win_mask, "pnl"],
        c="#2e8b57", s=25, alpha=0.7, label="Won",
    )
    ax.scatter(
        group.loc[~win_mask, "edge"], group.loc[~win_mask, "pnl"],
        c="#c0392b", s=25, alpha=0.7, label="Lost",
    )
    ax.axhline(y=0, color="#333333", linestyle="--", linewidth=1)
    ax.set_title(f"Edge vs Outcome - {version}", fontsize=13)
    ax.set_xlabel("Model edge (|model_prob - market_prob|)")
    ax.set_ylabel("P&L ($)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left")
    fig.tight_layout()

    out = charts_dir / f"edge_vs_pnl_{version}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f" Saved {out}")

    # --- Chart 4: Cumulative P&L by date ---
    daily = (
        group
        .groupby("date")
        .agg(daily_pnl=("pnl", "sum"), bets_that_day=("game_pk", "count"))
        .reset_index()
    )
    daily["cumulative_pnl"] = daily["daily_pnl"].cumsum()

    fig, ax= plt.subplots(figsize=(12, 5))
    ax.fill_between(daily["date"], 0, daily["cumulative_pnl"],
                    where=daily["cumulative_pnl"] >=0,
                    color="#2e8b57", alpha=0.3, interpolate=True)
    ax.fill_between(daily["date"], 0, daily["cumulative_pnl"],
                    where=daily["cumulative_pnl"] < 0,
                    color="#c0392b", alpha=0.3, interpolate=True)
    ax.plot(daily["date"], daily["cumulative_pnl"], color="#333333", linewidth=1.5)
    ax.axhline(y=0, color="#333333", linestyle="--", linewidth=1)
    ax.set_title(f"Cumulative P&L by Date - {version}", fontsize=13)
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative  P&L ($)")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()

    out = charts_dir / f"cumulative_pnl_{version}.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f" Saved {out}")

print("\nALL charts saved to charts/")

                    

