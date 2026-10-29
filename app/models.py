from datetime import datetime
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class Part(Base):
    __tablename__ = "parts"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(index=True)
    name: Mapped[str]
    perf: Mapped[float] = mapped_column(default=0)
    attrs: Mapped[dict] = mapped_column(JSON, default=dict)  # socket, ram type, tdp, watts...


class PriceSnapshot(Base):
    """One row per part, store and collection run. Append-only, so history is free."""
    __tablename__ = "price_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    part_id: Mapped[int] = mapped_column(ForeignKey("parts.id"), index=True)
    store: Mapped[str]
    price: Mapped[float]
    seen_at: Mapped[datetime] = mapped_column(index=True)
