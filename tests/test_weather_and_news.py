"""
Integration tests for Weather and News providers using provided live API keys.
"""

from app.integrations.weather.weather_client import GetWeatherTool, weather_client
from app.integrations.news.news_client import GetNewsTool, news_client


def test_weather_live_api():
    tool = GetWeatherTool()
    res = tool.execute(city="Hyderabad")
    assert res.success is True
    assert "Hyderabad" in res.message
    assert "°C" in res.message
    assert "humidity" in res.message.lower()


def test_weather_tomorrow_forecast():
    tool = GetWeatherTool()
    res = tool.execute(city="Hyderabad", target_day="tomorrow")
    assert res.success is True
    assert "Tomorrow in Hyderabad" in res.message or "Hyderabad" in res.message


def test_news_live_api():
    tool = GetNewsTool()
    res = tool.execute(query="technology")
    assert res.success is True
    assert len(res.data.get("articles", [])) > 0
    assert "technology" in res.message.lower()
