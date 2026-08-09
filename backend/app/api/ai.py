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

# ---- 异步任务容错：任务可能因实例重启而中断，轮询 GET 时会自动重拉 ----
_task_lock = threading.Lock()
_running_tasks: set[int] = set()


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

    ensure_task_running(trip.id)

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="AI 正在规划行程，请稍候…",
    )


def ensure_task_running(trip_id: int) -> None:
    """Start the generation/optimization task unless it is already running."""
    with _task_lock:
        if trip_id in _running_tasks:
            return
        _running_tasks.add(trip_id)
    threading.Thread(target=_run_task, args=(trip_id,), daemon=True).start()


def _run_task(trip_id: int) -> None:
    """Background generation/optimization driven by trip.status."""
    db = SessionLocal()
    try:
        trip = db.get(Trip, trip_id)
        if trip is None:
            return
        if trip.status == "draft":
            payload = TripCreate(
                destination=trip.destination,
                start_date=trip.start_date,
                end_date=trip.end_date,
                travelers=trip.travelers,
                budget=trip.budget,
                pace=trip.pace,
                interests=json.loads(trip.interests or "[]"),
            )
            result = ai_service.generate_itinerary(payload)
            ai_service.save_itinerary(
                db, trip, result, city_hint=trip.destination
            )
            trip.status = "generated"
            db.commit()
        elif trip.status == "optimizing":
            result = ai_service.reoptimize_itinerary(db, trip, None)
            ai_service.save_reoptimized(
                db, trip, result, city_hint=trip.destination
            )
            trip.status = "edited"
            db.commit()
    except LLMError:
        db.rollback()
        trip = db.get(Trip, trip_id)
        if trip is not None:
            if trip.status == "draft":
                db.delete(trip)  # 生成失败，草稿删除，轮询将看到 404
            else:
                trip.status = "edited"  # 优化失败保留旧行程
            db.commit()
    finally:
        db.close()
        with _task_lock:
            _running_tasks.discard(trip_id)


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

    ensure_task_running(trip.id)

    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=not settings.LLM_API_KEY,
        message="AI 正在优化路线，请稍候…",
    )
