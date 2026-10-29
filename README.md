# Rigwise

Track PC part prices across retailers and turn a budget into a compatible build.
**Live site:** _add your GitHub Pages link here_

**Stack:** Python 3.12, SQLAlchemy, FastAPI, pytest, GitHub Actions, GitHub Pages, vanilla JS

## How it works
```
GitHub Actions (daily cron)
  -> scripts/export_static.py   collect prices, append to data/snapshots.json
                                precompute the best build for every $50 budget
  -> web/data.json              committed back to the repo
  -> GitHub Pages               static frontend reads data.json
```
There is no server to host. Price history lives in the repo as `data/snapshots.json`, so it survives every deploy. The optimizer runs only in Python and is unit tested. The browser just looks up the result.

## Features
- Daily price snapshots (90-day window) with per-part trend sparklines
- Pluggable `PriceProvider` interface (a mock ships by default)
- Budget optimizer: exhaustive search over compatible combos with socket, RAM type and PSU-headroom checks
- Optional FastAPI server (`app/main.py`) exposing the same data over REST at `/docs`

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.export_static        # writes web/data.json
python -m http.server -d web 8000      # open http://localhost:8000
pytest -q
```
Optional live API: `uvicorn app.main:app --reload` (serves the same page and `/docs`).

## Deploy
1. Push to GitHub with `main` as the default branch.
2. Settings > Pages > Source: **GitHub Actions**.
3. Settings > Actions > General > Workflow permissions: **Read and write**.
4. Run the workflow once from the Actions tab (Collect prices and deploy). It then runs daily.

## Design notes
- **Precomputed builds:** budgets are discrete ($50 steps), so 182 builds are computed once per run. This keeps one optimizer implementation instead of a Python and a JS copy.
- **Search is brute force** (~1.7k combos). For a bigger catalogue, prune by price or move to OR-Tools CP-SAT.
- **Prices are mock data.** Implement `PriceProvider.fetch` against a retailer or affiliate API, and check each store's terms before scraping.

## Roadmap
- [x] Static pipeline with scheduled collection
- [ ] Real price provider
- [ ] Price-drop alerts
- [ ] Cases and coolers with clearance checks
- [ ] Per-part history chart view
