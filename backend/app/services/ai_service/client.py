"""Low-level LLM HTTP client: call, parse, retry, and cost calibration."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------- cost calibration

_COST_RANGES: dict[str, tuple[float, float]] = {
    "美食": (15, 800),
    "餐饮": (15, 800),
    "景点": (0, 500),
    "门票": (0, 500),
    "住宿": (80, 5000),
    "娱乐": (0, 1000),
    "购物": (0, 5000),
    "交通": (0, 800),
}


def _calibrate_cost(category: str | None, value: float | None) -> float:
    """Clamp an LLM cost guess to a plausible range for its category.

    AMap's real per-capita cost wins when available; otherwise this keeps
    model estimates from being wildly off from typical market prices.
    """
    low, high = 0.0, 100000.0
    if category:
        for key, (lo, hi) in _COST_RANGES.items():
            if key in category:
                low, high = lo, hi
                break
    try:
        num = float(value or 0)
    except (TypeError, ValueError):
        num = 0.0
    return max(low, min(high, num))


# ---------------------------------------------------------------- HTTP helpers


def _call_llm(url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
    """POST to the LLM provider with one retry on transient timeouts."""
    from app.services.ai_service.prompt import LLMError

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            resp = httpx.post(
                url, json=payload, headers=headers, timeout=settings.LLM_TIMEOUT_SECONDS
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            last_error = exc
            continue
        except Exception as exc:
            raise LLMError(f"LLM 调用失败: {exc}") from exc
    raise LLMError(f"LLM 调用失败（已自动重试一次）: {last_error}")


def _supports_thinking_param() -> bool:
    """SiliconFlow / DeepSeek accept a `thinking` param; other providers may not."""
    base = settings.LLM_BASE_URL.lower()
    return "siliconflow" in base or "deepseek.com" in base


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)
