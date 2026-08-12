"""Trip expense (real spending) API."""


def _trip_id(client, token: str) -> int:
    start = "2026-08-20"
    resp = client.post(
        "/api/ai/generate-trip",
        json={
            "destination": "北京",
            "start_date": start,
            "end_date": "2026-08-21",
            "travelers": 2,
            "budget": 3000,
            "pace": "适中",
            "interests": ["美食"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["trip"]["id"]


def test_expense_crud(client, token_factory):
    token = token_factory("expense@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}
    trip_id = _trip_id(client, token)

    add = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={"amount": 120, "category": "餐饮", "day": 1, "description": "午饭"},
        headers=headers,
    )
    assert add.status_code == 201, add.text
    expense_id = add.json()["id"]

    summary = client.get(f"/api/trips/{trip_id}/expenses", headers=headers)
    assert summary.status_code == 200
    data = summary.json()
    assert data["spent"] == 120
    assert data["remaining"] == 3000 - 120
    assert len(data["items"]) == 1

    denied = client.get(f"/api/trips/{trip_id}/expenses")
    assert denied.status_code == 401

    delete = client.delete(
        f"/api/trips/{trip_id}/expenses/{expense_id}", headers=headers
    )
    assert delete.status_code == 204
    after = client.get(f"/api/trips/{trip_id}/expenses", headers=headers).json()
    assert after["spent"] == 0


def test_invalid_amount_rejected(client, token_factory):
    token = token_factory("expense2@tripai.cn")
    headers = {"Authorization": f"Bearer {token}"}
    trip_id = _trip_id(client, token)
    resp = client.post(
        f"/api/trips/{trip_id}/expenses",
        json={"amount": 0, "category": "交通"},
        headers=headers,
    )
    assert resp.status_code == 422
