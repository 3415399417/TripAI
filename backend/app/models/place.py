from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Place(Base):
    """POI cache backed by AMap search results (saves the 100/day quota)."""

    __tablename__ = "places"

    id: Mapped[int] = mapped_column(primary_key=True)
    amap_id: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), index=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
