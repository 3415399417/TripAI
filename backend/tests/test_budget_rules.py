"""Expert knowledge base: budget x city x time -> consumption plan."""

from datetime import date, timedelta

import pytest

from app.schemas.trip import TripCreate
from app.services.ai_service.budget import compute_budget_plan


def _req(
    destination="上海",
    days=3,
    budget=3000,
    travelers=2,
    interests=None,
    travel_style="城市探索",
    traveler_group="成人",
    pace="适中",
):
    start = date.today() + timedelta(days=10)
    return TripCreate(
        destination=destination,
        start_date=start,
        end_date=start + timedelta(days=days - 1),
        travelers=travelers,
        budget=budget,
        pace=pace,
        interests=interests or [],
        travel_style=travel_style,
        traveler_group=traveler_group,
    )


def test_shanghai_3000_is_comfortable():
    plan = compute_budget_plan(_req("上海", 3, 3000, 2))
    assert plan["city_level"] == "一线城市"
    assert plan["city_factor"] == 1.0
    assert plan["level"] == "舒适型"
    # 建议区间是预算的 85%~93%（预算代表消费能力，不必花完）
    assert 0 < plan["budget_range"]["min"] <= plan["budget_range"]["max"] < 3000


def test_shanghai_30000_is_luxury():
    plan = compute_budget_plan(_req("上海", 3, 30000, 1))
    assert plan["level"] in ("高品质", "奢华型")


def test_city_factor_changes_tier():
    # 人均日预算约 333 元：上海经济型，淄博因城市系数 0.55 升档为舒适型
    shanghai = compute_budget_plan(_req("上海", 3, 1000, 1))
    zibo = compute_budget_plan(_req("淄博", 3, 1000, 1))
    assert shanghai["level"] == "经济型"
    assert zibo["level"] == "舒适型"


def test_breakdown_sums_to_90_percent():
    plan = compute_budget_plan(_req("成都", 4, 8000, 2, interests=["美食"]))
    allocation_base = round(8000 * 0.9)
    assert sum(plan["budget_breakdown"].values()) == pytest.approx(
        allocation_base, abs=10
    )
    assert plan["budget_breakdown"]["备用资金"] >= 0


def test_profile_contains_destination_and_tier():
    plan = compute_budget_plan(_req("杭州", 2, 1500, 1, interests=["摄影"]))
    assert "杭州" in plan["profile"]
    assert plan["level"] in plan["profile"]
