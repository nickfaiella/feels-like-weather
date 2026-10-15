# description: A live weather web app. Type any city to see current conditions,
#              a plain-English "feels like" headline, and hourly and 7-day forecasts.
# author: Nick Faiella (built with help from Claude)
# date: October 14, 2026
#
# Run locally with:  streamlit run app.py

from datetime import datetime

import altair as alt
import pandas as pd
import requests
import streamlit as st

import weather

st.set_page_config(page_title="Feels Like", page_icon="🌤️", layout="centered")

# ---------- styling ----------
# Archivo has a "width" axis; the headline uses the extra-wide version so it reads
# like a weather bulletin. Colors live in .streamlit/config.toml.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..800&display=swap');
    html, body, [class*="css"], .stMarkdown, .stTextInput, .stRadio {
        font-family: 'Archivo', system-ui, sans-serif;
    }
    .headline {
        font-family: 'Archivo', system-ui, sans-serif;
        font-stretch: 125%;
        font-weight: 800;
        font-size: clamp(2.6rem, 9vw, 5.2rem);
        line-height: 0.95;
        letter-spacing: -0.02em;
        margin: 0.4rem 0 0.8rem 0;
    }
    .summary { font-size: 1.15rem; max-width: 34em; line-height: 1.5; }
    .week { width: 100%; border-collapse: collapse; font-size: 1rem; border: none; }
    .week td { padding: 0.55rem 0.4rem; border: none; border-bottom: 1px solid #C9D4DB; }
    .week td.num { text-align: right; font-variant-numeric: tabular-nums; }
    .week tr:last-child td { border-bottom: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- cached data fetching ----------
# Caching means we don't call the API again for 10 minutes for the same city.

@st.cache_data(ttl=600)
def cached_city(name):
    return weather.find_city(name)


@st.cache_data(ttl=600)
def cached_forecast(latitude, longitude, unit):
    return weather.get_forecast(latitude, longitude, unit)


# ---------- inputs ----------
left, right = st.columns([3, 2])
with left:
    city_name = st.text_input("City", value="Boston")
with right:
    unit_label = st.radio("Units", ["°F", "°C"], horizontal=True)

unit = "fahrenheit" if unit_label == "°F" else "celsius"
speed = "mph" if unit == "fahrenheit" else "km/h"

if city_name.strip() == "":
    st.info("Type a city name to see its weather.")
    st.stop()

# ---------- fetch data, with clear error messages ----------
try:
    city = cached_city(city_name.strip())
except requests.RequestException:
    st.error("Couldn't reach the weather service. Check your internet connection and try again.")
    st.stop()

if city is None:
    st.warning(f'No city called "{city_name}" was found. Check the spelling or try a nearby larger city.')
    st.stop()

try:
    forecast = cached_forecast(city["latitude"], city["longitude"], unit)
except requests.RequestException:
    st.error("Found the city, but the forecast didn't load. Try again in a minute.")
    st.stop()

# ---------- headline ----------
now = forecast["current"]
emoji, description = weather.describe_code(now["weather_code"])
feels_f = weather.to_fahrenheit(now["apparent_temperature"], unit)
word = weather.feels_like_word(feels_f)

place = city["name"]
if city["region"]:
    place += f", {city['region']}"

st.markdown(f'<div class="headline">It is {word}.</div>', unsafe_allow_html=True)
st.markdown(
    f'<p class="summary">{emoji} {description} in {place}. '
    f'It\'s {now["temperature_2m"]:.0f}{unit_label} and feels like '
    f'{now["apparent_temperature"]:.0f}{unit_label}.</p>',
    unsafe_allow_html=True,
)

# ---------- today at a glance ----------
daily = forecast["daily"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("High", f"{daily['temperature_2m_max'][0]:.0f}{unit_label}")
col2.metric("Low", f"{daily['temperature_2m_min'][0]:.0f}{unit_label}")
col3.metric("Humidity", f"{now['relative_humidity_2m']}%")
col4.metric("Wind", f"{now['wind_speed_10m']:.0f} {speed}")

# ---------- next 24 hours ----------
st.subheader("Next 24 hours")
times, temps, rain = weather.next_24_hours(forecast)
hourly_df = pd.DataFrame({"Time": pd.to_datetime(times), "Temp": temps, "Rain": rain})

# Altair lets the temperature axis zoom in on the real range instead of starting at 0
temp_chart = alt.Chart(hourly_df).mark_line(color="#B86A00", strokeWidth=3).encode(
    x=alt.X("Time:T", title=None, axis=alt.Axis(format="%-I %p")),
    y=alt.Y("Temp:Q", title=unit_label, scale=alt.Scale(zero=False)),
    tooltip=[alt.Tooltip("Time:T", format="%a %-I %p"), alt.Tooltip("Temp:Q", format=".0f")],
).properties(height=220)

rain_chart = alt.Chart(hourly_df).mark_bar(color="#5B87A8").encode(
    x=alt.X("Time:T", title=None, axis=alt.Axis(format="%-I %p")),
    y=alt.Y("Rain:Q", title="Rain %", scale=alt.Scale(domain=[0, 100])),
    tooltip=[alt.Tooltip("Time:T", format="%a %-I %p"), alt.Tooltip("Rain:Q", title="Rain %")],
).properties(height=130)

st.altair_chart(temp_chart, use_container_width=True)
st.altair_chart(rain_chart, use_container_width=True)

# ---------- 7-day forecast ----------
st.subheader("This week")
rows = ""
for i in range(len(daily["time"])):
    day_name = datetime.fromisoformat(daily["time"][i]).strftime("%A")
    if i == 0:
        day_name = "Today"
    day_emoji, day_text = weather.describe_code(daily["weather_code"][i])
    high = daily["temperature_2m_max"][i]
    low = daily["temperature_2m_min"][i]
    rain_max = daily["precipitation_probability_max"][i]
    if rain_max is None:  # the API occasionally leaves this blank
        rain_max = 0
    rows += (
        f"<tr><td>{day_name}</td><td>{day_emoji} {day_text}</td>"
        f"<td class='num'>{high:.0f}° / {low:.0f}°</td>"
        f"<td class='num'>{rain_max}% rain</td></tr>"
    )
st.markdown(f"<table class='week'>{rows}</table>", unsafe_allow_html=True)

st.caption("Weather data from Open-Meteo.com. Updates every 10 minutes.")
