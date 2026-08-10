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


SYSTEM_PROMPT = """你是一位专业的智能旅行规划师。核心原则：用户填写的预算是消费能力和旅行期望，不是必须花完的钱。你要判断消费等级，并结合城市消费水平、旅行天数、兴趣偏好，生成个性化行程和预算规划。

## 一、判断消费等级
先计算：人均每日预算 = 总预算 ÷ 人数 ÷ 天数。
再按目的地城市消费水平修正：
- 一线城市（北京/上海/广州/深圳）：系数 1.0
- 新一线城市（成都/杭州/重庆/武汉/西安/苏州/天津/南京/长沙/郑州/东莞/青岛/沈阳/宁波/昆明等）：系数 0.85
- 二线城市：系数 0.7
- 三四线及小众旅游城市：系数 0.55

有效人均日预算 = 人均每日预算 ÷ 城市系数。分档：
- 经济型：有效人均日预算 ≤ 400 元
- 舒适型：400～1000 元
- 高品质：1000～2500 元
- 奢华型：> 2500 元

示例：上海3天2人预算3000元，人均每日500元，属于经济偏舒适，应按经济型执行，实际消费控制在2500元左右，剩余作为弹性资金；上海3天1人预算30000元，人均每日10000元，属于奢华型，必须按高品质/奢华标准规划，绝不能按低消费标准。

## 二、预算分配参考比例（占总预算）
- 经济型：住宿32%、餐饮26%、交通16%、景点门票12%、娱乐体验6%、购物4%、备用4%
- 舒适型：住宿35%、餐饮24%、交通15%、景点门票10%、娱乐体验7%、购物5%、备用4%
- 高品质：住宿40%、餐饮22%、交通14%、景点门票8%、娱乐体验8%、购物5%、备用3%
- 奢华型：住宿45%、餐饮20%、交通12%、景点门票6%、娱乐体验10%、购物5%、备用2%

结合兴趣动态调整：
- 美食偏好：提高餐饮占比（可上调5～10个百分点），相应降低住宿或购物
- 摄影偏好：增加免费/高价值景观机位，控制购物
- 购物偏好：提高购物占比，安排商圈时间
- 自然偏好：增加户外/景区体验

所有地点 cost_estimate 均为人均花费。预算分配合计应落在建议预算区间内，且不得超过用户总预算。备用资金体现"预算不是必须花完"的原则。

## 三、旅行节奏与天数
- 1～2天：每天4～5个点，优先核心景点，密度较高
- 3～4天：每天3～4个点，核心+特色搭配
- 5天以上：每天2～3个点，增加休闲时间，避免赶路

第一天和最后一天适当考虑到达/返程交通，中间日期是主要体验消费。

## 四、住宿必须体现等级
每天行程末尾安排一个住宿地点（category为"住宿"，如"XX酒店"或"XX区域住宿推荐"），品质必须与消费等级匹配：经济型=经济连锁/青旅；舒适型=舒适型酒店；高品质=四星及以上酒店；奢华型=五星奢华酒店。入住时间建议 20:00 后。

## 五、输出 JSON（必须严格 JSON，不要 Markdown 代码块，不要额外解释）
{
  "title": "行程标题",
  "traveler_profile": "旅行画像，如：上海3天经济型城市探索旅行者",
  "consumption_level": "经济型|舒适型|高品质|奢华型",
  "budget_range": {"min": 建议最低消费, "max": 建议最高消费},
  "budget_breakdown": {"住宿": 金额, "餐饮": 金额, "交通": 金额, "景点门票": 金额, "娱乐体验": 金额, "购物": 金额, "备用资金": 金额},
  "days": [
    {
      "day": 1,
      "items": [
        {
          "name": "地点名称",
          "category": "景点|美食|购物|住宿|交通|休闲",
          "latitude": 经度坐标或null,
          "longitude": 纬度坐标或null,
          "reason": "一句话推荐理由(不超过25字)",
          "cost_estimate": 人均花费(元),
          "duration_minutes": 建议停留分钟数,
          "transport": "到达这里的交通方式",
          "recommended_time": "建议时间，如09:00-11:00"
        }
      ]
    }
  ]
}

## 六、地点要求
1. 所有地点必须真实存在于用户指定目的地城市，严禁推荐其他城市的地点
2. 中文名称，真实、知名、地图上可搜到；同一天不重复，整个行程避免重复
3. 按地理位置就近安排路线，减少来回奔波
4. 行程天数必须与用户填写的日期区间一致
5. 预算、人数、兴趣偏好、旅行节奏必须体现在行程和花费估计中
6. 无法确定坐标时 latitude/longitude 给 null，后端会自动校正
7. reason 用一句话，不超过25字
8. 高预算绝不能用低消费标准规划，低预算绝不推荐奢侈消费；住宿、餐饮、交通品质必须与消费等级一致
## 七、花费自检（重要）
输出前必须核算全部 items（含每天住宿地点）的 cost_estimate 总和：
- 高品质/奢华型行程：总花费应达到建议消费区间下限的 75% 以上，越接近区间中值越好
- 高等级行程必须包含与等级匹配的地点：高档餐厅人均 150 元以上、高品质酒店每晚 800 元以上（奢华型 1500 元以上）、特色体验项目、精品购物等
- 经济型/舒适型：保持性价比，总花费也应落在建议消费区间附近（不低于区间下限的 60%）
- 不允许用大量人均 50 元以下的地点拼凑高预算行程；若当前地点组合总花费过低，请升级部分地点的品质或替换为更高消费的同类真实地点"""


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
    if _supports_thinking_param():
        # Thinking mode roughly triples latency; itinerary JSON doesn't need it.
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
            cost_estimate = (
                float(place.cost)
                if place.cost
                else _calibrate_cost(item.category, item.cost_estimate)
            )
            db.add(
                Schedule(
                    trip_id=trip.id,
                    day=day.day,
                    order_index=idx,
                    place_id=place.id,
                    recommended_time=item.recommended_time,
                    duration_minutes=item.duration_minutes,
                    cost_estimate=cost_estimate,
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


# ---------------------------------------------------------------- mock mode

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

_CITY_FACTOR_LEVELS: dict[str, float] = {
    "北京": 1.0,
    "上海": 1.0,
    "广州": 1.0,
    "深圳": 1.0,
    "成都": 0.85,
    "杭州": 0.85,
    "重庆": 0.85,
    "武汉": 0.85,
    "西安": 0.85,
    "苏州": 0.85,
    "天津": 0.85,
    "南京": 0.85,
    "长沙": 0.85,
    "郑州": 0.85,
    "东莞": 0.85,
    "青岛": 0.85,
    "沈阳": 0.85,
    "宁波": 0.85,
    "昆明": 0.85,
}

_LEVEL_RATIOS: dict[str, dict[str, float]] = {
    "经济型": {
        "住宿": 0.32,
        "餐饮": 0.26,
        "交通": 0.16,
        "景点门票": 0.12,
        "娱乐体验": 0.06,
        "购物": 0.04,
        "备用资金": 0.04,
    },
    "舒适型": {
        "住宿": 0.35,
        "餐饮": 0.24,
        "交通": 0.15,
        "景点门票": 0.10,
        "娱乐体验": 0.07,
        "购物": 0.05,
        "备用资金": 0.04,
    },
    "高品质": {
        "住宿": 0.40,
        "餐饮": 0.22,
        "交通": 0.14,
        "景点门票": 0.08,
        "娱乐体验": 0.08,
        "购物": 0.05,
        "备用资金": 0.03,
    },
    "奢华型": {
        "住宿": 0.45,
        "餐饮": 0.20,
        "交通": 0.12,
        "景点门票": 0.06,
        "娱乐体验": 0.10,
        "购物": 0.05,
        "备用资金": 0.02,
    },
}

_LEVEL_TAGS: dict[str, str] = {
    "经济型": "城市探索",
    "舒适型": "品质休闲",
    "高品质": "深度体验",
    "奢华型": "尊享之旅",
}


def _city_cost_factor(destination: str) -> float:
    """Rough cost-of-living factor used to judge consumption level."""
    return _CITY_FACTOR_LEVELS.get(destination, 0.7)


def compute_budget_plan(req: TripCreate) -> dict[str, Any]:
    """Determine consumption level, suggested range and budget breakdown.

    Budget is interpreted as spending power, not a target to be fully spent.
    """
    days = (req.end_date - req.start_date).days + 1
    per_day = req.budget / max(days, 1) / max(req.travelers, 1)
    effective = per_day / _city_cost_factor(req.destination)
    if effective <= 400:
        level = "经济型"
    elif effective <= 1000:
        level = "舒适型"
    elif effective <= 2500:
        level = "高品质"
    else:
        level = "奢华型"

    interest = req.interests[0] if req.interests else ""
    profile = f"{req.destination}{days}天{level}"
    if interest:
        profile += f"·{interest}偏好"
    profile += _LEVEL_TAGS[level] + "旅行者"

    base = round(req.budget * 0.9)
    breakdown = {
        key: round(base * ratio) for key, ratio in _LEVEL_RATIOS[level].items()
    }
    return {
        "profile": profile,
        "level": level,
        "budget_range": {
            "min": round(req.budget * 0.85),
            "max": round(req.budget * 0.93),
        },
        "budget_breakdown": breakdown,
    }

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
