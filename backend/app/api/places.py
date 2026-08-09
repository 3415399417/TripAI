from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
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

