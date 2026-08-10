"""AMap weather service (free, forecasts for the next 4 days).

Forecasts beyond 4 days are unreliable, so weather is only consulted when
the trip starts within the forecast window.
"""

from __future__ import annotations

from datetime import date, timedelta

import httpx

from app.core.config import get_settings

settings = get_settings()


def get_weather(city: str, target: date) -> dict | None:
    """Return {weather, temperature} for the target date, or None."""
    if not settings.AMAP_WEB_KEY:
        return None
    today = date.today()
    if not (today <= target <= today + timedelta(days=4)):
        return None
    try:
        resp = httpx.get(
            "https://restapi.amap.com/v3/weather/weatherInfo",
            params={
                "key": settings.AMAP_WEB_KEY,
                "city": city,
                "extensions": "all",
            },
            timeout=8,
        )
        data = resp.json()
    except Exception:
        return None
    if data.get("status") != "1":
        return None
    try:
        casts = data["forecasts"][0]["casts"]
    except (KeyError, IndexError, TypeError):
        return None
    for cast in casts:
        if cast.get("date") == target.isoformat():
            return {
                "weather": cast.get("dayweather") or "",
                "temperature": cast.get("daytemp") or "",
            }
    return None
