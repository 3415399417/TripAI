from typing import List

from pydantic import BaseModel, Field

from app.schemas.trip import TripOut


class AIPlaceItem(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    category: str = Field(default="景点", max_length=64)
    latitude: float | None = None
    longitude: float | None = None
    reason: str | None = None
    cost_estimate: float = Field(default=0, ge=0)
    duration_minutes: int = Field(default=60, ge=10, le=600)
    transport: str | None = None
    recommended_time: str | None = None


class AIItineraryDay(BaseModel):
    day: int = Field(ge=1)
    items: List[AIPlaceItem] = Field(min_length=1)


class AIGenerateResult(BaseModel):
    title: str | None = None
    days: List[AIItineraryDay] = Field(min_length=1)


class AIGenerateResponse(BaseModel):
    trip: TripOut
    mock: bool = False
    message: str = ""


class ReoptimizeRequest(BaseModel):
    trip_id: int
    instruction: str | None = None
