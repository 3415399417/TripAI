"""Traveler group constraints.

Real trips have physical limits: elderly travelers cannot walk 8000+ steps
and hop between far-flung districts; kids need afternoon rest. These rules
are injected into generation and used to filter unsuitable places.
"""

CONSTRAINTS: dict[str, dict] = {
    "成人": {
        "max_places": 6,
        "afternoon_rest": False,
        "avoid_switching": False,
        "notes": "节奏适中，保持合理休息",
    },
    "老人": {
        "max_places": 3,
        "afternoon_rest": True,
        "avoid_switching": True,
        "notes": (
            "老人同行：每天步行不超过8000步，连续参观景点不超过2个，"
            "减少换乘、就近安排，午后安排休息，避免爬坡和高强度项目"
        ),
    },
    "儿童": {
        "max_places": 3,
        "afternoon_rest": True,
        "avoid_switching": True,
        "notes": (
            "儿童同行：下午安排休息或轻松活动，避免长距离移动和暴晒，"
            "优先亲子友好地点（科技馆、动物园、主题乐园等）"
        ),
    },
    "情侣": {
        "max_places": 5,
        "afternoon_rest": False,
        "avoid_switching": False,
        "notes": "情侣出行：增加夜景、江景餐厅和浪漫体验，减少赶路",
    },
}

# 类别关键词黑名单：某些地点类型与人群不匹配
_BLOCKED_KEYWORDS: dict[str, tuple[str, ...]] = {
    "儿童": ("酒吧", "夜总会", "迪厅", "KTV", "夜店", "歌舞厅"),
    "家庭亲子": ("酒吧", "夜总会", "迪厅", "KTV", "夜店", "歌舞厅"),
    "老人": ("攀岩", "蹦极", "漂流", "跳伞", "极限运动", "高空项目"),
}


def traveler_constraints(group: str) -> dict:
    return CONSTRAINTS.get(group, CONSTRAINTS["成人"])


def place_matches(category: str | None, traveler_group: str) -> bool:
    """Reject places whose category conflicts with the traveler group."""
    if not category:
        return True
    blocked = _BLOCKED_KEYWORDS.get(traveler_group)
    if not blocked:
        return True
    return not any(keyword in category for keyword in blocked)
