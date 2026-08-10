"""Persist AI-generated itinerary into the database with POI enrichment."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.models.place import Place
from app.models.trip import Schedule, Trip
from app.schemas.ai import AIGenerateResult
from app.services import amap_service
from app.services.ai_service.client import _calibrate_cost


def _dist_sq(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Squared lat/lng distance, good enough for ordering."""
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2


def _order_by_nearest(
    items: list[tuple], city_hint: str | None
) -> list[tuple]:
    """Greedy nearest-neighbour ordering; hotel stops go last."""
    from app.services.ai_service.mock import _CITY_COORDS

    if len(items) <= 1:
        return items
    hotels = [x for x in items if "住宿" in (x[0].category or "")]
    others = [x for x in items if "住宿" not in (x[0].category or "")]
    start_lng, start_lat = _CITY_COORDS.get(city_hint or "", (116.4074, 39.9042))
    ordered: list[tuple] = []
    current = (start_lat, start_lng)
    remaining = list(others)
    while remaining:
        best = min(
            remaining,
            key=lambda x: _dist_sq(current, (x[0].latitude, x[0].longitude)),
        )
        remaining.remove(best)
        ordered.append(best)
        current = (best[0].latitude, best[0].longitude)
    return ordered + hotels


def save_itinerary(
    db: Session, trip: Trip, result: AIGenerateResult, city_hint: str | None
) -> tuple[int, int, int]:
    """Persist itinerary items. Returns (total, fallback, filtered) counts.

    `fallback` counts places where AMap could not confirm a match, meaning
    the LLM-provided coordinates are used as-is (possible wrong city).
    `filtered` counts places rejected because they conflict with the
    traveler group (e.g. bars in a family trip). Places are re-ordered per
    day with a nearest-neighbour heuristic to cut transit time.
    """
    from app.data.traveler_constraints import place_matches

    traveler_group = trip.traveler_group or "成人"
    total = 0
    fallback = 0
    filtered = 0
    for day in result.days:

        def _fetch(item):
            try:
                results = amap_service.search_places(
                    item.name, city_hint or trip.destination, limit=1
                )
                return item, (results[0] if results else None)
            except Exception:
                return item, None

        with ThreadPoolExecutor(max_workers=6) as pool:
            fetched = list(pool.map(_fetch, day.items))
        enriched: list[tuple] = []
        for item, amap_result in fetched:
            if amap_result:
                place = amap_service.upsert_place(db, amap_result)
            else:
                fallback += 1
                lat = item.latitude
                lng = item.longitude
                place = amap_service.upsert_place(
                    db,
                    {
                        "amap_id": None,
                        "name": item.name,
                        "address": None,
                        "city": city_hint or trip.destination,
                        "category": item.category,
                        "latitude": float(lat) if lat else 0.0,
                        "longitude": float(lng) if lng else 0.0,
                        "rating": None,
                        "cost": None,
                        "image_url": None,
                    },
                )
            if not place_matches(place.category, traveler_group):
                filtered += 1
                continue
            if "暂停开放" in (place.name or "") or "暂停营业" in (place.name or ""):
                filtered += 1
                continue
            cost_estimate = (
                float(place.cost)
                if place.cost
                else _calibrate_cost(item.category, item.cost_estimate)
            )
            enriched.append((place, item, cost_estimate))
            total += 1
        ordered = _order_by_nearest(enriched, city_hint or trip.destination)
        time_slots = [
            it.recommended_time for _, it, _ in ordered if it.recommended_time
        ]
        for idx, (place, item, cost_estimate) in enumerate(ordered):
            recommended_time = item.recommended_time
            if time_slots:
                recommended_time = time_slots[idx % len(time_slots)]
            db.add(
                Schedule(
                    trip_id=trip.id,
                    day=day.day,
                    order_index=idx,
                    place_id=place.id,
                    recommended_time=recommended_time,
                    duration_minutes=item.duration_minutes,
                    cost_estimate=cost_estimate,
                    transport=item.transport,
                    reason=item.reason,
                )
            )
    db.commit()
    return total, fallback, filtered


def save_reoptimized(
    db: Session, trip: Trip, result: AIGenerateResult, city_hint: str | None
) -> None:
    """Replace schedules after re-optimization, reusing known places by name."""
    existing = {s.place.name: s.place for s in trip.schedules}
    db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
    db.flush()
    for day in result.days:
        for idx, item in enumerate(day.items):
            place = existing.get(item.name)
            if place is None:
                place = amap_service.enrich_place(
                    db,
                    item.name,
                    city_hint or trip.destination,
                    {
                        "category": item.category,
                        "latitude": item.latitude,
                        "longitude": item.longitude,
                    },
                )
            db.add(
                Schedule(
                    trip_id=trip.id,
                    day=day.day,
                    order_index=idx,
                    place_id=place.id,
                    recommended_time=item.recommended_time,
                    duration_minutes=item.duration_minutes,
                    cost_estimate=item.cost_estimate,
                    transport=item.transport,
                    reason=item.reason,
                )
            )
    db.commit()
