import re
from typing import Any, List

from pydantic import BaseModel, Field, field_validator

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

    @field_validator("cost_estimate", mode="before")
    @classmethod
    def _parse_cost(cls, value: Any) -> float:
        """GLM-4-Flash sometimes emits strings like '免费' or '约200元/人'."""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = (
                value.replace("约", "")
                .replace("元", "")
                .replace("人民币", "")
                .replace("每人", "")
                .replace("/人", "")
                .replace("人均", "")
                .strip()
            )
            if text in ("免费", "无", "-", "未知", ""):
                return 0.0
            match = re.search(r"\d+(?:\.\d+)?", text)
            return float(match.group()) if match else 0.0
        return 0.0

    @field_validator("duration_minutes", mode="before")
    @classmethod
    def _parse_duration(cls, value: Any) -> int:
        if isinstance(value, (int, float)):
            minutes = int(value)
            # 0 / missing duration -> assume one hour instead of failing
            return 60 if minutes < 10 else min(600, max(10, minutes))
        if isinstance(value, str):
            text = value.strip()
            if "半天" in text:
                return 240
            if "一天" in text or "全天" in text:
                return 480
            match = re.search(r"\d+(?:\.\d+)?", text)
            if match:
                hours = float(match.group())
                if "小时" in text or "h" in text.lower():
                    return max(10, min(600, int(hours * 60)))
                return max(10, min(600, int(hours)))
        return 60


class AIItineraryDay(BaseModel):
    day: int = Field(ge=1)
    items: List[AIPlaceItem] = Field(min_length=1)


class BudgetRange(BaseModel):
    min: float = Field(default=0, ge=0)
    max: float = Field(default=0, ge=0)

    @field_validator("min", "max", mode="before")
    @classmethod
    def _parse_budget_amount(cls, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
            return float(match.group()) if match else 0.0
        return 0.0


class AlternativeItem(BaseModel):
    """An optional suggestion the user can choose to add or swap in."""

    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    cost_estimate: float = Field(default=0, ge=0)
    day: int | None = Field(default=None, ge=1)
    replaces: str | None = None
    reason: str | None = None

    @field_validator("cost_estimate", mode="before")
    @classmethod
    def _parse_cost(cls, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
            return float(match.group()) if match else 0.0
        return 0.0


class AIGenerateResult(BaseModel):
    title: str | None = None
    traveler_profile: str | None = None
    consumption_level: str | None = None
    budget_range: BudgetRange | None = None
    budget_breakdown: dict[str, float] = Field(default_factory=dict)
    days: List[AIItineraryDay] = Field(min_length=1)
    alternatives: List[AlternativeItem] = Field(default_factory=list)

    @field_validator("budget_breakdown", mode="before")
    @classmethod
    def _parse_breakdown(cls, value: Any) -> dict[str, float]:
        if not isinstance(value, dict):
            return {}
        parsed: dict[str, float] = {}
        for key, amount in value.items():
            if isinstance(amount, (int, float)):
                parsed[str(key)] = float(amount)
            elif isinstance(amount, str):
                match = re.search(r"\d+(?:\.\d+)?", amount.replace(",", ""))
                parsed[str(key)] = float(match.group()) if match else 0.0
        return parsed


class AIGenerateResponse(BaseModel):
    trip: TripOut
    mock: bool = False
    message: str = ""


class ReoptimizeRequest(BaseModel):
    trip_id: int
    instruction: str | None = None
