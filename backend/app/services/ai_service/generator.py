"""Main itinerary generation: orchestrates prompt building, LLM call, and result parsing."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.schemas.ai import AIGenerateResult
from app.schemas.trip import TripCreate

settings = get_settings()


def generate_itinerary(req: TripCreate, feedback: str | None = None) -> AIGenerateResult:
    """Generate a validated itinerary. Falls back to a mock when no key."""
    from app.services.ai_service.prompt import (
        SYSTEM_PROMPT,
        LLMError,
        build_user_prompt,
        last_prompt as _lp,
    )
    from app.services.ai_service.client import (
        _call_llm,
        _parse_json,
        _supports_thinking_param,
    )
    from app.services.ai_service.mock import _mock_itinerary
    from app.services.ai_service.budget import compute_budget_plan
    from app.services import weather_service as weather_svc

    import app.services.ai_service.prompt as prompt_mod

    if not settings.LLM_API_KEY:
        return _mock_itinerary(req)

    user_content = build_user_prompt(req)
    plan = compute_budget_plan(req)
    place_prefs = plan.get("place_preferences") or []
    if place_prefs:
        user_content += (
            "\n地点类型偏好（生成地点时请优先安排这些类型）：\n- "
            + "\n- ".join(place_prefs)
        )
    signature = plan.get("signature_places") or []
    if signature:
        user_content += (
            "\n标志性地点（与你的偏好匹配，优先安排；若因预算或时间限制"
            "无法放入主行程，必须放入 alternatives 备选推荐）：\n- "
            + "\n- ".join(signature)
        )
    constraints = plan.get("constraints") or {}
    if constraints.get("notes"):
        user_content += f"\n旅行约束（必须遵守）：{constraints['notes']}"
    season = plan.get("season") or {}
    if season.get("label") and season["label"] != "平日":
        user_content += (
            f"\n出行时间价格提示：{season['label']}期间，酒店约为平日 "
            f"{season['hotel_factor']} 倍、餐饮 {season['dining_factor']} 倍、"
            f"景点门票 {season['attraction_factor']} 倍，生成地点价格时请按此上浮。"
        )

    weather = weather_svc.get_weather(req.destination, req.start_date)
    if weather and ("雨" in weather["weather"] or "雪" in weather["weather"]):
        user_content += (
            f"\n天气预报：{req.start_date} {req.destination} 为"
            f"{weather['weather']}（{weather['temperature']}°C），"
            "请优先安排室内地点（博物馆、商场、室内乐园），减少户外项目。"
        )
    if feedback:
        user_content += (
            "\n\n上一轮生成的行程存在问题，请严格修正后再输出：\n" + feedback
        )
    prompt_mod.last_prompt = user_content  # set the global

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
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
        data = _parse_json(content)
        return AIGenerateResult.model_validate(data)
    except (ValidationError, ValueError, json.JSONDecodeError) as exc:
        raise LLMError(f"LLM 输出解析失败: {exc}") from exc
