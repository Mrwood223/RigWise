"""Budget -> build. Pure Python (no DB or web imports) so it is trivial to unit test."""
from dataclasses import dataclass, field
from itertools import product

CATEGORIES = ["CPU", "Motherboard", "Memory", "GPU", "Storage", "Power supply"]
WEIGHTS = {
    "gaming": {"CPU": .25, "GPU": .50, "Memory": .15, "Storage": .10},
    "work":   {"CPU": .40, "GPU": .20, "Memory": .25, "Storage": .15},
}
PSU_HEADROOM = 1.6  # PSU watts must cover (CPU + GPU TDP) * 1.6 + 50


@dataclass
class Item:
    id: int
    category: str
    name: str
    price: float
    perf: float = 0
    attrs: dict = field(default_factory=dict)


@dataclass
class Build:
    items: list
    cost: float
    score: float


def is_compatible(cpu, mobo, mem, gpu, storage, psu) -> bool:
    need = (cpu.attrs["tdp"] + gpu.attrs["tdp"]) * PSU_HEADROOM + 50
    return (
        cpu.attrs["socket"] == mobo.attrs["socket"]
        and mem.attrs["ram"] == mobo.attrs["ram"]
        and psu.attrs["watts"] >= need
    )


def build(items: list[Item], budget: float, focus: str = "gaming") -> Build | None:
    """Exhaustive search over compatible combos; keeps the highest weighted score
    under budget (ties go to the cheaper build). The search space is the product of
    options per category (~1.7k combos here). For a larger catalogue, prune by
    price or swap in a constraint solver such as OR-Tools CP-SAT."""
    w = WEIGHTS[focus]
    pools = [[i for i in items if i.category == c] for c in CATEGORIES]
    best: Build | None = None
    for combo in product(*pools):
        cost = sum(i.price for i in combo)
        if cost > budget or not is_compatible(*combo):
            continue
        score = sum(i.perf * w.get(i.category, 0) for i in combo)
        if best is None or (score, -cost) > (best.score, -best.cost):
            best = Build(list(combo), round(cost, 2), round(score, 2))
    return best
