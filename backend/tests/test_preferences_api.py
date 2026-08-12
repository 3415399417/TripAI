"""User preference memory: API + generation learning."""


def test_preferences_empty(client, token_factory):
    token = token_factory("pref@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/auth/me/preferences", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["generation_count"] == 0
    assert "还没有偏好数据" in data["summary"]


def test_preferences_update_and_clear(client, token_factory):
    token = token_factory("pref2@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}

    update = client.put(
        "/api/auth/me/preferences",
        json={
            "favorite_places": ["外滩", "豫园"],
            "avoid_places": ["某某酒吧"],
        },
        headers=headers,
    )
    assert update.status_code == 200
    data = update.json()
    assert "外滩" in data["favorite_places"]
    assert "某某酒吧" in data["avoid_places"]

    cleared = client.delete("/api/auth/me/preferences", headers=headers)
    assert cleared.status_code == 204
    after = client.get("/api/auth/me/preferences", headers=headers).json()
    assert after["generation_count"] == 0
    assert after["favorite_places"] == []


def test_generation_records_preferences(client, token_factory):
    token = token_factory("pref4@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post(
        "/api/ai/generate-trip",
        json={
            "destination": "成都",
            "start_date": "2026-08-20",
            "end_date": "2026-08-21",
            "travelers": 1,
            "budget": 2000,
            "pace": "适中",
            "interests": ["美食"],
            "travel_style": "城市探索",
            "traveler_group": "成人",
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    prefs = client.get("/api/auth/me/preferences", headers=headers).json()
    assert prefs["generation_count"] == 1
    assert "美食" in prefs["interests"]
    assert len(prefs["favorite_places"]) > 0
    assert "生成记录" in prefs["summary"]
