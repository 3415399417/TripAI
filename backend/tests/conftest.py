import os
from pathlib import Path

os.environ.setdefault("LLM_API_KEY", "")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_tripai.db")

import pytest

DB_FILE = Path(__file__).resolve().parent.parent / "test_tripai.db"


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    if DB_FILE.exists():
        DB_FILE.unlink()
    yield


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.core.database import init_db
    from app.main import app

    init_db()
    return TestClient(app)


@pytest.fixture()
def token_factory(client):
    def make(email: str) -> str:
        resp = client.post(
            "/api/auth/register",
            json={"email": email, "password": "secret123", "nickname": "测试用户"},
        )
        if resp.status_code not in (200, 201):
            resp = client.post(
                "/api/auth/login",
                json={"email": email, "password": "secret123"},
            )
        assert resp.status_code in (200, 201), resp.text
        return resp.json()["access_token"]

    return make
