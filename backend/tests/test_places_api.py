"""Place detail lazy enrichment + search."""


def test_place_detail_enriches_from_amap(client, monkeypatch, token_factory):
    from app.core.database import SessionLocal
    from app.models.place import Place

    with SessionLocal() as db:
        place = Place(
            name="测试景点",
            city="上海",
            latitude=31.23,
            longitude=121.47,
            amap_id="TEST001",
        )
        db.add(place)
        db.commit()
        place_id = place.id

    def fake_detail(amap_id: str):
        return {
            "opening_hours": "09:00-17:00",
            "phone": "021-12345678",
            "photos": ["https://example.com/a.jpg"],
        }

    monkeypatch.setattr(
        "app.services.amap_service.fetch_place_detail", fake_detail
    )
    token = token_factory("place@tripai.cn")
    resp = client.get(
        f"/api/places/{place_id}/detail",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["opening_hours"] == "09:00-17:00"
    assert data["phone"] == "021-12345678"
    assert data["photos"] == ["https://example.com/a.jpg"]


def test_place_detail_missing_returns_404(client, token_factory):
    token = token_factory("place2@tripai.cn")
    resp = client.get(
        "/api/places/999999/detail",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
