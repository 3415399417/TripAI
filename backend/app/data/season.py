"""Seasonal price fluctuation model.

Tourism prices vary a lot: five-star hotels can be 1800 on weekdays and
5000 during Spring Festival. These factors are injected into generation so
the AI prices places realistically for the travel dates.
"""

from __future__ import annotations

from datetime import date

# (label, start_month, start_day, end_month, end_day, hotel, dining, attraction)
_SEASONS = [
    ("春节", 1, 25, 2, 20, 1.5, 1.2, 1.2),
    ("国庆假期", 10, 1, 10, 7, 1.4, 1.15, 1.1),
    ("五一假期", 5, 1, 5, 5, 1.3, 1.1, 1.05),
    ("暑假", 7, 1, 8, 31, 1.2, 1.05, 1.1),
    ("元旦假期", 1, 1, 1, 3, 1.25, 1.1, 1.05),
]


def _in_range(day: date, sm: int, sd: int, em: int, ed: int) -> bool:
    start = date(day.year, sm, sd)
    end = date(day.year, em, ed)
    return start <= day <= end


def season_factors(start: date, end: date) -> dict:
    """Return dominant season multipliers for the travel date range."""
    days = [start]
    current = start
    while current < end:
        current = date.fromordinal(current.toordinal() + 1)
        days.append(current)

    # Count days that fall into each seasonal window.
    hit: dict[str, int] = {}
    for day in days:
        for label, sm, sd, em, ed, *_ in _SEASONS:
            if _in_range(day, sm, sd, em, ed):
                hit[label] = hit.get(label, 0) + 1
                break
        else:
            if day.weekday() >= 5:  # weekend
                hit["周末"] = hit.get("周末", 0) + 1

    if not hit:
        return {
            "label": "平日",
            "hotel_factor": 1.0,
            "dining_factor": 1.0,
            "attraction_factor": 1.0,
        }

    dominant = max(hit, key=hit.get)
    for label, _sm, _sd, _em, _ed, hotel, dining, attraction in _SEASONS:
        if label == dominant:
            return {
                "label": label,
                "hotel_factor": hotel,
                "dining_factor": dining,
                "attraction_factor": attraction,
            }
    return {
        "label": "周末",
        "hotel_factor": 1.1,
        "dining_factor": 1.0,
        "attraction_factor": 1.0,
    }

