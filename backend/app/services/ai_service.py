"""LLM itinerary generation (OpenAI-compatible chat completions).

Provider is configurable via env vars (DeepSeek / SiliconFlow / Zhipu),
the response is validated against a Pydantic schema, and when no API key
is configured a deterministic mock itinerary keeps the demo runnable.
"""

from __future__ import annotations

import json
import re
from datetime import date
from typing import Any

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.trip import Schedule, Trip
from app.schemas.ai import AIGenerateResult
from app.schemas.trip import TripCreate
from app.services import amap_service

settings = get_settings()


class LLMError(Exception):
    """Raised when the LLM call or its output validation fails."""


SYSTEM_PROMPT = """你是一名专业的旅行规划师，擅长根据用户需求设计节奏合理、可执行的每日行程。
请始终输出严格的 JSON（不要 Markdown 代码块，不要额外解释），格式如下：
{
  "title": "行程标题",
  "days": [
    {
      "day": 1,
      "items": [
        {
          "name": "景点/地点名称",
          "category": "景点|美食|购物|住宿|交通|休闲",
          "latitude": 经度坐标或null,
          "longitude": 纬度坐标或null,
          "reason": "为什么推荐这里",
          "cost_estimate": 人均预估花费(元),
          "duration_minutes": 建议停留时长(分钟),
          "transport": "到达这里的交通方式",
          "recommended_time": "建议时间段，如 09:00-11:00"
        }
      ]
    }
  ]
}
要求：
1. 所有地点必须真实存在于用户指定的目的地城市，严禁推荐其他城市的地点。
2. 每个地点给出中文名，尽量真实、知名、可在地图上找到；同一天不要安排重复地点，整个行程尽量避免重复。
3. 每天 3-6 个地点，按地理位置就近安排，减少来回奔波。
4. 行程天数要与用户填写的日期区间一致。
5. 预算、人数、兴趣偏好、旅行节奏必须体现在行程和花费估计里。
6. 如果无法确定坐标，latitude/longitude 可以给 null，后端会自行校正。
"""


def generate_itinerary(req: TripCreate, feedback: str | None = None) -> AIGenerateResult:
    """Generate a validated itinerary. Falls back to a mock when no key."""
    if not settings.LLM_API_KEY:
        return _mock_itinerary(req)

    user_content = build_user_prompt(req)
    if feedback:
        user_content += (
            "\n\n上一轮生成的行程存在问题，请严格修正后再输出：\n" + feedback
        )

    payload = {
        "model": settings.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
    }
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


def build_user_prompt(req: TripCreate) -> str:
    days = (req.end_date - req.start_date).days + 1
    interests = "、".join(req.interests) if req.interests else "不限"
    return (
        f"目的地：{req.destination}\n"
        f"日期：{req.start_date} 至 {req.end_date}（共 {days} 天）\n"
        f"人数：{req.travelers} 人\n"
        f"总预算：{req.budget:.0f} 元\n"
        f"兴趣偏好：{interests}\n"
        f"旅行节奏：{req.pace}\n"
        f"请生成一份完整的每日行程。"
    )


def save_itinerary(
    db: Session, trip: Trip, result: AIGenerateResult, city_hint: str | None
) -> tuple[int, int]:
    """Persist itinerary items. Returns (total, fallback) place counts.

    `fallback` counts places where AMap could not confirm a match, meaning
    the LLM-provided coordinates are used as-is (possible wrong city).
    """
    total = 0
    fallback = 0
    for day in result.days:
        for idx, item in enumerate(day.items):
            place = amap_service.enrich_place(
                db,
                item.name,
                city_hint or trip.destination,
                {
                    "category": item.category,
                    "latitude": item.latitude,
                    "longitude": item.longitude,
                },
            )
            db.add(
                Schedule(
                    trip_id=trip.id,
                    day=day.day,
                    order_index=idx,
                    place_id=place.id,
                    recommended_time=item.recommended_time,
                    duration_minutes=item.duration_minutes,
                    cost_estimate=item.cost_estimate,
                    transport=item.transport,
                    reason=item.reason,
                )
            )
            total += 1
            if not place.amap_id:
                fallback += 1
    db.commit()
    return total, fallback


def save_reoptimized(
    db: Session, trip: Trip, result: AIGenerateResult, city_hint: str | None
) -> None:
    """Replace schedules after re-optimization, reusing known places by name."""
    existing = {s.place.name: s.place for s in trip.schedules}
    db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
    db.flush()
    for day in result.days:
        for idx, item in enumerate(day.items):
            place = existing.get(item.name)
            if place is None:
                place = amap_service.enrich_place(
                    db,
                    item.name,
                    city_hint or trip.destination,
                    {
                        "category": item.category,
                        "latitude": item.latitude,
                        "longitude": item.longitude,
                    },
                )
            db.add(
                Schedule(
                    trip_id=trip.id,
                    day=day.day,
                    order_index=idx,
                    place_id=place.id,
                    recommended_time=item.recommended_time,
                    duration_minutes=item.duration_minutes,
                    cost_estimate=item.cost_estimate,
                    transport=item.transport,
                    reason=item.reason,
                )
            )
    db.commit()


def reoptimize_itinerary(db: Session, trip: Trip, instruction: str | None) -> AIGenerateResult:
    """Reorder the existing places based on the user's instruction."""
    if not settings.LLM_API_KEY:
        return _mock_reoptimize(trip)

    lines = [
        f"第{s.day}天: " + " -> ".join(f"{s.place.name}({s.recommended_time or '全天'})" for s in day)
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
                    + (f"\n用户要求：{instruction}" if instruction else "\n用户要求：更合理的路线")
                ),
            },
        ],
        "temperature": 0.5,
        "response_format": {"type": "json_object"},
    }
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


def _group_schedules(trip: Trip) -> list[list[Schedule]]:
    grouped: dict[int, list[Schedule]] = {}
    for s in trip.schedules:
        grouped.setdefault(s.day, []).append(s)
    return [grouped[d] for d in sorted(grouped)]


def _call_llm(url: str, headers: dict[str, str], payload: dict[str, Any]) -> str:
    """POST to the LLM provider with one retry on transient timeouts."""
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


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


# ---------------------------------------------------------------- mock mode

_CITY_COORDS: dict[str, tuple[float, float]] = {
    "上海": (121.4737, 31.2304),
    "北京": (116.4074, 39.9042),
    "广州": (113.2644, 23.1291),
    "深圳": (114.0579, 22.5431),
    "杭州": (120.1551, 30.2741),
    "成都": (104.0665, 30.5723),
    "西安": (108.9398, 34.3416),
    "重庆": (106.5516, 29.563),
    "南京": (118.7969, 32.0603),
    "武汉": (114.3055, 30.5931),
    "长沙": (112.9388, 28.2282),
    "三亚": (109.5119, 18.2528),
    "青岛": (120.3826, 36.0671),
    "厦门": (118.0894, 24.4798),
    "昆明": (102.8329, 24.8801),
    "大理": (100.2676, 25.6065),
    "丽江": (100.2296, 26.855),
    "桂林": (110.2900, 25.2736),
    "哈尔滨": (126.6424, 45.7569),
    "乌鲁木齐": (87.6168, 43.8256),
}

_MOCK_PLACES: list[dict[str, Any]] = [
    {
        "name": "市中心历史文化街区",
        "category": "人文景观",
        "reason": "城市最具代表性的历史街区，适合第一天感受当地文化。",
        "cost_estimate": 0,
        "duration_minutes": 120,
        "transport": "地铁/公交",
        "recommended_time": "09:00-11:00",
    },
    {
        "name": "城市标志性观景台",
        "category": "地标建筑",
        "reason": "俯瞰城市全景，拍照打卡的必去地点。",
        "cost_estimate": 60,
        "duration_minutes": 90,
        "transport": "打车或步行",
        "recommended_time": "14:00-15:30",
    },
    {
        "name": "当地特色美食街",
        "category": "美食",
        "reason": "集中品尝当地小吃，晚餐首选。",
        "cost_estimate": 80,
        "duration_minutes": 90,
        "transport": "步行",
        "recommended_time": "17:30-19:00",
    },
    {
        "name": "城市滨水公园",
        "category": "自然风光",
        "reason": "环境优美适合散步放松，行程中段调剂节奏。",
        "cost_estimate": 0,
        "duration_minutes": 90,
        "transport": "公交/骑行",
        "recommended_time": "09:30-11:00",
    },
]


def _mock_itinerary(req: TripCreate) -> AIGenerateResult:
    days_count = (req.end_date - req.start_date).days + 1
    days_count = min(max(days_count, 1), 5)
    lng, lat = _CITY_COORDS.get(req.destination, (116.4074, 39.9042))

    def item_with_coords(item: dict[str, Any], offset: float) -> dict[str, Any]:
        return {
            **item,
            "latitude": round(lat + offset * 0.01, 6),
            "longitude": round(lng + offset * 0.01, 6),
        }

    return AIGenerateResult(
        title=f"{req.destination} {days_count}天旅行计划",
        days=[
            {
                "day": day,
                "items": [
                    item_with_coords(_MOCK_PLACES[(day + i) % len(_MOCK_PLACES)], i + day)
                    for i in range(3)
                ],
            }
            for day in range(1, days_count + 1)
        ],
    )


def _mock_reoptimize(trip: Trip) -> AIGenerateResult:
    """Demo re-optimization: reverse the order of each day's places."""
    days = []
    for day_index, group in enumerate(_group_schedules(trip), start=1):
        items = [
            {
                "name": s.place.name,
                "category": s.place.category or "景点",
                "latitude": s.place.latitude,
                "longitude": s.place.longitude,
                "reason": s.reason,
                "cost_estimate": s.cost_estimate,
                "duration_minutes": s.duration_minutes,
                "transport": s.transport,
                "recommended_time": s.recommended_time,
            }
            for s in reversed(group)
        ]
        days.append({"day": day_index, "items": items})
    return AIGenerateResult(title=trip.title, days=days)
