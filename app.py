import os
from flask import Flask, render_template, request, jsonify
from services.weather_service import weather_service

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/search")
def search_locations():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    try:
        results = weather_service.search_locations(query, count=6)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/weather")
def get_weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    city = request.args.get("city", "").strip()
    units = request.args.get("units", "metric").lower()
    if units not in ["metric", "imperial"]:
        units = "metric"

    location_name = None

    # If city is passed without lat/lon, geocode first
    if (lat is None or lon is None) and city:
        matches = weather_service.search_locations(city, count=1)
        if matches:
            lat = matches[0]["latitude"]
            lon = matches[0]["longitude"]
            location_name = matches[0]["display_name"]
        else:
            return jsonify({"error": f"City '{city}' not found."}), 404

    # Default fallback to London if nothing specified
    if lat is None or lon is None:
        lat = 51.5074
        lon = -0.1278
        location_name = "London, Greater London, United Kingdom"

    try:
        weather_data = weather_service.get_weather(
            lat=lat,
            lon=lon,
            units=units,
            location_name=location_name
        )
        return jsonify(weather_data)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve weather data: {str(e)}"}), 500

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "Live Weather App"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
