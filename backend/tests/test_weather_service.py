"""Weather service: forecast window + day mapping + live weather."""

from datetime import date, timedelta

import app.services.weather_service as ws


def _forecast_payload(start: date, days: int) -> dict:
    casts = []
    for i in range(days):
        d = start + timedelta(days=i)
        casts.append(
            {
                "date": d.isoformat(),
                "dayweather": "晴" if i % 2 == 0 else "多云",
                "daytemp": str(30 - i),
                "nighttemp": str(24 - i),
            }
        )
    return {"status": "1", "forecasts": [{"casts": casts}]}


def test_forecast_maps_trip_days(monkeypatch):
    today = date.today()
    monkeypatch.setattr(
        ws, "_fetch_amap", lambda city: _forecast_payload(today, 4)
    )
    monkeypatch.setattr(
        ws,
        "_fetch_live",
        lambda city: {"weather": "晴", "temperature": "28"},
    )

    info = ws.get_weather_forecast("上海", today, today + timedelta(days=2))
    assert info["within_window"] is True
    assert len(info["days"]) == 3
    assert info["days"][0]["weather"] == "晴"
    assert info["days"][1]["day"] == 2
    assert info["live"]["temperature"] == "28"


def test_out_of_window_no_forecast(monkeypatch):
    far = date.today() + timedelta(days=30)
    monkeypatch.setattr(ws, "_fetch_amap", lambda city: None)
    monkeypatch.setattr(ws, "_fetch_live", lambda city: None)
    info = ws.get_weather_forecast("杭州", far, far + timedelta(days=2))
    assert info["within_window"] is False
    assert info["days"] == []


def test_get_weather_beyond_window_returns_none():
    assert (
        ws.get_weather("上海", date.today() + timedelta(days=10)) is None
    )
