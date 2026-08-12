from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserPreference(Base):
    """Implicit user profile learned from generations and edits.

    Counters are stored as JSON objects ({value: count}) so the most common
    preferences can be derived without losing history.
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    interests: Mapped[str] = mapped_column(Text, default="{}")  # {tag: count}
    travel_styles: Mapped[str] = mapped_column(Text, default="{}")
    traveler_groups: Mapped[str] = mapped_column(Text, default="{}")
    paces: Mapped[str] = mapped_column(Text, default="{}")
    budget_tiers: Mapped[str] = mapped_column(Text, default="{}")
    favorite_places: Mapped[str] = mapped_column(Text, default="{}")
    avoid_places: Mapped[str] = mapped_column(Text, default="{}")
    generation_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="preference")
