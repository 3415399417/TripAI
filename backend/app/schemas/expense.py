from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TripExpenseCreate(BaseModel):
    day: int | None = Field(default=None, ge=1, le=31)
    category: str = Field(default="其他", max_length=32)
    description: str | None = Field(default=None, max_length=255)
    amount: float = Field(gt=0, le=1_000_000)


class TripExpenseOut(BaseModel):
    id: int
    trip_id: int
    day: int | None
    category: str
    description: str | None
    amount: float
    created_at: datetime

    model_config = {"from_attributes": True}


class TripExpenseSummary(BaseModel):
    budget: float
    spent: float
    remaining: float
    items: list[TripExpenseOut]
