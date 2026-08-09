"""AMap Web Service client with a local POI cache.

Personal-developer quota for POI search is only 100/day, so every search
result is upserted into the local `places` table and reused later.
"""

from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.place import Place

settings = get_settings()


class AMapNotConfigured(Exception):
    """Raised when AMAP_WEB_KEY is not set."""


class AMapError(Exception):
    """Raised when the AMap API returns an error or is unreachable."""


def is_configured() -> bool:
    return bool(settings.AMAP_WEB_KEY)


def search_places(query: str, city: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Search POIs via AMap text search and return normalized results."""
    if not is_configured():
        raise AMapNotConfigured("后端未配置高德 Web 服务 Key（AMAP_WEB_KEY）")

    params: dict[str, Any] = {
        "key": settings.AMAP_WEB_KEY,
        "keywords": query,
        "offset": str(limit),
        "page": "1",
        "extensions": "base",
    }
    if city:
        params["city"] = city

    try:
        resp = httpx.get(settings.AMAP_SEARCH_URL, params=params, timeout=10)
        data = resp.json()
    except Exception as exc:
        raise AMapError(f"高德接口请求失败: {exc}") from exc

    if data.get("status") != "1":
        raise AMapError(data.get("info", "高德搜索失败"))

    results: list[dict[str, Any]] = []
    for poi in data.get("pois", [])[:limit]:
        location = poi.get("location") or ""
        if "," not in location:
            continue
        lng, lat = location.split(",", 1)
        if not lng or not lat:
            continue
        results.append(
            {
                "amap_id": poi.get("id"),
                "name": poi.get("name", "").strip(),
                "address": poi.get("address") or None,
                "city": (city or poi.get("cityname")) or None,
                "category": poi.get("type") or None,
                "latitude": float(lat),
                "longitude": float(lng),
                "rating": _to_float(poi.get("rating")),
                "image_url": None,
            }
        )
    return results


def upsert_place(db: Session, data: dict[str, Any]) -> Place:
    """Cache a POI, matching by amap_id first, then name + city."""
    place = None
    if data.get("amap_id"):
        place = db.query(Place).filter(Place.amap_id == data["amap_id"]).first()
    if place is None:
        place = (
            db.query(Place)
            .filter(Place.name == data["name"])
            .filter(Place.city == data.get("city"))
            .first()
        )
    if place is None:
        place = Place(**data)
        db.add(place)
    else:
        for key, value in data.items():
            setattr(place, key, value)
    db.flush()
    return place


def enrich_place(
    db: Session,
    name: str,
    city: str | None,
    fallback: dict[str, Any],
) -> Place:
    """Get authoritative coordinates from AMap (cached), else use LLM data."""
    try:
        results = search_places(name, city, limit=1)
    except (AMapNotConfigured, AMapError):
        results = []

    if results:
        return upsert_place(db, results[0])

    lat = fallback.get("latitude")
    lng = fallback.get("longitude")
    return upsert_place(
        db,
        {
            "amap_id": None,
            "name": name,
            "address": None,
            "city": city,
            "category": fallback.get("category"),
            "latitude": float(lat) if lat else 0.0,
            "longitude": float(lng) if lng else 0.0,
            "rating": None,
            "image_url": None,
        },
    )


def _to_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

