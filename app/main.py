import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .db import engine, SessionLocal, Base
from .models import Part, PriceSnapshot
from .collector import latest_prices
from .optimizer import Item, build
from .seed import seed_if_empty

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(title="Rigwise", lifespan=lifespan)
# CORS_ORIGINS is a comma-separated list, e.g. https://your-name.github.io (no path)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["*"])


def get_db():
    with SessionLocal() as db:
        yield db


def trend(db: Session, part_id: int) -> list[float]:
    """Cheapest price at each collection time, oldest first."""
    rows = db.execute(select(PriceSnapshot.seen_at, func.min(PriceSnapshot.price))
                      .where(PriceSnapshot.part_id == part_id)
                      .group_by(PriceSnapshot.seen_at).order_by(PriceSnapshot.seen_at))
    return [p for _, p in rows]


def with_best(db: Session, part: Part) -> dict:
    prices = latest_prices(db, part.id)
    store = min(prices, key=prices.get) if prices else None
    return {"id": part.id, "category": part.category, "name": part.name, "prices": prices,
            "best_store": store, "best_price": prices.get(store), "trend": trend(db, part.id)}


@app.get("/parts")
def list_parts(category: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Part)
    if category:
        stmt = stmt.where(Part.category == category)
    if q:
        stmt = stmt.where(Part.name.ilike(f"%{q}%"))
    return [with_best(db, p) for p in db.scalars(stmt)]


@app.get("/parts/{part_id}/history")
def history(part_id: int, store: str | None = None, db: Session = Depends(get_db)):
    if not db.get(Part, part_id):
        raise HTTPException(404, "Part not found")
    stmt = select(PriceSnapshot).where(PriceSnapshot.part_id == part_id).order_by(PriceSnapshot.seen_at)
    if store:
        stmt = stmt.where(PriceSnapshot.store == store)
    return [{"store": s.store, "price": s.price, "seen_at": s.seen_at} for s in db.scalars(stmt)]


class BuildRequest(BaseModel):
    budget: float = Field(ge=500, le=10000)
    focus: Literal["gaming", "work"] = "gaming"


@app.post("/build")
def make_build(req: BuildRequest, db: Session = Depends(get_db)):
    items = []
    for p in db.scalars(select(Part)):
        items.append(Item(p.id, p.category, p.name, with_best(db, p)["best_price"], p.perf, p.attrs))
    result = build(items, req.budget, req.focus)
    if not result:
        raise HTTPException(422, "No compatible build fits that budget. Try a higher budget.")
    return {"cost": result.cost, "score": result.score,
            "parts": [{"category": i.category, "name": i.name, "price": i.price} for i in result.items]}


# Serve the frontend from the same server for local use. Must be registered last.
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
