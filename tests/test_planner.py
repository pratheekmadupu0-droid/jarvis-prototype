"""
Tests for AI Planner and Multi-Step Execution Engine.
Verifies intent matching, decomposition, step reporting, and emergency stop.
"""

from app.ai.planner import planner
from app.security.guardrails import SecurityGuardrails


def test_planner_direct_time_query():
    res = planner.plan_and_execute("JARVIS, what is the current time?")
    assert res["status"] == "completed"
    assert "The current time is" in res["response"]


def test_planner_direct_weather_query():
    res = planner.plan_and_execute("JARVIS, what is the weather in Hyderabad today?")
    assert res["status"] == "completed"
    assert "Hyderabad" in res["response"]


def test_planner_emergency_stop_halts_execution():
    SecurityGuardrails.trigger_emergency_stop()
    res = planner.plan_and_execute("JARVIS, create a folder named Malicious on my desktop")
    assert res["status"] in ("failed", "cancelled")
    SecurityGuardrails.reset_emergency_stop()
