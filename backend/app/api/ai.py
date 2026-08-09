from __future__ import annotations

import json
import threading

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import SessionLocal, get_db
from app.models.trip import Trip
from app.models.user import User
from app.schemas.ai import AIGenerateResponse, ReoptimizeRequest
from app.schemas.trip import TripCreate, TripOut
from app.services import ai_service
from app.services.ai_service import LLMError

settings = get_settings()
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-trip", response_model=AIGenerateResponse, status_code=202)
def generate_trip(
    payload: TripCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIGenerateResponse:
    days = (payload.end_date - payload.start_date).days + 1
    if days < 1:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    title = payload.title or f"{payload.destination} {days}天旅行计划"
    trip_data = payload.model_dump(exclude={"title"})
    trip_data["interests"] = json.dumps(trip_data["interests"], ensure_ascii=False)
    trip = Trip(
        user_id=user.id,
        title=title,
        **trip_data,
        status="draft",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    # 异步后台生成：请求立即返回，前端轮询 trip.status
    threading.Thread(
        target=_generate_worker, args=(trip.id, payload), daemon=True
    ).start()

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="AI 正在规划行程，请稍候…",
    )


def _generate_worker(trip_id: int, payload: TripCreate) -> None:
    """Background generation. Failures delete the draft so polling sees 404."""
    db = SessionLocal()
    try:
        trip = db.get(Trip, trip_id)
        if trip is None:
            return
        result = ai_service.generate_itinerary(payload)
        ai_service.save_itinerary(db, trip, result, city_hint=payload.destination)
        trip.status = "generated"
        db.commit()
    except LLMError:
        db.rollback()
        db.query(Trip).filter(Trip.id == trip_id).delete()
        db.commit()
    finally:
        db.close()


@router.post("/reoptimize", response_model=AIGenerateResponse, status_code=202)
def reoptimize_trip(
    payload: ReoptimizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIGenerateResponse:
    trip = db.get(Trip, payload.trip_id)
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="旅行不存在")
    if not trip.schedules:
        raise HTTPException(status_code=400, detail="行程为空，无法重新优化")

    trip.status = "optimizing"
    db.commit()

    threading.Thread(
        target=_reoptimize_worker,
        args=(trip.id, payload.instruction),
        daemon=True,
    ).start()

    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=not settings.LLM_API_KEY,
        message="AI 正在优化路线，请稍候…",
    )


def _reoptimize_worker(trip_id: int, instruction: str | None) -> None:
    db = SessionLocal()
    try:
        trip = db.get(Trip, trip_id)
        if trip is None:
            return
        result = ai_service.reoptimize_itinerary(db, trip, instruction)
        ai_service.save_reoptimized(db, trip, result, city_hint=trip.destination)
        trip.status = "edited"
        db.commit()
    except LLMError:
        db.rollback()
        trip = db.get(Trip, trip_id)
        if trip is not None:
            trip.status = "edited"  # 保留旧行程
            db.commit()
    finally:
        db.close()
