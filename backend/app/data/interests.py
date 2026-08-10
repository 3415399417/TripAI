"""Interest preference weights.

Each interest shifts the budget distribution by percentage points.
Positive = raise that category, negative = lower it. Applied on top of the
tier ratio and then clamped to sane bounds.
"""

INTEREST_WEIGHTS: dict[str, dict[str, float]] = {
    "美食": {"餐饮": 8, "购物": -4, "住宿": -2, "娱乐体验": -2},
    "摄影": {"景点门票": 3, "交通": 2, "购物": -5, "娱乐体验": -3},
    "购物": {"购物": 10, "餐饮": -4, "住宿": -3, "娱乐体验": -3},
    "自然风光": {"景点门票": 5, "交通": 2, "购物": -4, "娱乐体验": -3},
    "户外": {"娱乐体验": 5, "交通": 3, "购物": -5, "住宿": -3},
    "人文历史": {"景点门票": 4, "餐饮": 2, "娱乐体验": -2, "购物": -4},
    "亲子": {"景点门票": 5, "娱乐体验": 3, "交通": 2, "购物": -5, "住宿": -3, "餐饮": -2},
    "夜生活": {"娱乐体验": 6, "餐饮": 2, "购物": -4, "景点门票": -4},
    "休闲度假": {"住宿": 4, "娱乐体验": 2, "交通": -3, "景点门票": -3},
    "艺术": {"景点门票": 4, "娱乐体验": 2, "购物": -3},
    "展览": {"景点门票": 4, "娱乐体验": 2, "购物": -3},
    "深度游": {"景点门票": 3, "住宿": 2, "交通": -2, "购物": -3},
}

# 各类目允许的最终占比区间（防止权重把分配推到离谱范围）
CATEGORY_BOUNDS: dict[str, tuple[float, float]] = {
    "住宿": (0.20, 0.55),
    "餐饮": (0.15, 0.40),
    "交通": (0.08, 0.25),
    "景点门票": (0.04, 0.20),
    "娱乐体验": (0.04, 0.20),
    "购物": (0.02, 0.18),
    "备用资金": (0.02, 0.08),
}

# 旅行类型 → 预算权重（与兴趣权重叠加）
TRAVEL_STYLE_WEIGHTS: dict[str, dict[str, float]] = {
    "蜜月": {"住宿": 6, "餐饮": 4, "娱乐体验": 4, "购物": 2, "交通": -4, "景点门票": -4},
    "家庭亲子": {"景点门票": 5, "娱乐体验": 3, "交通": 2, "住宿": -3, "餐饮": -2, "购物": -5},
    "商务出差": {"住宿": 5, "交通": 2, "餐饮": 2, "购物": -2, "娱乐体验": -4, "景点门票": -4},
    "城市探索": {"景点门票": 3, "交通": 2, "餐饮": 2, "购物": -4, "娱乐体验": -2},
    "独自旅行": {"交通": 2, "景点门票": 2, "餐饮": 2, "住宿": -3, "娱乐体验": -2, "购物": -3},
    "毕业旅行": {"娱乐体验": 6, "餐饮": 4, "住宿": -4, "购物": 2, "景点门票": -2},
    "闺蜜出行": {"购物": 5, "餐饮": 4, "娱乐体验": 3, "住宿": -3, "交通": -2},
    "情侣约会": {"餐饮": 5, "娱乐体验": 4, "住宿": 2, "购物": 2, "交通": -3},
    "深度研学": {"景点门票": 6, "住宿": 2, "交通": 2, "购物": -5, "娱乐体验": -4},
    "康养休闲": {"住宿": 4, "娱乐体验": 3, "餐饮": 2, "交通": -3, "景点门票": -3, "购物": -2},
}

# 兴趣 → 推荐地点类型（影响路线构成）
INTEREST_PLACE_PREFERENCES: dict[str, str] = {
    "美食": "老字号、小吃街、本地特色餐厅、高评分餐馆",
    "摄影": "观景台、地标建筑、城市天际线、免费摄影机位、建筑街区",
    "购物": "核心商圈、购物中心、品牌旗舰店、特色集市",
    "自然风光": "公园、湖泊、山景、海滨、户外徒步路线",
    "户外": "徒步路线、山地、骑行道、户外营地",
    "人文历史": "博物馆、历史街区、古迹遗址、名人故居",
    "亲子": "动物园、科技馆、主题乐园、亲子友好景区",
    "夜生活": "酒吧街、演出场馆、夜市、滨江夜景",
    "休闲度假": "咖啡馆、温泉、海滨步道、度假村",
    "艺术": "美术馆、艺术馆、创意园区、展览",
    "展览": "美术馆、科技馆、特展场馆",
    "深度游": "小众街区、在地文化体验、手工作坊",
    "蜜月": "浪漫江景餐厅、高空观景、情侣纪念体验",
    "家庭亲子": "主题乐园、亲子餐厅、科技馆、动物园",
    "商务出差": "商务区、高端酒店周边、效率优先路线",
    "独自旅行": "青年旅舍街区、当地市集、轻松社交场所",
    "毕业旅行": "主题乐园、夜市、音乐演出、网红打卡点",
    "闺蜜出行": "咖啡馆、拍照打卡点、商圈、下午茶",
    "情侣约会": "江景餐厅、观景台、浪漫街区、演出",
    "深度研学": "博物馆、文化遗址、研学基地、老城街区",
    "康养休闲": "温泉、SPA、生态公园、海滨步道",
}


def place_preferences(interests: list[str], travel_style: str = "") -> list[str]:
    """Collect place-type preferences from interests + travel style."""
    preferences = []
    for key in interests:
        value = INTEREST_PLACE_PREFERENCES.get(key)
        if value:
            preferences.append(f"{key}：{value}")
    style_value = INTEREST_PLACE_PREFERENCES.get(travel_style)
    if style_value:
        preferences.append(f"旅行类型{travel_style}：{style_value}")
    return preferences


def adjust_ratio(base: dict[str, float], interests: list[str]) -> dict[str, float]:
    """Return a budget ratio adjusted by the user's interest preferences."""
    ratio = dict(base)
    for interest in interests:
        weights = INTEREST_WEIGHTS.get(interest) or TRAVEL_STYLE_WEIGHTS.get(
            interest
        )
        if not weights:
            continue
        for category, delta in weights.items():
            ratio[category] = ratio.get(category, 0) + delta / 100.0
    # Clamp each category to sane bounds, then renormalize to sum = 1.0.
    for category in ratio:
        low, high = CATEGORY_BOUNDS.get(category, (0.0, 1.0))
        ratio[category] = max(low, min(high, ratio[category]))
    total = sum(ratio.values())
    if total <= 0:
        return dict(base)
    return {k: v / total for k, v in ratio.items()}
