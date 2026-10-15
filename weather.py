# description: Functions that fetch live weather from the free Open-Meteo API
#              and turn the raw data into words people understand
# author: Nick Faiella (built with help from Claude)
# date: October 14, 2026

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather codes used by Open-Meteo, mapped to an emoji and a description
WEATHER_CODES = {
    0: ("☀️", "Clear sky"),
    1: ("🌤️", "Mainly clear"),
    2: ("⛅", "Partly cloudy"),
    3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"),
    48: ("🌫️", "Freezing fog"),
    51: ("🌦️", "Light drizzle"),
    53: ("🌦️", "Drizzle"),
    55: ("🌧️", "Heavy drizzle"),
    56: ("🌧️", "Freezing drizzle"),
    57: ("🌧️", "Heavy freezing drizzle"),
    61: ("🌦️", "Light rain"),
    63: ("🌧️", "Rain"),
    65: ("🌧️", "Heavy rain"),
    66: ("🌧️", "Freezing rain"),
    67: ("🌧️", "Heavy freezing rain"),
    71: ("🌨️", "Light snow"),
    73: ("🌨️", "Snow"),
    75: ("❄️", "Heavy snow"),
    77: ("🌨️", "Snow grains"),
    80: ("🌦️", "Rain showers"),
    81: ("🌧️", "Heavy rain showers"),
    82: ("⛈️", "Violent rain showers"),
    85: ("🌨️", "Snow showers"),
    86: ("❄️", "Heavy snow showers"),
    95: ("⛈️", "Thunderstorm"),
    96: ("⛈️", "Thunderstorm with hail"),
    99: ("⛈️", "Thunderstorm with heavy hail"),
}


def describe_code(code):
    """Return (emoji, description) for a WMO weather code."""
    return WEATHER_CODES.get(code, ("🌡️", "Unknown conditions"))


def to_fahrenheit(temp, unit):
    """Convert a temperature to Fahrenheit if it's in Celsius."""
    if unit == "celsius":
        return temp * 9 / 5 + 32
    return temp


def feels_like_word(temp_f):
    """Return a 'feels like' adjective for a Fahrenheit temperature.

    This is the logic from my CS1 TempFeelsLike exercise, turned into a function.
    """
    if temp_f < 0:
        return "arctic"
    elif temp_f < 10:
        return "frigid"
    elif temp_f < 20:
        return "raw"
    elif temp_f < 30:
        return "freezing"
    elif temp_f < 40:
        return "cold"
    elif temp_f < 50:
        return "chilly"
    elif temp_f < 60:
        return "cool"
    elif temp_f < 70:
        return "pleasant"
    elif temp_f < 80:
        return "warm"
    elif temp_f < 90:
        return "hot"
    elif temp_f < 100:
        return "steamy"
    else:
        return "equatorial"


def find_city(name):
    """Look up a city by name. Returns a dictionary, or None if not found."""
    response = requests.get(
        GEOCODE_URL,
        params={"name": name, "count": 1, "language": "en", "format": "json"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    # When nothing matches, Open-Meteo leaves out the "results" key entirely
    if "results" not in data or len(data["results"]) == 0:
        return None

    place = data["results"][0]
    return {
        "name": place["name"],
        "region": place.get("admin1", ""),
        "country": place.get("country", ""),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
    }


def get_forecast(latitude, longitude, unit="fahrenheit"):
    """Fetch current conditions plus hourly and 7-day forecasts."""
    wind_unit = "mph" if unit == "fahrenheit" else "kmh"
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                       "wind_speed_10m,weather_code",
            "hourly": "temperature_2m,precipitation_probability",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                     "precipitation_probability_max",
            "temperature_unit": unit,
            "wind_speed_unit": wind_unit,
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def next_24_hours(forecast):
    """Return lists of (times, temps, rain chances) for the next 24 hours.

    Times are full timestamps like "2026-10-14T22:00", so a chart keeps them
    in the right order even after midnight.
    """
    hourly = forecast["hourly"]
    current_hour = forecast["current"]["time"][:13]  # e.g. "2026-10-14T22"

    # Find where "now" is in the hourly list, then take the next 24 hours
    start = 0
    for index, time in enumerate(hourly["time"]):
        if time[:13] == current_hour:
            start = index
            break

    end = start + 24
    times = hourly["time"][start:end]
    temps = hourly["temperature_2m"][start:end]
    rain = hourly["precipitation_probability"][start:end]
    return times, temps, rain
