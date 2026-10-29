"""Price collection. Implement PriceProvider for a real source (retailer API,
affiliate feed) and pass it to run_collection. Prefer official APIs over scraping:
most retailers forbid scraping in their terms."""
import random
from datetime import datetime, timedelta
from typing import Protocol
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Part, PriceSnapshot

STORES = ["Amazon", "Newegg", "Micro Center", "B&H"]


class PriceProvider(Protocol):
    def fetch(self, part: Part) -> dict[str, float]: ...


class MockProvider:
    """Random walk around each part's base price. Stands in for a live source."""
    def __init__(self, seed: int = 1):
        self.rng = random.Random(seed)

    def fetch(self, part: Part) -> dict[str, float]:
        base = part.attrs["base"]
        return {s: round(base * self.rng.uniform(.92, 1.10)) for s in STORES}


def run_collection(db: Session, provider: PriceProvider, now: datetime | None = None) -> int:
    now = now or datetime.utcnow()
    n = 0
    for part in db.scalars(select(Part)):
        for store, price in provider.fetch(part).items():
            db.add(PriceSnapshot(part_id=part.id, store=store, price=price, seen_at=now))
            n += 1
    db.commit()
    return n


def latest_prices(db: Session, part_id: int) -> dict[str, float]:
    """Most recent price per store for one part."""
    newest = (select(PriceSnapshot.store, func.max(PriceSnapshot.seen_at).label("t"))
              .where(PriceSnapshot.part_id == part_id).group_by(PriceSnapshot.store).subquery())
    rows = db.execute(
        select(PriceSnapshot.store, PriceSnapshot.price).join(
            newest, (PriceSnapshot.store == newest.c.store) & (PriceSnapshot.seen_at == newest.c.t))
        .where(PriceSnapshot.part_id == part_id))
    return {s: p for s, p in rows}


def backfill(db: Session, provider: PriceProvider, days: int = 30, step: int = 3):
    """Seed history so charts have something to show on first run."""
    for d in range(days, -1, -step):
        run_collection(db, provider, datetime.utcnow() - timedelta(days=d))
