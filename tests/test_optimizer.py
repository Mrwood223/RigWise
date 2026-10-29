from app.optimizer import Item, build, CATEGORIES


def cat(*specs):
    return [Item(i, c, n, price, perf, a) for i, (c, n, price, perf, a) in enumerate(specs)]


ITEMS = cat(
    ("CPU", "AM5 cpu", 200, 70, {"socket": "AM5", "tdp": 65}),
    ("CPU", "Intel cpu", 150, 55, {"socket": "LGA", "tdp": 65}),
    ("Motherboard", "AM5 board", 150, 0, {"socket": "AM5", "ram": "DDR5"}),
    ("Motherboard", "LGA board", 120, 0, {"socket": "LGA", "ram": "DDR4"}),
    ("Memory", "DDR5", 100, 80, {"ram": "DDR5"}),
    ("Memory", "DDR4", 70, 80, {"ram": "DDR4"}),
    ("GPU", "gpu", 300, 60, {"tdp": 150}),
    ("Storage", "ssd", 70, 60, {}),
    ("Power supply", "small psu", 60, 0, {"watts": 300}),
    ("Power supply", "psu", 90, 0, {"watts": 750}),
)


def test_respects_budget_and_compatibility():
    b = build(ITEMS, 1000)
    names = {i.category: i for i in b.items}
    assert b.cost <= 1000
    assert names["CPU"].attrs["socket"] == names["Motherboard"].attrs["socket"]
    assert names["Memory"].attrs["ram"] == names["Motherboard"].attrs["ram"]
    assert names["Power supply"].name == "psu"  # 300W is below the headroom rule


def test_returns_none_when_too_cheap():
    assert build(ITEMS, 400) is None


def test_more_budget_never_scores_lower():
    assert build(ITEMS, 1000).score >= build(ITEMS, 850).score
