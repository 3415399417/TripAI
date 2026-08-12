"""Personal center API: stats + nickname update."""


def test_me_stats_and_update(client, token_factory):
    token = token_factory("me@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}

    stats = client.get("/api/auth/me/stats", headers=headers)
    assert stats.status_code == 200
    data = stats.json()
    assert data["trip_count"] == 0
    assert data["total_budget"] == 0
    assert data["total_spent"] == 0
    assert data["member_days"] >= 0

    update = client.put(
        "/api/auth/me", json={"nickname": "旅行达人"}, headers=headers
    )
    assert update.status_code == 200
    assert update.json()["nickname"] == "旅行达人"

    me = client.get("/api/auth/me", headers=headers)
    assert me.json()["nickname"] == "旅行达人"


def test_me_requires_auth(client):
    assert client.get("/api/auth/me/stats").status_code == 401
