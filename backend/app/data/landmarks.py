"""Signature places per city x preference.

Some places are must-see for a given preference in a city (Disney for a
family trip to Shanghai, Forbidden City for history lovers in Beijing).
These are injected into generation so the AI does not accidentally skip
them.
"""

LANDMARKS: dict[tuple[str, str], list[str]] = {
    ("上海", "亲子"): ["上海迪士尼度假区"],
    ("上海", "家庭亲子"): ["上海迪士尼度假区"],
    ("上海", "人文历史"): ["外滩", "豫园"],
    ("上海", "购物"): ["南京路步行街", "国金中心商场"],
    ("北京", "人文历史"): ["故宫博物院", "八达岭长城"],
    ("北京", "亲子"): ["北京环球度假区", "中国科学技术馆"],
    ("西安", "人文历史"): ["秦始皇兵马俑博物馆", "西安城墙"],
    ("成都", "美食"): ["宽窄巷子", "锦里"],
    ("成都", "亲子"): ["成都大熊猫繁育研究基地"],
    ("成都", "自然"): ["都江堰", "青城山"],
    ("杭州", "自然"): ["西湖", "灵隐寺"],
    ("杭州", "人文历史"): ["西湖", "河坊街"],
    ("广州", "亲子"): ["长隆野生动物世界"],
    ("深圳", "亲子"): ["欢乐谷", "世界之窗"],
    ("三亚", "度假"): ["亚龙湾", "蜈支洲岛"],
    ("三亚", "亲子"): ["亚特兰蒂斯水世界"],
    ("大理", "自然"): ["洱海", "苍山"],
    ("丽江", "自然"): ["玉龙雪山", "丽江古城"],
    ("桂林", "自然"): ["漓江", "象鼻山"],
    ("张家界", "自然"): ["天门山国家森林公园", "武陵源"],
    ("青岛", "自然"): ["栈桥", "崂山"],
    ("厦门", "自然"): ["鼓浪屿", "环岛路"],
    ("重庆", "夜生活"): ["洪崖洞", "解放碑"],
    ("长沙", "美食"): ["太平街", "橘子洲"],
    ("武汉", "人文历史"): ["黄鹤楼", "湖北省博物馆"],
    ("南京", "人文历史"): ["中山陵", "夫子庙"],
    ("苏州", "人文历史"): ["拙政园", "平江路"],
    ("昆明", "自然"): ["滇池", "石林"],
    ("哈尔滨", "自然"): ["冰雪大世界", "中央大街"],
}


def signature_places(destination: str, interests: list[str], travel_style: str) -> list[str]:
    """Return must-see places matching destination + preferences."""
    keys = [(destination, travel_style)] + [
        (destination, interest) for interest in interests
    ]
    result: list[str] = []
    for key in keys:
        for place in LANDMARKS.get(key, []):
            if place not in result:
                result.append(place)
    return result
