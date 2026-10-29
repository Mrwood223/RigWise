"""Daily job: collect prices, append to data/snapshots.json, and write web/data.json.

web/data.json holds everything the static frontend needs: latest prices, trends,
and a precomputed best build for every $50 budget step, so the optimizer stays in
Python (one tested implementation) and the browser only does a lookup.
Run from the repo root:  python -m scripts.export_static
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.collector import MockProvider  # swap for a real PriceProvider later
from app.optimizer import Item, build
from app.seed import PARTS

ROOT = Path(__file__).resolve().parent.parent
SNAPS = ROOT / "data" / "snapshots.json"
OUT = ROOT / "web" / "data.json"
KEEP_DAYS = 90
BUDGETS = range(500, 5001, 50)


def collect(provider, when):
    return {"t": when.isoformat(timespec="seconds"),
            "prices": {p.name: provider.fetch(p) for p in PARTS}}


def main(now=None):
    now = now or datetime.now(timezone.utc)
    provider = MockProvider(seed=int(now.timestamp()))
    snaps = json.loads(SNAPS.read_text()) if SNAPS.exists() else []
    if not snaps:  # first run: backfill about 30 days so trends have history
        snaps = [collect(provider, now - timedelta(days=d)) for d in range(30, 0, -3)]
    today = now.date().isoformat()
    snaps = [s for s in snaps if not s["t"].startswith(today)]  # one snapshot per day
    snaps.append(collect(provider, now))
    cutoff = (now - timedelta(days=KEEP_DAYS)).isoformat()
    snaps = [s for s in snaps if s["t"] >= cutoff]

    parts, items = [], []
    for i, p in enumerate(PARTS, 1):
        prices = snaps[-1]["prices"][p.name]
        store = min(prices, key=prices.get)
        trend = [min(s["prices"][p.name].values()) for s in snaps if p.name in s["prices"]]
        attrs = {k: v for k, v in p.attrs.items() if k != "base"}
        parts.append({"id": i, "category": p.category, "name": p.name, "prices": prices,
                      "best_store": store, "best_price": prices[store], "trend": trend})
        items.append(Item(i, p.category, p.name, prices[store], p.perf, attrs))

    builds = {}
    for focus in ("gaming", "work"):
        builds[focus] = {}
        for b in BUDGETS:
            r = build(items, b, focus)
            builds[focus][str(b)] = None if r is None else {
                "cost": r.cost, "score": r.score,
                "parts": [{"category": i.category, "name": i.name, "price": i.price} for i in r.items]}

    SNAPS.parent.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SNAPS.write_text(json.dumps(snaps, separators=(",", ":")))
    OUT.write_text(json.dumps({"updated": snaps[-1]["t"], "parts": parts, "builds": builds},
                              separators=(",", ":")))
    print(f"{len(snaps)} snapshots, {len(parts)} parts, builds for {len(BUDGETS)} budgets")


if __name__ == "__main__":
    main()
