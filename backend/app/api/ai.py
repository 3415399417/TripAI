from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.trip import Trip
from app.models.user import User
from app.schemas.ai import AIGenerateResponse, BudgetRange, ReoptimizeRequest
from app.schemas.trip import TripCreate, TripOut
from app.services import ai_service
from app.services.ai_service import LLMError

settings = get_settings()
router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-trip", response_model=AIGenerateResponse)
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

    try:
        result = ai_service.generate_itinerary(payload)
        total, fallback = ai_service.save_itinerary(
            db, trip, result, city_hint=payload.destination
        )
        # 质量守护：大部分地点无法在目的地城市确认时，带反馈重试一次
        if fallback > 0 and fallback / max(total, 1) > 0.5:
            feedback = (
                f"上一轮输出中部分地点无法在目的地 {payload.destination} 确认，"
                f"请只推荐 {payload.destination} 的真实地点，重新输出完整 JSON。"
            )
            result = ai_service.generate_itinerary(payload, feedback=feedback)
            from app.models.trip import Schedule

            db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
            db.flush()
            ai_service.save_itinerary(
                db, trip, result, city_hint=trip.destination
            )
    except LLMError as exc:
        db.delete(trip)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not result.traveler_profile:
        plan = ai_service.compute_budget_plan(payload)
        result.traveler_profile = plan["profile"]
        result.consumption_level = plan["level"]
        result.budget_range = BudgetRange(**plan["budget_range"])
        result.budget_breakdown = plan["budget_breakdown"]
    trip.traveler_profile = result.traveler_profile
    trip.consumption_level = result.consumption_level
    if result.budget_range:
        trip.budget_min = result.budget_range.min
        trip.budget_max = result.budget_range.max
    trip.budget_breakdown = json.dumps(result.budget_breakdown, ensure_ascii=False)

    trip.status = "generated"
    db.commit()
    db.refresh(trip)

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="行程已生成（当前为示例数据，配置 LLM_API_KEY 后由 AI 生成真实行程）"
        if mock
        else "行程已生成",
    )


@router.post("/reoptimize", response_model=AIGenerateResponse)
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

    try:
        result = ai_service.reoptimize_itinerary(db, trip, payload.instruction)
        ai_service.save_reoptimized(
            db, trip, result, city_hint=trip.destination
        )
    except LLMError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    trip.status = "edited"
    db.commit()

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="已重新优化（示例数据）" if mock else "已重新优化",
    )
