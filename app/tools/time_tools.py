"""
JARVIS Time, Date, and Time Zone Tools
Retrieves current real local time, dates, relative calculations, and world timezones.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import zoneinfo
from typing import Optional
from app.tools.base import BaseTool, ToolResult

CITY_TIMEZONES = {
    "london": "Europe/London",
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "san francisco": "America/Los_Angeles",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "tokyo": "Asia/Tokyo",
    "hyderabad": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "mumbai": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata",
    "india": "Asia/Kolkata",
    "dubai": "Asia/Dubai",
    "singapore": "Asia/Singapore",
    "sydney": "Australia/Sydney",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
}


class GetTimeTool(BaseTool):
    name = "get_time"
    description = "Get the current time, either locally or in a specific city/timezone."
    parameters_schema = {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "Optional city name (e.g. 'London', 'New York', 'Tokyo')"}
        }
    }

    def execute(self, city: Optional[str] = None) -> ToolResult:
        now = datetime.now()
        if not city or str(city).strip().lower() in ("none", "", "local"):
            time_str = now.strftime("%I:%M %p")
            date_str = now.strftime("%A, %B %d, %Y")
            return ToolResult(
                success=True,
                message=f"The current time is {time_str} ({date_str}).",
                data={"time": time_str, "date": date_str}
            )

        city_clean = city.strip().lower()
        tz_name = CITY_TIMEZONES.get(city_clean)
        if not tz_name:
            # Fallback to direct timezone lookup
            try:
                zoneinfo.ZoneInfo(city)
                tz_name = city
            except Exception:
                return ToolResult(
                    success=False,
                    message=f"Time zone for city '{city}' not recognized. Please specify a major city."
                )

        try:
            tz = zoneinfo.ZoneInfo(tz_name)
            city_time = datetime.now(tz)
            time_str = city_time.strftime("%I:%M %p")
            date_str = city_time.strftime("%A, %B %d, %Y")
            return ToolResult(
                success=True,
                message=f"The current time in {city.title()} is {time_str} ({date_str}).",
                data={"city": city.title(), "time": time_str, "date": date_str, "timezone": tz_name}
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to calculate time for {city}: {str(e)}")


class GetDateTool(BaseTool):
    name = "get_date"
    description = "Get today's date, tomorrow's date, or relative days (e.g. 'next monday')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "relative_target": {"type": "string", "description": "Optional relative target e.g. 'today', 'tomorrow', 'next monday'"}
        }
    }

    def execute(self, relative_target: Optional[str] = None) -> ToolResult:
        now = datetime.now()
        target = (relative_target or "today").strip().lower()

        if target == "today":
            dt = now
            msg = f"Today is {dt.strftime('%A, %B %d, %Y')}."
        elif target == "tomorrow":
            dt = now + timedelta(days=1)
            msg = f"Tomorrow is {dt.strftime('%A, %B %d, %Y')}."
        elif "next monday" in target:
            days_ahead = (0 - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            dt = now + timedelta(days=days_ahead)
            msg = f"Next Monday is {dt.strftime('%A, %B %d, %Y')}."
        elif "yesterday" in target:
            dt = now - timedelta(days=1)
            msg = f"Yesterday was {dt.strftime('%A, %B %d, %Y')}."
        else:
            dt = now
            msg = f"Today is {dt.strftime('%A, %B %d, %Y')}."

        return ToolResult(
            success=True,
            message=msg,
            data={"date": dt.strftime("%Y-%m-%d"), "formatted": dt.strftime("%A, %B %d, %Y")}
        )


class CalculateTimeUntilTool(BaseTool):
    name = "calculate_time_until"
    description = "Calculate the hours and minutes remaining until a specified time of day (e.g. '6 PM' or '18:00')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "target_time": {"type": "string", "description": "Target time of day e.g. '6 PM', '18:00', '11:30 AM'"}
        },
        "required": ["target_time"]
    }

    def execute(self, target_time: str) -> ToolResult:
        now = datetime.now()
        # Parse target time
        clean = target_time.strip().upper()
        parsed_dt = None
        for fmt in ["%I %p", "%I:%M %p", "%H:%M", "%I%p"]:
            try:
                t = datetime.strptime(clean, fmt).time()
                parsed_dt = datetime.combine(now.date(), t)
                break
            except Exception:
                pass

        if not parsed_dt:
            return ToolResult(success=False, message=f"Could not parse time '{target_time}'. Please format as '6 PM' or '18:00'.")

        if parsed_dt < now:
            # Assume tomorrow
            parsed_dt += timedelta(days=1)

        diff = parsed_dt - now
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        parts = []
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0 or not parts:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        msg = f"There are {' and '.join(parts)} until {target_time}."
        return ToolResult(success=True, message=msg, data={"hours": hours, "minutes": minutes, "seconds": total_seconds})
