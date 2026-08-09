from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.place import Place
from app.models.user import User


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(128), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    travelers: Mapped[int] = mapped_column(Integer, default=1)
    budget: Mapped[float] = mapped_column(Float, default=0)
    pace: Mapped[str] = mapped_column(String(32), default="适中")
    interests: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft|generated
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="trips")
    schedules: Mapped[list[Schedule]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="Schedule.day, Schedule.order_index",
    )


class Schedule(Base):
    """One place visit inside a trip, on a given day in a given order."""

    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(
        ForeignKey("trips.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[int] = mapped_column(Integer)
    order_index: Mapped[int] = mapped_column(Integer)
    place_id: Mapped[int] = mapped_column(ForeignKey("places.id"), index=True)
    recommended_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    cost_estimate: Mapped[float] = mapped_column(Float, default=0)
    transport: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    trip: Mapped[Trip] = relationship(back_populates="schedules")
    place: Mapped[Place] = relationship()

