import unittest
import json
from app import app
from services.weather_service import weather_service, degrees_to_compass, WMO_CODE_MAP

class WeatherAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

    def test_degrees_to_compass(self):
        self.assertEqual(degrees_to_compass(0), "N")
        self.assertEqual(degrees_to_compass(90), "E")
        self.assertEqual(degrees_to_compass(180), "S")
        self.assertEqual(degrees_to_compass(270), "W")

    def test_wmo_code_mapping(self):
        info_day = weather_service.get_weather_info(0, is_day=1)
        self.assertEqual(info_day["desc"], "Clear sky")
        self.assertEqual(info_day["icon"], "sun")
        self.assertEqual(info_day["theme"], "clear-day")

        info_night = weather_service.get_weather_info(0, is_day=0)
        self.assertEqual(info_night["icon"], "moon")
        self.assertEqual(info_night["theme"], "clear-night")

        rain_info = weather_service.get_weather_info(61, is_day=1)
        self.assertIn("rain", rain_info["desc"].lower())
        self.assertEqual(rain_info["theme"], "rain")

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SkyPulse", response.data)

    def test_health_route(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "ok")

    def test_search_api_mock_or_live(self):
        response = self.client.get("/api/search?q=London")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("London", data[0]["name"])

    def test_weather_api_with_coords(self):
        response = self.client.get("/api/weather?lat=51.5074&lon=-0.1278&units=metric")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("current", data)
        self.assertIn("temperature", data["current"])
        self.assertIn("hourly", data)
        self.assertIn("daily", data)
        self.assertEqual(data["current"]["units"]["temp"], "°C")

    def test_weather_api_imperial_units(self):
        response = self.client.get("/api/weather?lat=40.7128&lon=-74.0060&units=imperial")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["current"]["units"]["temp"], "°F")
        self.assertEqual(data["current"]["units"]["wind"], "mph")

    def test_weather_api_city_search(self):
        response = self.client.get("/api/weather?city=Paris&units=metric")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("Paris", data["location_name"])
        self.assertIn("current", data)

if __name__ == "__main__":
    unittest.main()
