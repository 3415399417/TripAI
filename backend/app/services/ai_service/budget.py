"""Budget plan computation: tier classification, ratio tables, and city cost factor."""

from __future__ import annotations

from typing import Any

from app.data import cities as city_data
from app.schemas.trip import TripCreate

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
    """Delegate to the authoritative city database in app.data.cities."""
    return city_data.city_factor(destination)


def compute_budget_plan(req: TripCreate) -> dict[str, Any]:
    """Determine consumption level, suggested range and budget breakdown.

    Budget is interpreted as spending power, not a target to be fully spent.
    """
    from app.data.rules import build_plan

    return build_plan(req)
