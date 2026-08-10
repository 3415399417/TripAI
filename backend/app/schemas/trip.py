from __future__ import annotations

import json
from datetime import date, datetime
from typing import List

from pydantic import BaseModel, Field

from app.schemas.place import PlaceOut


class TripCreate(BaseModel):
    destination: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=50)
    budget: float = Field(default=0, ge=0)
    pace: str = Field(default="适中", max_length=32)
    interests: List[str] = Field(default_factory=list)
    travel_style: str = Field(default="城市探索", max_length=32)
    traveler_group: str = Field(default="成人", max_length=16)


class TripUpdate(BaseModel):
    title: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    travelers: int | None = Field(default=None, ge=1, le=50)
    budget: float | None = Field(default=None, ge=0)
    pace: str | None = None
    interests: List[str] | None = None
    travel_style: str | None = None
    traveler_group: str | None = None


class ScheduleItemOut(BaseModel):
    id: int
    day: int
    order_index: int
    place: PlaceOut
    recommended_time: str | None
    duration_minutes: int
    cost_estimate: float
    transport: str | None
    reason: str | None

    model_config = {"from_attributes": True}


class ScheduleUpsertItem(BaseModel):
    day: int = Field(ge=1)
    order_index: int = Field(ge=0)
    place_id: int
    recommended_time: str | None = None
    duration_minutes: int = Field(default=60, ge=1)
    cost_estimate: float = Field(default=0, ge=0)
    transport: str | None = None
    reason: str | None = None


class TripOut(BaseModel):
    id: int
    title: str
    destination: str
    start_date: date
    end_date: date
    travelers: int
    budget: float
    pace: str
    interests: List[str]
    travel_style: str = "城市探索"
    traveler_group: str = "成人"
    traveler_profile: str | None = None
    consumption_level: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    budget_breakdown: dict[str, float] = Field(default_factory=dict)
    city_level: str | None = None
    city_factor: float | None = None
    daily_budget: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    schedules: List[ScheduleItemOut] = Field(default_factory=list)

    @classmethod
    def from_trip(cls, trip: Trip) -> "TripOut":
        interests = json.loads(trip.interests or "[]")
        schedules = [ScheduleItemOut.model_validate(s) for s in trip.schedules]
        try:
            breakdown = json.loads(trip.budget_breakdown or "{}")
        except (ValueError, TypeError):
            breakdown = {}
        return cls(
            id=trip.id,
            title=trip.title,
            destination=trip.destination,
            start_date=trip.start_date,
            end_date=trip.end_date,
            travelers=trip.travelers,
            budget=trip.budget,
            pace=trip.pace,
            interests=interests,
            travel_style=trip.travel_style or "城市探索",
            traveler_group=trip.traveler_group or "成人",
            traveler_profile=trip.traveler_profile,
            consumption_level=trip.consumption_level,
            budget_min=trip.budget_min,
            budget_max=trip.budget_max,
            budget_breakdown=breakdown if isinstance(breakdown, dict) else {},
            city_level=trip.city_level,
            city_factor=trip.city_factor,
            daily_budget=trip.daily_budget,
            status=trip.status,
            created_at=trip.created_at,
            updated_at=trip.updated_at,
            schedules=schedules,
        )
