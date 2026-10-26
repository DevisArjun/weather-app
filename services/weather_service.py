import time
import requests
from typing import Dict, Any, List, Optional

WMO_CODE_MAP = {
    0: {"desc": "Clear sky", "icon": "sun", "theme": "clear"},
    1: {"desc": "Mainly clear", "icon": "cloud-sun", "theme": "partly-cloudy"},
    2: {"desc": "Partly cloudy", "icon": "cloud-sun", "theme": "partly-cloudy"},
    3: {"desc": "Overcast", "icon": "cloud", "theme": "cloudy"},
    45: {"desc": "Foggy", "icon": "cloud-fog", "theme": "fog"},
    48: {"desc": "Depositing rime fog", "icon": "cloud-fog", "theme": "fog"},
    51: {"desc": "Light drizzle", "icon": "cloud-drizzle", "theme": "rain"},
    53: {"desc": "Moderate drizzle", "icon": "cloud-drizzle", "theme": "rain"},
    55: {"desc": "Dense drizzle", "icon": "cloud-drizzle", "theme": "rain"},
    56: {"desc": "Light freezing drizzle", "icon": "cloud-snow", "theme": "snow"},
    57: {"desc": "Dense freezing drizzle", "icon": "cloud-snow", "theme": "snow"},
    61: {"desc": "Slight rain", "icon": "cloud-rain", "theme": "rain"},
    63: {"desc": "Moderate rain", "icon": "cloud-rain", "theme": "rain"},
    65: {"desc": "Heavy rain", "icon": "cloud-rain", "theme": "rain"},
    66: {"desc": "Light freezing rain", "icon": "cloud-snow", "theme": "snow"},
    67: {"desc": "Heavy freezing rain", "icon": "cloud-snow", "theme": "snow"},
    71: {"desc": "Slight snow fall", "icon": "snowflake", "theme": "snow"},
    73: {"desc": "Moderate snow fall", "icon": "snowflake", "theme": "snow"},
    75: {"desc": "Heavy snow fall", "icon": "snowflake", "theme": "snow"},
    77: {"desc": "Snow grains", "icon": "snowflake", "theme": "snow"},
    80: {"desc": "Slight rain showers", "icon": "cloud-drizzle", "theme": "rain"},
    81: {"desc": "Moderate rain showers", "icon": "cloud-rain", "theme": "rain"},
    82: {"desc": "Violent rain showers", "icon": "cloud-rain", "theme": "rain"},
    85: {"desc": "Slight snow showers", "icon": "snowflake", "theme": "snow"},
    86: {"desc": "Heavy snow showers", "icon": "snowflake", "theme": "snow"},
    95: {"desc": "Thunderstorm", "icon": "cloud-lightning", "theme": "thunderstorm"},
    96: {"desc": "Thunderstorm with slight hail", "icon": "cloud-lightning", "theme": "thunderstorm"},
    99: {"desc": "Thunderstorm with heavy hail", "icon": "cloud-lightning", "theme": "thunderstorm"},
}

def degrees_to_compass(deg: float) -> str:
    val = int((deg / 22.5) + .5)
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return directions[(val % 16)]

class WeatherService:
    def __init__(self, cache_ttl_seconds: int = 600):
        self.cache_ttl = cache_ttl_seconds
        self._weather_cache: Dict[str, Dict[str, Any]] = {}
        self._search_cache: Dict[str, Dict[str, Any]] = {}

    def get_weather_info(self, code: int, is_day: int = 1) -> Dict[str, str]:
        info = WMO_CODE_MAP.get(code, {"desc": "Unknown", "icon": "cloud", "theme": "cloudy"})
        desc = info["desc"]
        icon = info["icon"]
        theme = info["theme"]

        if is_day == 0:
            if icon == "sun":
                icon = "moon"
            elif icon == "cloud-sun":
                icon = "cloud-moon"
            if theme in ["clear", "partly-cloudy"]:
                theme = f"{theme}-night"
        else:
            if theme in ["clear", "partly-cloudy"]:
                theme = f"{theme}-day"

        return {"desc": desc, "icon": icon, "theme": theme}

    def search_locations(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        cache_key = f"{query.lower()}_{count}"
        cached = self._search_cache.get(cache_key)
        if cached and time.time() - cached["timestamp"] < self.cache_ttl:
            return cached["data"]

        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": query,
            "count": count,
            "language": "en",
            "format": "json"
        }

        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json().get("results", [])
                formatted = []
                for item in data:
                    formatted.append({
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "latitude": item.get("latitude"),
                        "longitude": item.get("longitude"),
                        "country": item.get("country", ""),
                        "country_code": item.get("country_code", ""),
                        "admin1": item.get("admin1", ""),
                        "display_name": f"{item.get('name')}, {item.get('admin1', '')} {item.get('country', '')}".replace(" ,", "").strip(", ")
                    })
                self._search_cache[cache_key] = {"data": formatted, "timestamp": time.time()}
                return formatted
        except Exception:
            pass

        # Fallback to local default locations if network is unreachable
        mock_locations = [
            {"name": "London", "latitude": 51.5074, "longitude": -0.1278, "country": "United Kingdom", "admin1": "England"},
            {"name": "New York", "latitude": 40.7128, "longitude": -74.0060, "country": "United States", "admin1": "New York"},
            {"name": "Tokyo", "latitude": 35.6762, "longitude": 139.6503, "country": "Japan", "admin1": "Tokyo"},
            {"name": "Paris", "latitude": 48.8566, "longitude": 2.3522, "country": "France", "admin1": "Île-de-France"},
            {"name": "Sydney", "latitude": -33.8688, "longitude": 151.2093, "country": "Australia", "admin1": "New South Wales"}
        ]
        filtered = [loc for loc in mock_locations if query.lower() in loc["name"].lower()]
        for loc in filtered:
            loc["display_name"] = f"{loc['name']}, {loc.get('admin1', '')} {loc.get('country', '')}".strip()
        return filtered

    def get_weather(self, lat: float, lon: float, units: str = "metric", location_name: Optional[str] = None) -> Dict[str, Any]:
        temp_unit = "fahrenheit" if units == "imperial" else "celsius"
        wind_unit = "mph" if units == "imperial" else "kmh"
        precip_unit = "inch" if units == "imperial" else "mm"

        cache_key = f"{round(lat, 2)}_{round(lon, 2)}_{units}"
        cached = self._weather_cache.get(cache_key)
        if cached and time.time() - cached["timestamp"] < self.cache_ttl:
            result = dict(cached["data"])
            if location_name:
                result["location_name"] = location_name
            return result

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
            "hourly": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code,wind_speed_10m,uv_index",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,uv_index_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
            "timezone": "auto",
            "temperature_unit": temp_unit,
            "wind_speed_unit": wind_unit,
            "precipitation_unit": precip_unit
        }

        try:
            resp = requests.get(url, params=params, timeout=6)
            if resp.status_code == 200:
                raw_data = resp.json()
                processed = self._process_weather_data(raw_data, units, location_name)
                self._weather_cache[cache_key] = {"data": processed, "timestamp": time.time()}
                return processed
        except Exception:
            pass

        # Return structured mock data if network is unavailable
        return self._generate_mock_weather(lat, lon, units, location_name)

    def _process_weather_data(self, data: Dict[str, Any], units: str, location_name: Optional[str]) -> Dict[str, Any]:
        current_raw = data.get("current", {})
        hourly_raw = data.get("hourly", {})
        daily_raw = data.get("daily", {})

        is_day = current_raw.get("is_day", 1)
        w_code = current_raw.get("weather_code", 0)
        w_info = self.get_weather_info(w_code, is_day)

        temp_symbol = "°F" if units == "imperial" else "°C"
        wind_symbol = "mph" if units == "imperial" else "km/h"
        precip_symbol = "in" if units == "imperial" else "mm"

        # Current weather
        current = {
            "temperature": round(current_raw.get("temperature_2m", 0)),
            "apparent_temperature": round(current_raw.get("apparent_temperature", 0)),
            "humidity": current_raw.get("relative_humidity_2m", 0),
            "wind_speed": round(current_raw.get("wind_speed_10m", 0), 1),
            "wind_direction": current_raw.get("wind_direction_10m", 0),
            "wind_compass": degrees_to_compass(current_raw.get("wind_direction_10m", 0)),
            "wind_gusts": round(current_raw.get("wind_gusts_10m", 0), 1),
            "pressure": round(current_raw.get("pressure_msl", 1013)),
            "cloud_cover": current_raw.get("cloud_cover", 0),
            "is_day": is_day,
            "weather_code": w_code,
            "description": w_info["desc"],
            "icon": w_info["icon"],
            "theme": w_info["theme"],
            "units": {
                "temp": temp_symbol,
                "wind": wind_symbol,
                "precip": precip_symbol
            }
        }

        # Hourly forecast (next 24 entries)
        hourly = []
        h_times = hourly_raw.get("time", [])
        h_temps = hourly_raw.get("temperature_2m", [])
        h_pops = hourly_raw.get("precipitation_probability", [])
        h_codes = hourly_raw.get("weather_code", [])
        h_winds = hourly_raw.get("wind_speed_10m", [])
        h_uvs = hourly_raw.get("uv_index", [])

        # Find current hour index or start from 0
        current_time_iso = current_raw.get("time", "")
        start_idx = 0
        if current_time_iso and current_time_iso in h_times:
            start_idx = h_times.index(current_time_iso)

        for i in range(start_idx, min(start_idx + 24, len(h_times))):
            t_str = h_times[i]
            # format hour label e.g., '14:00' -> '2 PM'
            time_part = t_str.split("T")[-1] if "T" in t_str else t_str
            hour_val = int(time_part.split(":")[0])
            hour_ampm = f"{12 if hour_val % 12 == 0 else hour_val % 12} {'AM' if hour_val < 12 else 'PM'}"
            if i == start_idx:
                hour_ampm = "Now"

            code = h_codes[i] if i < len(h_codes) else 0
            is_day_hour = 1 if 6 <= hour_val < 19 else 0
            info = self.get_weather_info(code, is_day_hour)

            hourly.append({
                "time": t_str,
                "hour_label": hour_ampm,
                "temperature": round(h_temps[i]) if i < len(h_temps) else 0,
                "pop": h_pops[i] if i < len(h_pops) else 0,
                "weather_code": code,
                "description": info["desc"],
                "icon": info["icon"],
                "wind_speed": round(h_winds[i], 1) if i < len(h_winds) else 0,
                "uv_index": round(h_uvs[i], 1) if i < len(h_uvs) else 0,
            })

        # Daily forecast (up to 7 days)
        daily = []
        d_times = daily_raw.get("time", [])
        d_code = daily_raw.get("weather_code", [])
        d_max = daily_raw.get("temperature_2m_max", [])
        d_min = daily_raw.get("temperature_2m_min", [])
        d_pop = daily_raw.get("precipitation_probability_max", [])
        d_precip = daily_raw.get("precipitation_sum", [])
        d_sunrises = daily_raw.get("sunrise", [])
        d_sunsets = daily_raw.get("sunset", [])
        d_uv = daily_raw.get("uv_index_max", [])

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i in range(min(7, len(d_times))):
            date_str = d_times[i]
            # determine weekday
            try:
                import datetime
                dt = datetime.date.fromisoformat(date_str)
                day_name = "Today" if i == 0 else ("Tomorrow" if i == 1 else days_of_week[dt.weekday()])
            except Exception:
                day_name = f"Day {i+1}"

            code = d_code[i] if i < len(d_code) else 0
            info = self.get_weather_info(code, 1)

            sunrise_str = d_sunrises[i].split("T")[-1][:5] if i < len(d_sunrises) and "T" in d_sunrises[i] else "06:00"
            sunset_str = d_sunsets[i].split("T")[-1][:5] if i < len(d_sunsets) and "T" in d_sunsets[i] else "18:00"

            daily.append({
                "date": date_str,
                "day_name": day_name,
                "max_temp": round(d_max[i]) if i < len(d_max) else 0,
                "min_temp": round(d_min[i]) if i < len(d_min) else 0,
                "pop": d_pop[i] if i < len(d_pop) else 0,
                "precipitation": round(d_precip[i], 1) if i < len(d_precip) else 0,
                "weather_code": code,
                "description": info["desc"],
                "icon": info["icon"],
                "sunrise": sunrise_str,
                "sunset": sunset_str,
                "uv_index_max": round(d_uv[i], 1) if i < len(d_uv) else 0
            })

        # Add current UV index and sunrise/sunset from day 0 to current
        if daily:
            current["sunrise"] = daily[0]["sunrise"]
            current["sunset"] = daily[0]["sunset"]
            current["uv_index"] = daily[0]["uv_index_max"]
        else:
            current["sunrise"] = "06:30"
            current["sunset"] = "18:45"
            current["uv_index"] = 4.0

        return {
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "timezone": data.get("timezone", "UTC"),
            "location_name": location_name or f"{data.get('latitude'):.2f}, {data.get('longitude'):.2f}",
            "current": current,
            "hourly": hourly,
            "daily": daily,
            "is_live": True
        }

    def _generate_mock_weather(self, lat: float, lon: float, units: str, location_name: Optional[str]) -> Dict[str, Any]:
        temp_symbol = "°F" if units == "imperial" else "°C"
        wind_symbol = "mph" if units == "imperial" else "km/h"
        precip_symbol = "in" if units == "imperial" else "mm"
        base_temp = 68 if units == "imperial" else 20

        current = {
            "temperature": base_temp,
            "apparent_temperature": base_temp + 1,
            "humidity": 55,
            "wind_speed": 12.5,
            "wind_direction": 210,
            "wind_compass": "SSW",
            "wind_gusts": 18.0,
            "pressure": 1015,
            "cloud_cover": 25,
            "is_day": 1,
            "weather_code": 1,
            "description": "Mainly clear",
            "icon": "cloud-sun",
            "theme": "partly-cloudy-day",
            "sunrise": "06:35",
            "sunset": "18:45",
            "uv_index": 5.2,
            "units": {"temp": temp_symbol, "wind": wind_symbol, "precip": precip_symbol}
        }

        hourly = []
        for i in range(24):
            hour = (12 + i) % 24
            ampm = f"{12 if hour % 12 == 0 else hour % 12} {'AM' if hour < 12 else 'PM'}"
            hourly.append({
                "time": f"2026-10-21T{hour:02d}:00",
                "hour_label": "Now" if i == 0 else ampm,
                "temperature": base_temp + (2 if 12 <= hour <= 16 else -3),
                "pop": 10 if i % 3 == 0 else 0,
                "weather_code": 1,
                "description": "Mainly clear",
                "icon": "cloud-sun" if 6 <= hour < 19 else "cloud-moon",
                "wind_speed": 10.0,
                "uv_index": 4.0 if 10 <= hour <= 15 else 0.0
            })

        days = ["Today", "Tomorrow", "Fri", "Sat", "Sun", "Mon", "Tue"]
        daily = []
        for i, day in enumerate(days):
            daily.append({
                "date": f"2026-10-{21+i:02d}",
                "day_name": day,
                "max_temp": base_temp + 3 + (i % 2),
                "min_temp": base_temp - 6 - (i % 3),
                "pop": 15 if i == 2 else 5,
                "precipitation": 0.5 if i == 2 else 0.0,
                "weather_code": 1 if i != 2 else 61,
                "description": "Slight rain" if i == 2 else "Mainly clear",
                "icon": "cloud-rain" if i == 2 else "sun",
                "sunrise": "06:35",
                "sunset": "18:45",
                "uv_index_max": 5.5
            })

        return {
            "latitude": lat,
            "longitude": lon,
            "timezone": "UTC",
            "location_name": location_name or "Demo City",
            "current": current,
            "hourly": hourly,
            "daily": daily,
            "is_live": False
        }

# Global singleton service
weather_service = WeatherService()
