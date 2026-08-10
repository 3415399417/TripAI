"""City consumption database (first stage: 20+ popular cities).

City factor = cost-of-living index. The same budget means different
spending power in different cities:
    人均每日预算 ÷ 城市系数 = 有效预算
"""

# 一线城市
TIER1 = ("上海", "北京", "深圳", "广州")
# 新一线城市
TIER2 = (
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
)
# 二线城市
TIER3 = (
    "西安",
    "昆明",
    "厦门",
    "大连",
    "无锡",
    "佛山",
    "福州",
    "济南",
    "哈尔滨",
    "合肥",
    "南昌",
    "贵阳",
    "南宁",
    "石家庄",
    "三亚",
)
# 三四线 / 小众旅游城市
TIER4 = (
    "大理",
    "丽江",
    "桂林",
    "淄博",
    "洛阳",
    "黄山",
    "张家界",
    "凤凰",
    "西双版纳",
    "北海",
    "敦煌",
    "喀纳斯",
)

CITY_FACTOR: dict[str, float] = {}
for _city in TIER1:
    CITY_FACTOR[_city] = 1.0
for _city in TIER2:
    CITY_FACTOR[_city] = 0.85
for _city in TIER3:
    CITY_FACTOR[_city] = 0.7
for _city in TIER4:
    CITY_FACTOR[_city] = 0.55

DEFAULT_FACTOR = 0.7


def city_factor(destination: str) -> float:
    """Return the cost factor for a destination (defaults to tier-2 level)."""
    return CITY_FACTOR.get(destination, DEFAULT_FACTOR)


def city_level(destination: str) -> str:
    """Return the city tier label for a destination."""
    if destination in TIER1:
        return "一线城市"
    if destination in TIER2:
        return "新一线城市"
    if destination in TIER3:
        return "二线城市"
    if destination in TIER4:
        return "三四线/旅游城市"
    return "二线城市"

