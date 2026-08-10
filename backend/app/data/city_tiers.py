"""City x tier expert price table (first stage: 20 hot cities).

Price ranges are derived from the global tier baseline scaled by the city
cost factor, so the same tier has different realistic prices in different
cities (e.g. economy hotels in Dali cost less than in Shanghai).
"""

from app.data import cities, tiers

HOT_CITIES = [
    "上海",
    "北京",
    "深圳",
    "广州",
    "成都",
    "杭州",
    "重庆",
    "武汉",
    "苏州",
    "南京",
    "长沙",
    "青岛",
    "天津",
    "郑州",
    "西安",
    "昆明",
    "厦门",
    "大理",
    "丽江",
    "桂林",
]


def city_tier_rule(city: str, level: str) -> dict:
    """Return hotel/dining price ranges for a city + tier, plus behavior."""
    base = tiers.TIER_RULES[level]
    factor = cities.city_factor(city)
    hotel_lo, hotel_hi = base["hotel_range"]
    dining_lo, dining_hi = base["dining_per_day"]
    hotel_lo = max(60.0, round(hotel_lo * factor))
    hotel_hi = max(round(hotel_hi * factor), hotel_lo + 50)
    dining_lo = max(40.0, round(dining_lo * factor))
    dining_hi = max(round(dining_hi * factor), dining_lo + 50)
    return {
        "hotel_range": (hotel_lo, hotel_hi),
        "dining_per_day": (dining_lo, dining_hi),
        "hotel_types": base["hotel_types"],
        "dining_types": base["dining_types"],
        "transport": base["transport"],
        "attractions": base["attractions"],
        "experiences": base["experiences"],
    }

