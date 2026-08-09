from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.trip import Schedule, Trip
from app.models.user import User
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


@router.get("/{trip_id}/public", response_model=TripOut)
def get_public_trip(trip_id: int, db: Session = Depends(get_db)) -> TripOut:
    trip = db.get(Trip, trip_id)
    if trip is None or trip.status not in ("generated", "edited"):
        raise HTTPException(status_code=404, detail="分享页面不存在")
    return TripOut.from_trip(trip)


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

