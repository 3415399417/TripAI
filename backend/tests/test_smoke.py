"""Smoke tests for the core API flow (uses the mock LLM mode)."""

import os

os.environ["LLM_API_KEY"] = ""
os.environ["DATABASE_URL"] = "sqlite:///./test_tripai.db"

from datetime import date, timedelta
import os as _os

from fastapi.testclient import TestClient

DB_FILE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "test_tripai.db")
if _os.path.exists(DB_FILE):
    _os.remove(DB_FILE)

from app.core.database import init_db
from app.main import app


def _client() -> TestClient:
    init_db()
    return TestClient(app)


def test_health() -> None:
    client = _client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_login_generate_trip() -> None:
    client = _client()
    email = "smoke@tripai.cn"
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "secret123", "nickname": "冒烟测试"},
    )
    assert register.status_code == 201, register.text
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    login = client.post(
        "/api/auth/login", json={"email": email, "password": "secret123"}
    )
    assert login.status_code == 200

    start = date.today() + timedelta(days=7)
    end = start + timedelta(days=2)
    payload = {
        "destination": "北京",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "travelers": 2,
        "budget": 2000,
        "pace": "适中",
        "interests": ["美食"],
    }
    gen = client.post("/api/ai/generate-trip", json=payload, headers=headers)
    assert gen.status_code == 200, gen.text
    data = gen.json()
    assert data["mock"] is True
    assert data["trip"]["schedules"], "行程地点不应为空"

    trip_id = data["trip"]["id"]
    detail = client.get(f"/api/trips/{trip_id}", headers=headers)
    assert detail.status_code == 200
    public = client.get(f"/api/trips/{trip_id}/public")
    assert public.status_code == 200

    # unauthorized access should fail
    denied = client.get("/api/trips")
    assert denied.status_code == 401
