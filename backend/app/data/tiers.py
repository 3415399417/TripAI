"""Consumption tier expert rules.

Four tiers: 经济型 / 舒适型 / 高品质 / 奢华型.
Each tier defines hotel price ranges, per-day dining budget, transport
preferences, attraction types, signature experiences and budget ratios.
"""

from typing import TypedDict


class TierRule(TypedDict):
    label: str
    hotel_range: tuple[float, float]
    hotel_types: str
    dining_per_day: tuple[float, float]
    dining_types: str
    transport: str
    attractions: str
    experiences: str
    goals: str
    ratio: dict[str, float]


TIER_RULES: dict[str, TierRule] = {
    "经济型": {
        "label": "经济型",
        "hotel_range": (100, 400),
        "hotel_types": "青旅/连锁快捷酒店，非核心区域、近地铁即可",
        "dining_per_day": (100, 300),
        "dining_types": "小吃、地方特色、高性价比餐厅",
        "transport": "地铁、公交为主，少量打车",
        "attractions": "免费景点、城市探索、少量收费景点",
        "experiences": "城市漫步、免费观景台、博物馆",
        "goals": "性价比：用较少的钱覆盖更多景点和城市区域",
        "ratio": {
            "住宿": 0.32,
            "餐饮": 0.26,
            "交通": 0.16,
            "景点门票": 0.12,
            "娱乐体验": 0.06,
            "购物": 0.04,
            "备用资金": 0.04,
        },
    },
    "舒适型": {
        "label": "舒适型",
        "hotel_range": (500, 1500),
        "hotel_types": "三星以上酒店、精品酒店、中档民宿",
        "dining_per_day": (300, 800),
        "dining_types": "特色餐厅、高评分餐厅、当地美食",
        "transport": "地铁 + 网约车结合",
        "attractions": "城市地标、热门景区、特色体验",
        "experiences": "演出、游船、特色体验项目",
        "goals": "便利与舒适：行程省心、时间效率高",
        "ratio": {
            "住宿": 0.35,
            "餐饮": 0.24,
            "交通": 0.15,
            "景点门票": 0.10,
            "娱乐体验": 0.07,
            "购物": 0.05,
            "备用资金": 0.04,
        },
    },
    "高品质": {
        "label": "高品质",
        "hotel_range": (1500, 4000),
        "hotel_types": "高星酒店、景观酒店、精品设计酒店",
        "dining_per_day": (1000, 3000),
        "dining_types": "米其林、高端特色餐厅、江景餐厅",
        "transport": "网约车、专车",
        "attractions": "高质量体验、私人导览、特殊活动",
        "experiences": "私人导览、VIP体验、高端展览",
        "goals": "服务与品质：独特体验、管家式安排",
        "ratio": {
            "住宿": 0.40,
            "餐饮": 0.22,
            "交通": 0.14,
            "景点门票": 0.08,
            "娱乐体验": 0.08,
            "购物": 0.05,
            "备用资金": 0.03,
        },
    },
    "奢华型": {
        "label": "奢华型",
        "hotel_range": (4000, 20000),
        "hotel_types": "五星奢华酒店、套房、地标酒店",
        "dining_per_day": (3000, 10000),
        "dining_types": "米其林、私人餐厅、高端宴请",
        "transport": "专车、包车、高端车型",
        "attractions": "VIP体验、高端展览、私人导览",
        "experiences": "私人摄影、VIP活动、游艇/直升机等",
        "goals": "时间与身份体验：专属服务、顶级礼遇",
        "ratio": {
            "住宿": 0.45,
            "餐饮": 0.20,
            "交通": 0.12,
            "景点门票": 0.06,
            "娱乐体验": 0.10,
            "购物": 0.05,
            "备用资金": 0.02,
        },
    },
}

TIER_ORDER = ["经济型", "舒适型", "高品质", "奢华型"]


def classify(per_day_effective: float) -> str:
    """Map effective per-person daily budget to a consumption tier."""
    if per_day_effective <= 400:
        return "经济型"
    if per_day_effective <= 1000:
        return "舒适型"
    if per_day_effective <= 2500:
        return "高品质"
    return "奢华型"


def hotel_min_for(level: str) -> float:
    return TIER_RULES[level]["hotel_range"][0]


def dining_per_day_for(level: str) -> float:
    return TIER_RULES[level]["dining_per_day"][0]
