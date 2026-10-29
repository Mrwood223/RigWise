from fastapi.testclient import TestClient
from app.main import app


def test_api_and_frontend():
    with TestClient(app) as c:
        parts = c.get("/parts").json()
        assert parts and parts[0]["best_store"] and len(parts[0]["trend"]) > 1
        r = c.post("/build", json={"budget": 1500, "focus": "gaming"})
        assert r.status_code == 200 and r.json()["cost"] <= 1500
        assert c.post("/build", json={"budget": 100}).status_code == 422
        assert "Rigwise" in c.get("/").text
