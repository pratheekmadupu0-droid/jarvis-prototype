"""
JARVIS Weather Integration
Connects to OpenWeatherMap API to retrieve real-time weather, feels-like temperature,
rain probability, humidity, wind, forecasts for tomorrow and upcoming days, sunrise/sunset.
"""

from __future__ import annotations
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.config import Config
from app.tools.base import BaseTool, ToolResult
from app.memory.memory_manager import memory_manager


class WeatherClient:
    """OpenWeatherMap API Client."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: str = Config.WEATHER_API_KEY):
        self.api_key = api_key

    def get_current_weather(self, city: str) -> Dict[str, Any]:
        """Fetch current weather data for a city."""
        url = f"{self.BASE_URL}/weather"
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_forecast(self, city: str) -> Dict[str, Any]:
        """Fetch 5-day / 3-hour forecast data."""
        url = f"{self.BASE_URL}/forecast"
        params = {"q": city, "appid": self.api_key, "units": "metric"}
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        return res.json()

    def get_weather_report(self, city: Optional[str] = None, target_day: str = "today") -> Dict[str, Any]:
        """Generate structured weather report and summary string."""
        target_city = city or memory_manager.recall("preferred_city") or Config.DEFAULT_CITY

        try:
            current_data = self.get_current_weather(target_city)
            forecast_data = self.get_forecast(target_city)
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve weather for {target_city}: {str(e)}"}

        main = current_data.get("main", {})
        weather_desc = current_data.get("weather", [{}])[0].get("description", "clear")
        wind = current_data.get("wind", {})
        sys = current_data.get("sys", {})

        sunrise_ts = sys.get("sunrise")
        sunset_ts = sys.get("sunset")
        sunrise = datetime.fromtimestamp(sunrise_ts).strftime("%I:%M %p") if sunrise_ts else "N/A"
        sunset = datetime.fromtimestamp(sunset_ts).strftime("%I:%M %p") if sunset_ts else "N/A"

        # Check rain forecast
        forecast_list = forecast_data.get("list", [])
        rain_prob = 0.0
        tomorrow_forecast_text = ""
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        tomorrow_temps = []
        tomorrow_conditions = []
        for item in forecast_list:
            dt_txt = item.get("dt_txt", "")
            pop = item.get("pop", 0.0)
            if pop > rain_prob:
                rain_prob = pop

            if dt_txt.startswith(tomorrow_date):
                tomorrow_temps.append(item.get("main", {}).get("temp", 0))
                cond = item.get("weather", [{}])[0].get("description", "")
                if cond and cond not in tomorrow_conditions:
                    tomorrow_conditions.append(cond)

        rain_pct = int(rain_prob * 100)

        report = {
            "success": True,
            "city": current_data.get("name", target_city),
            "country": sys.get("country", ""),
            "temp": round(main.get("temp", 0), 1),
            "feels_like": round(main.get("feels_like", 0), 1),
            "temp_min": round(main.get("temp_min", 0), 1),
            "temp_max": round(main.get("temp_max", 0), 1),
            "humidity": main.get("humidity", 0),
            "condition": weather_desc.title(),
            "wind_speed": wind.get("speed", 0),
            "rain_probability": rain_pct,
            "sunrise": sunrise,
            "sunset": sunset,
            "observation_time": datetime.now().strftime("%I:%M %p"),
        }

        if tomorrow_temps:
            avg_temp = round(sum(tomorrow_temps) / len(tomorrow_temps), 1)
            report["tomorrow"] = {
                "avg_temp": avg_temp,
                "conditions": ", ".join(tomorrow_conditions)
            }

        # Format natural spoken summary
        if target_day.lower() == "tomorrow" and "tomorrow" in report:
            summary = (
                f"Tomorrow in {report['city']}, expect {report['tomorrow']['conditions']} "
                f"with an average temperature of {report['tomorrow']['avg_temp']}°C "
                f"and a {report['rain_probability']}% chance of rain."
            )
        else:
            summary = (
                f"In {report['city']}, it is currently {report['temp']}°C (feels like {report['feels_like']}°C) "
                f"with {report['condition'].lower()}. Humidity is {report['humidity']}%, wind speed is {report['wind_speed']} m/s, "
                f"and rain probability is {report['rain_probability']}%. Sunset will be at {report['sunset']}."
            )

        report["summary"] = summary
        return report


weather_client = WeatherClient()


class GetWeatherTool(BaseTool):
    name = "get_weather"
    description = "Retrieve current weather, temperature, humidity, wind, and forecast for any city."
    parameters_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name (e.g. 'Hyderabad', 'London', 'New York')"},
            "target_day": {"type": "string", "description": "'today' or 'tomorrow'"}
        }
    }

    def execute(self, city: Optional[str] = None, target_day: str = "today") -> ToolResult:
        res = weather_client.get_weather_report(city=city, target_day=target_day)
        if not res.get("success"):
            return ToolResult(success=False, message=res.get("error", "Weather data unavailable."))
        return ToolResult(success=True, message=res["summary"], data=res)
