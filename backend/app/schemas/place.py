import json

from pydantic import BaseModel, field_validator


class PlaceOut(BaseModel):
    id: int
    amap_id: str | None
    name: str
    address: str | None
    city: str | None
    category: str | None
    latitude: float
    longitude: float
    rating: float | None
    cost: float | None
    image_url: str | None
    opening_hours: str | None = None
    phone: str | None = None
    photos: list[str] | None = None

    model_config = {"from_attributes": True}

    @field_validator("photos", mode="before")
    @classmethod
    def _parse_photos(cls, value):
        """DB stores photos as a JSON string; normalize to a list."""
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else None
            except (ValueError, TypeError):
                return None
        return value


class PlaceSearchResult(BaseModel):
    id: int | None
    amap_id: str | None
    name: str
    address: str | None
    city: str | None
    category: str | None
    latitude: float
    longitude: float
    rating: float | None
    cost: float | None
    image_url: str | None
    opening_hours: str | None = None
    phone: str | None = None
    photos: list[str] | None = None

    @field_validator("photos", mode="before")
    @classmethod
    def _parse_photos(cls, value):
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else None
            except (ValueError, TypeError):
                return None
        return value
