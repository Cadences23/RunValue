# RunValue

A daily MLB prediction pipeline that comapres team-records-based win probabilities against sports market odds

Built as a personal learning project to gain hands-on experience with full applied data science loop: data ingestion, feature engineering, modeling, evaluation, and interation. Designed to teach the surrounding plumbing of ML systems (pipelines, persistance, model versioning, evaluation discipline) ahead of starting a master's program in AI and data science.

## What it does

Every morning, one command ('Python run_daily.py) runs the full pipeline:

1. **Fetches yesterday's results** from the MLB Stats API
2. **Fetches today's game schedule** with current team records
3. **Fetches today's sportsbook odds** from The Odds API across ~9 books
4. **Merges games and odds** into a single per-day table
5. **Predicts each game** using the current model version
6. **Evaluates** all historical predictions against actual results

Predictions are tagged with a model version and appended to a growing log (`predictions.csv`). Results accumulate in `results.csv`. The scorecard updates over time in `scorecard_history.csv`.

## Model versions

- **v1_team_records** — baseline: predicts home win probability as `home_pct / (home_pct + away_pct)`. The simplest possible model; the floor every future version must beat.

## Tech stack

- Python 3.14
- pandas for tabular data
- requests for HTTP / API calls
- python-dotenv for secrets management

## Data sources

- [MLB Stats API](https://statsapi.mlb.com/) — free, no key required
- [The Odds API](https://the-odds-api.com/) — free tier, ~500 requests/month

## Notes

This is a learning project, not a betting tool. The goal is to build intuition for the full ML pipeline (ingestion → modeling → evaluation → iteration), with baseball as a convenient domain that has rich, free, fast-feedback data.