from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromptVersion(Base):
    """Versioned SYSTEM_PROMPT snapshots to compare generation quality."""

    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    prompt_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

