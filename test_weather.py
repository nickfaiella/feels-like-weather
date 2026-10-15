# Tests for weather.py and app.py. Run with:  pytest
# These use fake API responses, so they work without internet.

from unittest.mock import patch, MagicMock

from streamlit.testing.v1 import AppTest

import weather

FAKE_CITY = {"results": [{
    "name": "Boston", "admin1": "Massachusetts", "country": "United States",
    "latitude": 42.36, "longitude": -71.06,
}]}

hours = [f"2026-10-{14 + h // 24}T{h % 24:02d}:00" for h in range(48)]
FAKE_FORECAST = {
    "current": {
        "time": "2026-10-14T22:45", "temperature_2m": 47.2,
        "apparent_temperature": 43.1, "relative_humidity_2m": 71,
        "wind_speed_10m": 9.4, "weather_code": 2,
    },
    "hourly": {
        "time": hours,
        "temperature_2m": [40 + (h % 24) / 2 for h in range(48)],
        "precipitation_probability": [h % 100 for h in range(48)],
    },
    "daily": {
        "time": [f"2026-10-{14 + d}" for d in range(7)],
        "weather_code": [2, 61, 0, 3, 45, 80, 71],
        "temperature_2m_max": [55, 52, 60, 58, 50, 49, 38],
        "temperature_2m_min": [41, 44, 45, 43, 39, 37, 29],
        "precipitation_probability_max": [10, 80, 0, 5, None, 60, 70],
    },
}


def fake_get(url, params=None, timeout=None):
    response = MagicMock()
    response.raise_for_status = lambda: None
    if "geocoding" in url:
        if params["name"].lower() == "atlantis":
            response.json = lambda: {}
        else:
            response.json = lambda: FAKE_CITY
    else:
        response.json = lambda: FAKE_FORECAST
    return response


def test_feels_like_words():
    assert weather.feels_like_word(-5) == "arctic"
    assert weather.feels_like_word(43) == "chilly"
    assert weather.feels_like_word(72) == "warm"
    assert weather.feels_like_word(105) == "equatorial"


def test_celsius_conversion():
    assert weather.to_fahrenheit(0, "celsius") == 32
    assert weather.to_fahrenheit(50, "fahrenheit") == 50


def test_describe_unknown_code():
    assert weather.describe_code(1234)[1] == "Unknown conditions"


def test_next_24_hours_starts_now():
    times, temps, rain = weather.next_24_hours(FAKE_FORECAST)
    assert times[0] == "2026-10-14T22:00"
    assert len(times) == 24 and len(temps) == 24 and len(rain) == 24


@patch("weather.requests.get", side_effect=fake_get)
def test_find_city(mock_get):
    assert weather.find_city("Boston")["region"] == "Massachusetts"
    assert weather.find_city("Atlantis") is None


@patch("weather.requests.get", side_effect=fake_get)
def test_app_renders(mock_get):
    app = AppTest.from_file("app.py").run(timeout=30)
    assert not app.exception
    page_text = " ".join(m.value for m in app.markdown)
    assert "It is chilly." in page_text
    assert "Massachusetts" in page_text


@patch("weather.requests.get", side_effect=fake_get)
def test_app_unknown_city(mock_get):
    app = AppTest.from_file("app.py").run(timeout=30)
    app.text_input[0].set_value("Atlantis").run(timeout=30)
    assert not app.exception
    assert "No city called" in app.warning[0].value
