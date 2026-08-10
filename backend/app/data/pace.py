"""Travel pace model.

Daily place density depends on trip length; first and last days are lighter
because of arrival / departure logistics.
"""


def daily_places(days: int) -> tuple[int, int]:
    """Return (min, max) places per day, excluding the hotel stop."""
    if days <= 2:
        return 3, 5
    if days <= 5:
        return 2, 4
    return 1, 3


def first_day_factor() -> float:
    """First day plans ~30% lighter (arrival, check-in)."""
    return 0.7


def last_day_factor() -> float:
    """Last day plans ~50% lighter (departure / return)."""
    return 0.5


def pace_label(days: int) -> str:
    if days <= 2:
        return "短途高密度"
    if days <= 5:
        return "均衡节奏"
    return "深度游"

