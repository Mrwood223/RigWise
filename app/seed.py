from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .models import Part
from .collector import MockProvider, backfill

P = lambda c, n, base, perf=0, **a: Part(category=c, name=n, perf=perf, attrs={"base": base, **a})
PARTS = [
    P("CPU", "Ryzen 5 7600", 195, 70, socket="AM5", tdp=65),
    P("CPU", "Ryzen 7 7800X3D", 385, 92, socket="AM5", tdp=120),
    P("CPU", "Core i5-12400F", 140, 55, socket="LGA1700", tdp=65),
    P("CPU", "Core i5-14600K", 280, 80, socket="LGA1700", tdp=125),
    P("GPU", "GeForce RTX 4060", 300, 45, tdp=115),
    P("GPU", "Radeon RX 7700 XT", 390, 62, tdp=245),
    P("GPU", "GeForce RTX 4070 Super", 600, 75, tdp=220),
    P("GPU", "Radeon RX 7900 XT", 700, 88, tdp=315),
    P("Motherboard", "B650 (AM5, DDR5)", 160, socket="AM5", ram="DDR5"),
    P("Motherboard", "B760 (LGA1700, DDR4)", 120, socket="LGA1700", ram="DDR4"),
    P("Motherboard", "B760 (LGA1700, DDR5)", 150, socket="LGA1700", ram="DDR5"),
    P("Memory", "16GB DDR4-3200", 40, 50, ram="DDR4"),
    P("Memory", "32GB DDR4-3200", 72, 80, ram="DDR4"),
    P("Memory", "16GB DDR5-6000", 65, 55, ram="DDR5"),
    P("Memory", "32GB DDR5-6000", 100, 85, ram="DDR5"),
    P("Storage", "500GB NVMe", 43, 40),
    P("Storage", "1TB NVMe", 74, 65),
    P("Storage", "2TB NVMe", 130, 85),
    P("Power supply", "550W 80+ Bronze", 60, watts=550),
    P("Power supply", "750W 80+ Gold", 90, watts=750),
    P("Power supply", "850W 80+ Gold", 120, watts=850),
]


def seed_if_empty(db: Session):
    if db.scalar(select(func.count(Part.id))):
        return
    db.add_all(PARTS)
    db.commit()
    backfill(db, MockProvider())
