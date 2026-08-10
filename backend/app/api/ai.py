from __future__ import annotations

import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.trip import Trip
from app.models.user import User
from app.schemas.ai import AIGenerateResponse, BudgetRange, ReoptimizeRequest
from app.schemas.trip import TripCreate, TripOut
from app.services import ai_service
from app.services.ai_service import LLMError

settings = get_settings()
router = APIRouter(prefix="/ai", tags=["ai"])


def _sum_costs(result) -> float:
    return sum(
        item.cost_estimate for day in result.days for item in day.items
    )


def _tier_quality_check(result, payload) -> tuple[bool, str]:
    """Ensure hotels / dining / experiences match the budget tier.

    Budget is spending power, not a spend-all target, so we verify the
    *quality tier* of the plan rather than forcing total spend upward.
    """
    from app.data import cities, tiers as tier_rules

    days = (payload.end_date - payload.start_date).days + 1
    per_day = payload.budget / max(days, 1) / max(payload.travelers, 1)
    effective = per_day / cities.city_factor(payload.destination)
    tier = tier_rules.TIER_RULES[tier_rules.classify(effective)]
    hotel_min = tier["hotel_range"][0]
    dining_min = round(tier["dining_per_day"][0] / 3)
    exp_min = round(tier["hotel_range"][0] / 4)

    hotels: list[float] = []
    dining: list[float] = []
    experiences: list[float] = []
    for day in result.days:
        for item in day.items:
            category = item.category or ""
            if "住宿" in category:
                hotels.append(item.cost_estimate)
            elif "餐饮" in category or "美食" in category:
                dining.append(item.cost_estimate)
            elif "娱乐" in category or "购物" in category:
                experiences.append(item.cost_estimate)

    avg_hotel = sum(hotels) / len(hotels) if hotels else 0.0
    fancy_dining = sum(1 for c in dining if c >= dining_min)
    fancy_exp = sum(1 for c in experiences if c >= exp_min)

    if hotels and avg_hotel < hotel_min:
        return False, (
            f"住宿均价 {round(avg_hotel)} 元低于该预算等级应有的 {hotel_min} 元，"
            "请升级酒店档次"
        )
    if dining and fancy_dining < 2:
        return False, (
            f"人均 {dining_min} 元以上的高档餐厅只有 {fancy_dining} 家，"
            "请至少安排 2 家与消费等级匹配的餐厅"
        )
    if experiences and fancy_exp < 1:
        return False, (
            f"缺少人均 {exp_min} 元以上的娱乐/购物体验，请增加 1 个"
        )
    total = _sum_costs(result)
    if total < payload.budget * 0.35:
        return False, (
            f"行程总花费 {round(total)} 元过低，请整体提升消费档次"
        )
    return True, ""


_INTEREST_KEYWORDS: dict[str, tuple[str, ...]] = {
    "美食": ("餐饮", "美食", "小吃", "餐厅", "食"),
    "购物": ("购物", "商场", "商圈", "品牌"),
    "亲子": ("亲子", "乐园", "博物馆", "科技馆", "动物园", "海洋馆"),
    "自然风光": ("公园", "湖", "山", "海", "湿地", "森林"),
    "户外": ("徒步", "户外", "登山", "骑行"),
    "人文历史": ("博物馆", "历史", "古", "遗址", "故居", "寺"),
    "摄影": ("观景", "地标", "塔", "江", "天台", "天际"),
    "夜生活": ("酒吧", "演出", "夜市", "夜景", "live"),
    "休闲度假": ("咖啡", "温泉", "海", "度假", "spa"),
    "艺术": ("美术", "艺术", "展览", "创意"),
    "展览": ("美术", "艺术", "展览", "科技馆"),
    "深度游": ("小巷", "街", "在地", "工艺"),
}


def _interest_hit(result, interest: str) -> bool:
    keywords = _INTEREST_KEYWORDS.get(interest)
    if not keywords:
        return True
    for day in result.days:
        for item in day.items:
            text = f"{item.name} {item.category or ''}"
            if any(keyword in text for keyword in keywords):
                return True
    return False


def _route_score(result) -> int:
    """Score how geographically clustered each day's route is."""
    day_scores: list[int] = []
    for day in result.days:
        points = [(i.latitude or 0, i.longitude or 0) for i in day.items]
        if len(points) < 2:
            day_scores.append(100)
            continue
        spans = [
            (points[i][0] - points[i - 1][0]) ** 2
            + (points[i][1] - points[i - 1][1]) ** 2
            for i in range(1, len(points))
        ]
        avg = sum(spans) / len(spans)
        score = max(0, 100 - round(avg / 0.0008 * 100))
        day_scores.append(min(100, score))
    return round(sum(day_scores) / len(day_scores)) if day_scores else 100


def _score_plan(result, payload) -> dict:
    """Rule-based generation score (0-100 per dimension)."""
    total_cost = _sum_costs(result)
    budget = max(float(payload.budget or 0), 1)
    low, high = budget * 0.85, budget * 0.93
    if low <= total_cost <= high:
        budget_match = 100
    elif total_cost < low:
        budget_match = max(0, 100 - round((low - total_cost) / low * 60))
    else:
        budget_match = max(0, 100 - round((total_cost - high) / high * 80))

    interests = payload.interests or []
    if interests:
        matched = sum(1 for interest in interests if _interest_hit(result, interest))
        interest_match = round(matched / len(interests) * 100)
    else:
        interest_match = 100

    route_reason = _route_score(result)
    ok, _ = _tier_quality_check(result, payload)
    quality_match = 100 if ok else 55
    total = round(
        budget_match * 0.3
        + interest_match * 0.2
        + route_reason * 0.2
        + quality_match * 0.3
    )
    return {
        "total": total,
        "budget_match": budget_match,
        "interest_match": interest_match,
        "route_reason": route_reason,
        "quality_match": quality_match,
    }


@router.post("/generate-trip", response_model=AIGenerateResponse)
def generate_trip(
    payload: TripCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIGenerateResponse:
    days = (payload.end_date - payload.start_date).days + 1
    if days < 1:
        raise HTTPException(status_code=400, detail="结束日期不能早于开始日期")

    title = payload.title or f"{payload.destination} {days}天旅行计划"
    trip_data = payload.model_dump(exclude={"title"})
    trip_data["interests"] = json.dumps(trip_data["interests"], ensure_ascii=False)
    trip = Trip(
        user_id=user.id,
        title=title,
        **trip_data,
        status="draft",
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)

    llm_seconds = 0.0
    save_seconds = 0.0
    try:
        t_llm = time.time()
        result = ai_service.generate_itinerary(payload)
        llm_seconds += time.time() - t_llm
        ok, quality_feedback = _tier_quality_check(result, payload)
        score = _score_plan(result, payload)
        reasons: list[str] = []
        if not ok:
            reasons.append(quality_feedback)
        if score["total"] < 62:
            reasons.append(
                f"综合评分 {score['total']}/100（预算匹配{score['budget_match']}、"
                f"兴趣匹配{score['interest_match']}、路线合理{score['route_reason']}、"
                f"消费符合{score['quality_match']}），请针对性优化："
                "预算接近建议区间、地点符合兴趣、路线减少跨区奔波、消费档次匹配等级。"
            )
        if reasons:
            feedback = (
                "；".join(reasons)
                + "，重新输出完整 JSON，保持地点真实且符合目的地城市。"
            )
            t_llm = time.time()
            result = ai_service.generate_itinerary(payload, feedback=feedback)
            llm_seconds += time.time() - t_llm
        t_save = time.time()
        total, fallback, filtered = ai_service.save_itinerary(
            db, trip, result, city_hint=payload.destination
        )
        save_seconds += time.time() - t_save
        # 质量守护：大部分地点无法在目的地城市确认时，带反馈重试一次
        if fallback > 0 and fallback / max(total, 1) > 0.5:
            feedback = (
                f"上一轮输出中部分地点无法在目的地 {payload.destination} 确认，"
                f"请只推荐 {payload.destination} 的真实地点，重新输出完整 JSON。"
            )
            t_llm = time.time()
            result = ai_service.generate_itinerary(payload, feedback=feedback)
            llm_seconds += time.time() - t_llm
            from app.models.trip import Schedule

            db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
            db.flush()
            t_save = time.time()
            ai_service.save_itinerary(
                db, trip, result, city_hint=trip.destination
            )
            save_seconds += time.time() - t_save
        elif filtered > 0 and filtered / max(total + filtered, 1) > 0.3:
            feedback = (
                f"上一轮有 {filtered} 个地点不适合随行人群"
                f"（{payload.traveler_group or '成人'}），例如酒吧/夜店不适合儿童、"
                "高强度项目不适合老人。请重新生成符合该人群的完整行程。"
            )
            t_llm = time.time()
            result = ai_service.generate_itinerary(payload, feedback=feedback)
            llm_seconds += time.time() - t_llm
            from app.models.trip import Schedule

            db.query(Schedule).filter(Schedule.trip_id == trip.id).delete()
            db.flush()
            t_save = time.time()
            ai_service.save_itinerary(
                db, trip, result, city_hint=trip.destination
            )
            save_seconds += time.time() - t_save
    except LLMError as exc:
        db.delete(trip)
        db.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # 消费等级/预算区间/分配由专家知识库确定性计算并覆盖 AI 输出，
    # AI 只负责生成符合该等级的地点。
    plan = ai_service.compute_budget_plan(payload)
    result.traveler_profile = plan["profile"]
    result.consumption_level = plan["level"]
    result.budget_range = BudgetRange(**plan["budget_range"])
    result.budget_breakdown = plan["budget_breakdown"]
    trip.traveler_profile = result.traveler_profile
    trip.consumption_level = result.consumption_level
    if result.budget_range:
        trip.budget_min = result.budget_range.min
        trip.budget_max = result.budget_range.max
    trip.budget_breakdown = json.dumps(result.budget_breakdown, ensure_ascii=False)
    trip.alternatives = json.dumps(
        [item.model_dump() for item in result.alternatives],
        ensure_ascii=False,
    )
    trip.city_level = plan["city_level"]
    trip.city_factor = plan["city_factor"]
    trip.daily_budget = plan["daily_budget"]
    from app.services.weather_service import get_weather

    weather_info = get_weather(payload.destination, payload.start_date)
    trip.weather = (
        f"{weather_info['weather']} {weather_info['temperature']}°C"
        if weather_info
        else None
    )
    score_final = _score_plan(result, payload)
    trip.score_total = score_final["total"]
    trip.score_detail = json.dumps(score_final, ensure_ascii=False)
    trip.llm_seconds = round(llm_seconds, 1)

    trip.status = "generated"
    db.commit()
    db.refresh(trip)

    from app.models.generation_log import GenerationLog

    db.add(
        GenerationLog(
            user_id=user.id,
            trip_id=trip.id,
            payload=payload.model_dump_json(),
            plan=json.dumps(plan, ensure_ascii=False, default=str),
            prompt=ai_service.last_prompt,
            ai_output=result.model_dump_json(),
            final_result=json.dumps(
                {
                    "trip_id": trip.id,
                    "status": trip.status,
                    "schedules": len(trip.schedules),
                    "score": _score_plan(result, payload),
                    "llm_seconds": round(llm_seconds, 1),
                    "save_seconds": round(save_seconds, 1),
                },
                ensure_ascii=False,
            ),
        )
    )
    db.commit()

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="行程已生成（当前为示例数据，配置 LLM_API_KEY 后由 AI 生成真实行程）"
        if mock
        else "行程已生成",
    )


@router.post("/reoptimize", response_model=AIGenerateResponse)
def reoptimize_trip(
    payload: ReoptimizeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIGenerateResponse:
    trip = db.get(Trip, payload.trip_id)
    if trip is None or trip.user_id != user.id:
        raise HTTPException(status_code=404, detail="旅行不存在")
    if not trip.schedules:
        raise HTTPException(status_code=400, detail="行程为空，无法重新优化")

    try:
        result = ai_service.reoptimize_itinerary(db, trip, payload.instruction)
        ai_service.save_reoptimized(
            db, trip, result, city_hint=trip.destination
        )
    except LLMError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    trip.status = "edited"
    db.commit()

    mock = not settings.LLM_API_KEY
    return AIGenerateResponse(
        trip=TripOut.from_trip(trip),
        mock=mock,
        message="已重新优化（示例数据）" if mock else "已重新优化",
    )
