# SkyPulse - Live Weather Web Application

A sleek, responsive, and real-time Weather Web Application built in **Python (Flask)** powered by the **Open-Meteo Live API** (free, no API key required).

---

## Features

- ⚡ **Live Weather & Geocoding**: Real-time atmospheric data from Open-Meteo with zero configuration or API keys required.
- 📍 **Instant City Search & Autocomplete**: Search any city, state, or region worldwide with live suggestions.
- 🎯 **One-Click Geolocation**: "My Location" button retrieves your exact local coordinates and weather.
- 🌡️ **Comprehensive Atmospheric Metrics**:
  - Current temperature & "Feels Like"
  - Humidity with visual progress indicator
  - Wind speed, direction, and compass orientation (N, NE, SW, etc.)
  - UV Index rating (Low, Moderate, High, Very High)
  - Atmospheric pressure (hPa)
  - Cloud cover (%)
  - Sunrise and sunset times
- 📊 **24-Hour Hourly Outlook & Trend Chart**: Interactive Chart.js graph plotting temperature curves and rain probability bars side-by-side.
- 📅 **7-Day Extended Forecast**: Daily forecast cards with precipitation probability and relative temperature range bars.
- 🔄 **Unit Toggle**: Instant switching between Celsius (°C / km/h) and Fahrenheit (°F / mph).
- 🎨 **Dynamic Weather Themes**: The background interface dynamically shifts its theme based on the current weather (Clear Day, Starry Night, Rain, Thunderstorm, Snow, Overcast).

---

## Project Structure

```
weather-app/
├── app.py                     # Flask application entry point and REST API routes
├── requirements.txt           # Python dependencies (Flask, requests)
├── run.sh                     # Quick launch shell script
├── services/
│   ├── __init__.py
│   └── weather_service.py     # Live API client, WMO code parser, caching & fallback
├── static/
│   ├── css/
│   │   └── style.css          # Weather themes, scrollbars & glassmorphism
│   └── js/
│       └── app.js             # Frontend interactivity, Chart.js, geolocation & units
├── templates/
│   └── index.html             # Responsive dashboard layout (Tailwind CSS)
└── tests/
    ├── __init__.py
    └── test_weather.py        # Automated test suite
```

---

## Quickstart

### 1. Run the App
From the `weather-app` directory:
```bash
./run.sh
```
Or manually using the virtual environment:
```bash
source venv/bin/activate
python app.py
```

### 2. Open in Browser
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

---

## Running Tests
Run the automated test suite:
```bash
./venv/bin/python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## API Endpoints

- `GET /`: Main dashboard interface.
- `GET /api/search?q={cityName}`: Autocomplete search returning matching places and coordinates.
- `GET /api/weather?lat={latitude}&lon={longitude}&units={metric|imperial}`: Live forecast data by coordinates.
- `GET /api/weather?city={cityName}&units={metric|imperial}`: Live forecast data by city name.
- `GET /api/health`: Health status endpoint.
