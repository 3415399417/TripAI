"""Rules entry: budget x city x time x people x interests -> travel plan."""

from __future__ import annotations

from typing import Any

from app.data import (
    cities,
    city_tiers,
    interests as interest_rules,
    pace as pace_rules,
    season as season_rules,
    tiers,
    traveler_constraints,
)


def build_plan(req: Any) -> dict[str, Any]:
    """Build a structured consumption plan from a TripCreate-like object."""
    destination = req.destination
    days = max((req.end_date - req.start_date).days + 1, 1)
    travelers = max(req.travelers, 1)
    budget = max(float(req.budget or 0), 0)
    user_interests = list(req.interests or [])
    travel_style = str(getattr(req, "travel_style", "") or "城市探索")
    traveler_group = str(getattr(req, "traveler_group", "") or "成人")

    factor = cities.city_factor(destination)
    city_label = cities.city_level(destination)
    per_day = budget / days / travelers if budget else 0.0
    effective = per_day / factor if per_day else 0.0
    level = tiers.classify(effective)

    tier_rule = tiers.TIER_RULES[level]
    ratio = interest_rules.adjust_ratio(tier_rule["ratio"], user_interests)
    style_weights = interest_rules.TRAVEL_STYLE_WEIGHTS.get(travel_style)
    if style_weights:
        ratio = interest_rules.adjust_ratio(ratio, [travel_style])

    suggested_min = round(budget * 0.85)
    suggested_max = round(budget * 0.93)
    allocation_base = round(budget * 0.9)
    breakdown = {
        key: round(allocation_base * value) for key, value in ratio.items()
    }

    interest = user_interests[0] if user_interests else ""
    tag = {
        "经济型": "城市探索",
        "舒适型": "品质休闲",
        "高品质": "深度体验",
        "奢华型": "尊享之旅",
    }[level]
    profile = f"{destination}{days}天{level}"
    if travel_style and travel_style != "城市探索":
        profile += f"·{travel_style}"
    if interest:
        profile += f"·{interest}偏好"
    profile += tag + "旅行者"

    daily_places = pace_rules.daily_places(days)
    constraints = traveler_constraints.traveler_constraints(traveler_group)
    season = season_rules.season_factors(req.start_date, req.end_date)
    place_preferences = interest_rules.place_preferences(
        user_interests, travel_style
    )
    return {
        "profile": profile,
        "level": level,
        "budget_range": {"min": suggested_min, "max": suggested_max},
        "budget_breakdown": breakdown,
        "city_level": city_label,
        "city_factor": factor,
        "daily_budget": round(per_day, 1),
        "effective_budget": round(effective, 1),
        "pace": pace_rules.pace_label(days),
        "daily_places": list(daily_places),
        "tier_rules": {
            "hotel_types": tier_rule["hotel_types"],
            "dining_types": tier_rule["dining_types"],
            "transport": tier_rule["transport"],
            "attractions": tier_rule["attractions"],
            "experiences": tier_rule["experiences"],
            "goals": tier_rule["goals"],
            "city_hotel_range": city_tiers.city_tier_rule(destination, level)[
                "hotel_range"
            ],
            "city_dining_range": city_tiers.city_tier_rule(destination, level)[
                "dining_per_day"
            ],
        },
        "place_preferences": place_preferences,
        "travel_style": travel_style,
        "traveler_group": traveler_group,
        "constraints": constraints,
        "season": season,
    }
