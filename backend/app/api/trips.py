from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.trip import Schedule, Trip, TripExpense
from app.models.user import User
from app.schemas.expense import TripExpenseCreate, TripExpenseOut, TripExpenseSummary
from app.schemas.trip import ScheduleUpsertItem, TripOut, TripUpdate

router = APIRouter(prefix="/trips", tags=["trips"])


def _get_owned_trip(db: Session, trip_id: int, user: User) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="旅行不存在")
    return trip


@router.get("", response_model=list[TripOut])
def list_trips(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[TripOut]:
    trips = (
        db.query(Trip)
        .filter(Trip.user_id == user.id)
        .order_by(Trip.created_at.desc())
        .all()
    )
    return [TripOut.from_trip(t) for t in trips]


@router.get("/{trip_id}", response_model=TripOut)
def get_trip(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripOut:
    return TripOut.from_trip(_get_owned_trip(db, trip_id, user))


@router.get("/{trip_id}/generation-log")
def get_generation_log(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return the full generation log for a trip (for debugging/training)."""
    _get_owned_trip(db, trip_id, user)
    from app.models.generation_log import GenerationLog

    log = (
        db.query(GenerationLog)
        .filter(GenerationLog.trip_id == trip_id)
        .order_by(GenerationLog.id.desc())
        .first()
    )
    if log is None:
        return {"detail": "暂无生成日志"}

    def _load(value: str | None) -> object | None:
        if not value:
            return None
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value

    return {
        "id": log.id,
        "payload": _load(log.payload),
        "plan": _load(log.plan),
        "prompt": log.prompt,
        "ai_output": _load(log.ai_output),
        "final_result": _load(log.final_result),
        "created_at": str(log.created_at),
    }


@router.get("/{trip_id}/public", response_model=TripOut)
def get_public_trip(trip_id: int, db: Session = Depends(get_db)) -> TripOut:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.status not in ("generated", "edited"):
        raise HTTPException(status_code=404, detail="分享页面不存在")
    return TripOut.from_trip(trip)


def _weather_payload(trip: Trip) -> dict:
    from app.services.weather_service import get_weather_forecast

    info = get_weather_forecast(trip.destination, trip.start_date, trip.end_date)
    return {
        "destination": trip.destination,
        "start_date": trip.start_date.isoformat(),
        "end_date": trip.end_date.isoformat(),
        "days": info["days"],
        "live": info["live"],
        "within_window": info["within_window"],
        "fallback": trip.weather,
    }


@router.get("/{trip_id}/weather")
def get_trip_weather(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Per-day weather for the trip dates plus live weather (cached 30 min)."""
    return _weather_payload(_get_owned_trip(db, trip_id, user))


@router.get("/{trip_id}/public/weather")
def get_public_trip_weather(trip_id: int, db: Session = Depends(get_db)) -> dict:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.status not in ("generated", "edited"):
        raise HTTPException(status_code=404, detail="分享页面不存在")
    return _weather_payload(trip)


@router.put("/{trip_id}", response_model=TripOut)
def update_trip(
    trip_id: int,
    payload: TripUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripOut:
    trip = _get_owned_trip(db, trip_id, user)
    changes = payload.model_dump(exclude_unset=True)
    if "interests" in changes and changes["interests"] is not None:
        changes["interests"] = json.dumps(changes["interests"], ensure_ascii=False)
    for key, value in changes.items():
        setattr(trip, key, value)
    db.commit()
    db.refresh(trip)
    return TripOut.from_trip(trip)


@router.put("/{trip_id}/schedule", response_model=TripOut)
def replace_schedule(
    trip_id: int,
    items: list[ScheduleUpsertItem],
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripOut:
    trip = _get_owned_trip(db, trip_id, user)
    db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
    for item in items:
        db.add(
            Schedule(
                trip_id=trip.id,
                day=item.day,
                order_index=item.order_index,
                place_id=item.place_id,
                recommended_time=item.recommended_time,
                duration_minutes=item.duration_minutes,
                cost_estimate=item.cost_estimate,
                transport=item.transport,
                reason=item.reason,
            )
        )
    trip.status = "edited"
    db.commit()
    db.refresh(trip)
    return TripOut.from_trip(trip)


@router.delete("/{trip_id}", status_code=204)
def delete_trip(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    trip = _get_owned_trip(db, trip_id, user)
    db.delete(trip)
    db.commit()


@router.get("/{trip_id}/expenses", response_model=TripExpenseSummary)
def list_expenses(
    trip_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripExpenseSummary:
    trip = _get_owned_trip(db, trip_id, user)
    items = (
        db.query(TripExpense)
        .filter(TripExpense.trip_id == trip.id)
        .order_by(TripExpense.day.asc().nullsfirst(), TripExpense.id.desc())
        .all()
    )
    spent = round(sum(item.amount for item in items), 2)
    return TripExpenseSummary(
        budget=trip.budget,
        spent=spent,
        remaining=round(max(0, trip.budget - spent), 2),
        items=[TripExpenseOut.model_validate(item) for item in items],
    )


@router.post("/{trip_id}/expenses", response_model=TripExpenseOut, status_code=201)
def add_expense(
    trip_id: int,
    payload: TripExpenseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TripExpenseOut:
    trip = _get_owned_trip(db, trip_id, user)
    item = TripExpense(trip_id=trip.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return TripExpenseOut.model_validate(item)


@router.delete("/{trip_id}/expenses/{expense_id}", status_code=204)
def delete_expense(
    trip_id: int,
    expense_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    trip = _get_owned_trip(db, trip_id, user)
    item = (
        db.query(TripExpense)
        .filter(TripExpense.id == expense_id, TripExpense.trip_id == trip.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="记账记录不存在")
    db.delete(item)
    db.commit()
