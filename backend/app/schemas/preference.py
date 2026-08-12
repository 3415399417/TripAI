from __future__ import annotations

from pydantic import BaseModel, Field


class UserPreferenceOut(BaseModel):
    interests: list[str]
    travel_styles: list[str]
    traveler_groups: list[str]
    paces: list[str]
    budget_tier: str | None
    favorite_places: list[str]
    avoid_places: list[str]
    generation_count: int
    summary: str


class UserPreferenceUpdate(BaseModel):
    favorite_places: list[str] | None = Field(default=None, max_length=100)
    avoid_places: list[str] | None = Field(default=None, max_length=100)
