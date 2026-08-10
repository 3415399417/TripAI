"""Mock itinerary generation when no LLM API key is configured."""

from __future__ import annotations

from typing import Any

from app.schemas.ai import AIGenerateResult
from app.models.trip import Trip

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


def _mock_itinerary(req) -> AIGenerateResult:
    from app.services.ai_service.budget import compute_budget_plan

    days_count = (req.end_date - req.start_date).days + 1
    days_count = min(max(days_count, 1), 5)
    lng, lat = _CITY_COORDS.get(req.destination, (116.4074, 39.9042))

    def item_with_coords(item: dict[str, Any], offset: float) -> dict[str, Any]:
        return {
            **item,
            "latitude": round(lat + offset * 0.01, 6),
            "longitude": round(lng + offset * 0.01, 6),
        }

    plan = compute_budget_plan(req)
    return AIGenerateResult(
        traveler_profile=plan["profile"],
        consumption_level=plan["level"],
        budget_range=plan["budget_range"],
        budget_breakdown=plan["budget_breakdown"],
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
    from app.services.ai_service.optimizer import _group_schedules

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
