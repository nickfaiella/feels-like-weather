# Feels Like

A live weather web app that answers the question people actually ask: what's it like out there? Type any city and the headline tells you in plain English, like **"It is chilly."**, followed by the details.

<!-- Add a screenshot here once it's running: take one, save it as screenshots/app.png, and uncomment the next line -->
<!-- ![Feels Like screenshot](screenshots/app.png) -->

**Live demo:** _add your Streamlit Community Cloud link here_

## Features

- Search any city in the world
- A "feels like" headline based on the apparent temperature, from "arctic" to "equatorial"
- Today's high, low, humidity, and wind
- Hourly temperature and rain-chance charts for the next 24 hours
- A 7-day forecast
- °F and °C, with wind in mph or km/h to match
- Clear messages when a city isn't found or the network is down

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

No API key needed. Weather data comes from the free [Open-Meteo](https://open-meteo.com) API.

## How it works

The project is split into two files:

- **`weather.py`** handles the data. It calls Open-Meteo's geocoding API to turn a city name into latitude and longitude, then calls the forecast API. Responses arrive as JSON, which `requests` turns into Python dictionaries.
- **`app.py`** handles the page. It's built with [Streamlit](https://streamlit.io), which turns a Python script into a web app, and [Altair](https://altair-viz.github.io) for the charts.

The headline word comes from an `if`/`elif` chain I first wrote as a CS1 exercise, turned into a reusable function. Results are cached for 10 minutes with `@st.cache_data`, so the app doesn't call the API again every time someone clicks something.

## Tests

```bash
pip install pytest
pytest
```

The tests use fake API responses, so they run without internet. They cover the feels-like words, unit conversion, finding "now" in the hourly forecast, and loading the full app.

<img width="896" height="767" alt="Screenshot 2026-10-20 at 3 00 32 PM" src="https://github.com/user-attachments/assets/8d621fe0-5d6f-48bf-acc6-04316bc7e259" />

Go to: https://nickfaiella-feels-like-weather-app-8pibt0.streamlit.app/

Built with help from Claude (Anthropic).
