"""Re-optimization: regenerate itinerary with user feedback on existing plans."""

from __future__ import annotations

import json

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.trip import Schedule, Trip
from app.schemas.ai import AIGenerateResult

settings = get_settings()


def _group_schedules(trip: Trip) -> list[list[Schedule]]:
    grouped: dict[int, list[Schedule]] = {}
    for s in trip.schedules:
        grouped.setdefault(s.day, []).append(s)
    return [grouped[d] for d in sorted(grouped)]


def reoptimize_itinerary(
    db: Session, trip: Trip, instruction: str | None
) -> AIGenerateResult:
    """Reorder the existing places based on the user's instruction."""
    from app.services.ai_service.prompt import SYSTEM_PROMPT, LLMError
    from app.services.ai_service.client import (
        _call_llm,
        _parse_json,
        _supports_thinking_param,
    )
    from app.services.ai_service.mock import _mock_reoptimize

    if not settings.LLM_API_KEY:
        return _mock_reoptimize(trip)

    lines = [
        f"第{s.day}天: "
        + " -> ".join(
            f"{s.place.name}({s.recommended_time or '全天'})" for s in day
        )
        for day in _group_schedules(trip)
    ]
    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "以下是当前行程，请重新优化（可以调整每天的安排顺序、时间，"
                    "但必须保留这些地点本身，不要新增或删除）：\n"
                    + "\n".join(lines)
                    + (
                        f"\n用户要求：{instruction}"
                        if instruction
                        else "\n用户要求：更合理的路线"
                    )
                ),
            },
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
    }
    if _supports_thinking_param():
        payload["thinking"] = {"type": "disabled"}
    url = settings.LLM_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    content = _call_llm(url, headers, payload)

    try:
        return AIGenerateResult.model_validate(_parse_json(content))
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise LLMError(f"LLM 输出解析失败: {exc}") from exc
