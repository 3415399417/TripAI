"""User preference memory: learn from generations/edits and build summaries."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.preference import UserPreference
from app.schemas.preference import UserPreferenceOut


def _load(value: str | None) -> dict[str, int]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def _dump(data: dict[str, int]) -> str:
    return json.dumps(data, ensure_ascii=False)


def _top(data: dict[str, int], limit: int = 3) -> list[str]:
    return [k for k, _ in sorted(data.items(), key=lambda x: -x[1])[:limit]]


def _most_common(data: dict[str, int]) -> str | None:
    return _top(data, 1)[0] if data else None


def _get_or_create(db: Session, user_id: int) -> UserPreference:
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )
    if pref is None:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
        db.flush()
    return pref


def record_generation(
    db: Session,
    user_id: int,
    payload,
    result,
) -> None:
    """Aggregate one successful generation into the user's preference profile."""
    pref = _get_or_create(db, user_id)
    pref.generation_count += 1

    interests = _load(pref.interests)
    for tag in (payload.interests or []):
        interests[tag] = interests.get(tag, 0) + 1
    pref.interests = _dump(interests)

    styles = _load(pref.travel_styles)
    style = getattr(payload, "travel_style", None) or "城市探索"
    styles[style] = styles.get(style, 0) + 1
    pref.travel_styles = _dump(styles)

    groups = _load(pref.traveler_groups)
    group = getattr(payload, "traveler_group", None) or "成人"
    groups[group] = groups.get(group, 0) + 1
    pref.traveler_groups = _dump(groups)

    paces = _load(pref.paces)
    pace = getattr(payload, "pace", None) or "适中"
    paces[pace] = paces.get(pace, 0) + 1
    pref.paces = _dump(paces)

    from app.services.ai_service.budget import compute_budget_plan

    tiers = _load(pref.budget_tiers)
    tier = compute_budget_plan(payload)["level"]
    tiers[tier] = tiers.get(tier, 0) + 1
    pref.budget_tiers = _dump(tiers)

    favorites = _load(pref.favorite_places)
    for day in result.days:
        for item in day.items:
            name = (item.name or "").strip()
            if name:
                favorites[name] = favorites.get(name, 0) + 1
    pref.favorite_places = _dump(favorites)


def record_removals(db: Session, user_id: int, names: list[str]) -> None:
    """Learn from places the user deleted while editing."""
    names = [n for n in names if n and n.strip()]
    if not names:
        return
    pref = _get_or_create(db, user_id)
    avoids = _load(pref.avoid_places)
    for name in names:
        avoids[name] = avoids.get(name, 0) + 1
    pref.avoid_places = _dump(avoids)


def build_summary(db: Session, user_id: int) -> str | None:
    """Compact one-sentence summary injected into the LLM prompt."""
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )
    if pref is None or pref.generation_count <= 0:
        return None
    return _to_out(pref).summary


def _to_out(pref: UserPreference) -> UserPreferenceOut:
    interests = _load(pref.interests)
    styles = _load(pref.travel_styles)
    groups = _load(pref.traveler_groups)
    paces = _load(pref.paces)
    tiers = _load(pref.budget_tiers)
    favorites = _load(pref.favorite_places)
    avoids = _load(pref.avoid_places)

    parts: list[str] = []
    tier = _most_common(tiers)
    if tier:
        parts.append(f"消费倾向{ tier }")
    top_interests = _top(interests, 3)
    if top_interests:
        parts.append("兴趣偏好" + "、".join(top_interests))
    style = _most_common(styles)
    if style:
        parts.append(f"常用类型{ style }")
    group = _most_common(groups)
    if group:
        parts.append(f"常随行{ group }")
    pace = _most_common(paces)
    if pace:
        parts.append(f"节奏{ pace }")
    top_fav = _top(favorites, 3)
    if top_fav:
        parts.append("常去" + "、".join(top_fav))
    top_avoid = _top(avoids, 3)
    if top_avoid:
        parts.append("不喜欢/删过" + "、".join(top_avoid))

    count = pref.generation_count
    summary = (
        f"根据该用户 {count} 次生成记录：" + "；".join(parts)
        if parts
        else f"该用户已有 {count} 次生成记录"
    )
    return UserPreferenceOut(
        interests=_top(interests, 5),
        travel_styles=_top(styles, 3),
        traveler_groups=_top(groups, 2),
        paces=_top(paces, 2),
        budget_tier=tier,
        favorite_places=_top(favorites, 8),
        avoid_places=_top(avoids, 8),
        generation_count=count,
        summary=summary,
    )


def to_out(db: Session, user_id: int) -> UserPreferenceOut:
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )
    if pref is None:
        return UserPreferenceOut(
            interests=[],
            travel_styles=[],
            traveler_groups=[],
            paces=[],
            budget_tier=None,
            favorite_places=[],
            avoid_places=[],
            generation_count=0,
            summary="还没有偏好数据，生成行程后会慢慢学习你的习惯",
        )
    return _to_out(pref)


def update_lists(
    db: Session,
    user_id: int,
    favorite_places: list[str] | None,
    avoid_places: list[str] | None,
) -> UserPreferenceOut:
    pref = _get_or_create(db, user_id)
    if favorite_places is not None:
        pref.favorite_places = _dump({name: 1 for name in favorite_places if name})
    if avoid_places is not None:
        pref.avoid_places = _dump({name: 1 for name in avoid_places if name})
    return _to_out(pref)


def clear(db: Session, user_id: int) -> None:
    pref = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .first()
    )
    if pref is not None:
        db.delete(pref)
