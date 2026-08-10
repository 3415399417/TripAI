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


def adjust_ratio(base: dict[str, float], interests: list[str]) -> dict[str, float]:
    """Return a budget ratio adjusted by the user's interest preferences."""
    ratio = dict(base)
    for interest in interests:
        weights = INTEREST_WEIGHTS.get(interest)
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

