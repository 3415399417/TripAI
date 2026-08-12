from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.place import Place
from app.schemas.place import PlaceSearchResult
from app.services import amap_service
from app.services.amap_service import AMapError, AMapNotConfigured

router = APIRouter(prefix="/places", tags=["places"])


@router.get("/search", response_model=list[PlaceSearchResult])
def search_places(
    q: str = Query(min_length=1, max_length=128),
    city: str | None = Query(default=None, max_length=128),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlaceSearchResult]:
    try:
        results = amap_service.search_places(q, city, limit=10)
    except AMapNotConfigured as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AMapError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    saved: list[PlaceSearchResult] = []
    for raw in results:
        place = amap_service.upsert_place(db, raw)
        saved.append(
            PlaceSearchResult(
                id=place.id,
                **{k: v for k, v in raw.items() if k != "amap_id"},
                amap_id=place.amap_id,
            )
        )
    db.commit()
    return saved


@router.get("/{place_id}/detail", response_model=PlaceSearchResult)
def get_place_detail(
    place_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlaceSearchResult:
    """Return cached place info; lazily enrich hours/phone/photos from AMap."""
    place = db.get(Place, place_id)
    if place is None:
        raise HTTPException(status_code=404, detail="地点不存在")

    if place.amap_id and (not place.opening_hours or not place.phone):
        try:
            detail = amap_service.fetch_place_detail(place.amap_id)
        except (AMapNotConfigured, AMapError):
            detail = {}
        if detail.get("photos"):
            place.photos = json.dumps(detail["photos"], ensure_ascii=False)
        for key in ("opening_hours", "phone"):
            if detail.get(key):
                setattr(place, key, detail[key])
        db.commit()
        db.refresh(place)

    photos = None
    if place.photos:
        try:
            photos = json.loads(place.photos)
        except (ValueError, TypeError):
            photos = None
    return PlaceSearchResult(
        id=place.id,
        amap_id=place.amap_id,
        name=place.name,
        address=place.address,
        city=place.city,
        category=place.category,
        latitude=place.latitude,
        longitude=place.longitude,
        rating=place.rating,
        cost=place.cost,
        image_url=place.image_url,
        opening_hours=place.opening_hours,
        phone=place.phone,
        photos=photos,
    )
