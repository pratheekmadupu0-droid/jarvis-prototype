"""
Unit tests for JARVIS Time, Date, and Scheduler functions.
Verifies real local time, world time zones, countdown timers, and persistent reminders.
"""

from datetime import datetime, timedelta
from app.tools.time_tools import GetTimeTool, GetDateTool, CalculateTimeUntilTool
from app.scheduler.timer_manager import SetTimerTool, SetReminderTool, ListRemindersTool, CancelReminderTool, timer_manager
from app.storage.database import db


def test_get_local_time():
    tool = GetTimeTool()
    res = tool.execute()
    assert res.success is True
    assert "The current time is" in res.message


def test_get_world_time():
    tool = GetTimeTool()
    res = tool.execute(city="London")
    assert res.success is True
    assert "London" in res.message


def test_get_date():
    tool = GetDateTool()
    res = tool.execute(relative_target="today")
    assert res.success is True
    assert datetime.now().strftime("%Y") in res.message


def test_calculate_time_until():
    tool = CalculateTimeUntilTool()
    res = tool.execute(target_time="11:59 PM")
    assert res.success is True
    assert "until 11:59 PM" in res.message


def test_timer_and_reminder_lifecycle():
    set_timer = SetTimerTool()
    set_rem = SetReminderTool()
    list_tool = ListRemindersTool()
    cancel_tool = CancelReminderTool()

    # 1. Set Timer
    t_res = set_timer.execute(duration="20 seconds", label="Test Quick Timer")
    assert t_res.success is True

    # 2. Set Reminder
    r_res = set_rem.execute(title="Test Meeting with Client", target_time="in 2 hours")
    assert r_res.success is True
    assert "Meeting with Client" in r_res.message

    # 3. List
    list_res = list_tool.execute()
    assert list_res.success is True
    assert "Meeting with Client" in list_res.message

    # 4. Cancel
    c_res = cancel_tool.execute(identifier="Meeting with Client")
    assert c_res.success is True
