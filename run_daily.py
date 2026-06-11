"""
Daily orchestrator: runs the full RunValue pipeline in order.

Steps:
1. Fetch yesterday's results
2. Fetch today's game 
3. fetch today's odds
4. merge today's odd and game data
5. Predict today's games
6. Evalulate the runnning scorecard

Each step runs the matching .py script as a subprocess. If any step fails, 
we print a clear error and stop -- but we don't lose data from prior steps.
 """
import subprocess
import sys
from datetime import date, timedelta


def run_step(label, command):
    """Run one pipeline step as a sub processs. Print clear progress."""
    print()
    print("=" * 60)
    print(f"STEP: {label}")
    print(f" command: {' '.join(command)}")
    print("=" * 60)

    result = subprocess.run(command, capture_output=False)

    if result.returncode !=0:
        print()
        print(f"!! STEP FAILED: {label} (exit code {result.returncode})")
        print("Stopping pipeline. Earlier steps' data is still saved.")
        sys.exit(1)

today = date.today().isoformat()
yesterday = (date.today() - timedelta(days=1)).isoformat()


print(f"\nRunValue daily pipeline")
print(f" today:     {today}")
print(f" yesterday   {yesterday}")

# Step 1: yesterday's results (so we have something to evalulate against)
run_step("Fetch yesterday's results", ["python", "fetch_results.py", yesterday])

# Step 2: today's games
run_step("Fetch today's games", ["python", "save_games.py"])

# Step 3: today's odds
run_step("Fetch today's odds", ["python", "fetch_odds.py"])

# Step 4: merge today's data
run_step("Merge today's data", ["python", "merge_data.py"])

# Step 5: predict today's games
run_step("Predict today's games", ["python", "predict.py"])

# Step 6: evaluate the running scorecard
run_step("Evaluate scorecard", ["python", "evaluate.py"])
# Step 7: simulate paper trading
run_step("Simulate paper trading",     ["python", "simulate_bets.py"])

# Step 8: generate charts
run_step("Generate charts",            ["python", "chart_bankroll.py"])


print()
print("=" * 60)
print("PIPELINE COMPLETE")
print(f" Predictions saved to predictions.csv")
print(f" Results saved to results.csv")
print(f" Scorecard snapshot in scorecard_history.csv")
print(f" Detailed graded predictions in graded.csv")
print(f" Simulated bets in bets.csv")
print(f" Daily bankroll in bankroll.csv")
print(f" Charts refreshed in charts/")