import json
from datetime import datetime, timezone
from scripts import export_static as ex


def test_export(tmp_path, monkeypatch):
    monkeypatch.setattr(ex, "SNAPS", tmp_path / "data" / "snapshots.json")
    monkeypatch.setattr(ex, "OUT", tmp_path / "web" / "data.json")
    now = datetime(2026, 10, 28, 6, tzinfo=timezone.utc)
    ex.main(now)
    ex.main(now)  # same day again must replace, not append
    snaps = json.loads(ex.SNAPS.read_text())
    assert sum(s["t"].startswith("2026-10-28") for s in snaps) == 1
    out = json.loads(ex.OUT.read_text())
    assert len(out["parts"]) > 10 and len(out["parts"][0]["trend"]) > 1
    b = out["builds"]["gaming"]["1500"]
    assert b and b["cost"] <= 1500
    assert out["builds"]["gaming"]["500"] is None
