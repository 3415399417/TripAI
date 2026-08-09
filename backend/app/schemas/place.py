from pydantic import BaseModel


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
    image_url: str | None

    model_config = {"from_attributes": True}


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
    image_url: str | None

