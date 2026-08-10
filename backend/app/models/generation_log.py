from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GenerationLog(Base):
    """Full record of one AI generation for future model training."""

    __tablename__ = "generation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trip_id: Mapped[int | None] = mapped_column(
        ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    payload: Mapped[str] = mapped_column(Text)  # user input JSON
    plan: Mapped[str | None] = mapped_column(Text, nullable=True)  # rule result
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)  # user prompt
    ai_output: Mapped[str | None] = mapped_column(Text, nullable=True)  # parsed AI JSON
    final_result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

