# Rigwise

Track PC part prices across retailers and turn a budget into a compatible build.

**Stack:** Python 3.12, FastAPI, SQLAlchemy 2, SQLite, pytest, Docker, GitHub Actions
**Frontend:** GitHub Pages. **API:** Render (see Deploy).

## Features
- Append-only price history per part and store, so trends come from real snapshots
- Pluggable `PriceProvider` interface for the collector (a mock ships by default)
- Budget optimizer: exhaustive search over compatible combos with socket, RAM type and PSU-headroom checks
- REST API with auto-generated docs at `/docs`

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # http://localhost:8000/docs
pytest -q
docker build -t rigwise . && docker run -p 8000:8000 rigwise
```

## Deploy
GitHub Pages is static, so the frontend and API are hosted separately.
1. **API:** create a Render web service from this repo (it reads `render.yaml`). Set `CORS_ORIGINS` to `https://YOUR-USERNAME.github.io`. Copy the service URL.
2. **Frontend:** in GitHub go to Settings > Secrets and variables > Actions > Variables and add `API_URL` with that URL. Then Settings > Pages > Source: GitHub Actions. Push to `main` and the workflow publishes `web/`.

Locally, `uvicorn` serves the frontend and API together at `http://localhost:8000`.
The free Render tier sleeps when idle and resets its SQLite file, so the mock data reseeds on each wake-up.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/parts?category=GPU&q=4070` | Parts with latest price per store and best store |
| GET | `/parts/{id}/history` | Price snapshots over time |
| POST | `/build` | `{"budget": 1200, "focus": "gaming"}` returns a build |

## Design notes
- **Optimizer is pure Python** (`app/optimizer.py`) with no DB or web imports, so it is unit tested directly.
- **Search is brute force** (~1.7k combos). For a bigger catalogue, prune by price or move to OR-Tools CP-SAT.
- **Prices are mock data.** Implement `PriceProvider.fetch` against a retailer or affiliate API; check each store's terms before scraping.

## Roadmap
- [ ] Real provider and a scheduled collection job (GitHub Actions cron)
- [ ] Price-drop alerts by email
- [ ] Cases and coolers with clearance and size checks
- [ ] Postgres and Alembic migrations
- [x] Frontend wired to the API
- [ ] Per-part history chart view
