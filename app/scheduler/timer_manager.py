"""
JARVIS Timers & Persistent Reminders Scheduler
Runs a background scheduler thread checking SQLite-persisted reminders and countdown timers.
Notifies the UI and speaks reminders via voice output when timers expire.
"""

from __future__ import annotations
import threading
import time
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from app.storage.database import db
from app.tools.base import BaseTool, ToolResult


class TimerManager:
    """Manages active timers and persistent database reminders."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.active_timers: List[Dict[str, Any]] = []

        # Callbacks
        self.on_reminder_triggered: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_timer_tick: Optional[Callable[[List[Dict[str, Any]]], None]] = None

    def start(self):
        """Start scheduler daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop scheduler."""
        self._running = False

    def set_timer(self, duration_seconds: int, label: str = "Timer") -> Dict[str, Any]:
        """Start a countdown timer."""
        due_time = datetime.now() + timedelta(seconds=duration_seconds)
        timer_id = db.add_reminder(title=label, due_time=due_time)

        timer_item = {
            "id": timer_id,
            "title": label,
            "due_time": due_time,
            "duration": duration_seconds,
            "remaining": duration_seconds,
            "is_timer": True
        }
        with self._lock:
            self.active_timers.append(timer_item)

        return timer_item

    def set_reminder(self, title: str, due_time: datetime, is_recurring: bool = False, pattern: Optional[str] = None) -> int:
        """Add a persistent reminder."""
        return db.add_reminder(title=title, due_time=due_time, is_recurring=is_recurring, recurrence_pattern=pattern)

    def cancel_reminder_or_timer(self, identifier: str) -> bool:
        """Cancel a timer or reminder by ID or matching title."""
        cancelled = False
        with self._lock:
            # Check active timers
            for t in list(self.active_timers):
                if str(t["id"]) == identifier or identifier.lower() in t["title"].lower():
                    self.active_timers.remove(t)
                    db.cancel_reminder(t["id"])
                    cancelled = True

        # Check pending reminders in DB
        pending = db.get_pending_reminders()
        for r in pending:
            if str(r["id"]) == identifier or identifier.lower() in r["title"].lower():
                db.cancel_reminder(r["id"])
                cancelled = True

        return cancelled

    def get_pending(self) -> List[Dict[str, Any]]:
        """Return all pending reminders and active countdowns."""
        return db.get_pending_reminders()

    def _scheduler_loop(self):
        """Background loop executing every second."""
        while self._running:
            now = datetime.now()

            # Update active countdown timers
            with self._lock:
                for t in list(self.active_timers):
                    rem = int((t["due_time"] - now).total_seconds())
                    t["remaining"] = max(0, rem)
                    if rem <= 0:
                        self.active_timers.remove(t)
                        db.update_reminder_status(t["id"], "completed")
                        if self.on_reminder_triggered:
                            try:
                                self.on_reminder_triggered(t)
                            except Exception:
                                pass

            # Check DB reminders
            try:
                pending = db.get_pending_reminders()
                for r in pending:
                    # Ignore if handled as active timer
                    with self._lock:
                        if any(t["id"] == r["id"] for t in self.active_timers):
                            continue

                    due_dt = datetime.fromisoformat(r["due_time"])
                    if due_dt <= now:
                        db.update_reminder_status(r["id"], "completed")
                        if self.on_reminder_triggered:
                            try:
                                self.on_reminder_triggered(r)
                            except Exception:
                                pass
            except Exception as e:
                print(f"[Scheduler] Loop check error: {e}")

            # Notify GUI tick
            if self.on_timer_tick:
                with self._lock:
                    try:
                        self.on_timer_tick(list(self.active_timers))
                    except Exception:
                        pass

            time.sleep(1.0)


timer_manager = TimerManager()


class SetTimerTool(BaseTool):
    name = "set_timer"
    description = "Set a countdown timer for a specified number of minutes or seconds (e.g. '10 minutes', '30 seconds')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "duration": {"type": "string", "description": "Duration string (e.g. '10 minutes', '2 hours', '45 seconds')"},
            "label": {"type": "string", "description": "Optional label or description for the timer"}
        },
        "required": ["duration"]
    }

    def execute(self, duration: str, label: Optional[str] = None) -> ToolResult:
        # Parse duration
        seconds = 0
        dur = duration.lower()
        m_sec = re.search(r"(\d+)\s*(s|sec|second)", dur)
        m_min = re.search(r"(\d+)\s*(m|min|minute)", dur)
        m_hr = re.search(r"(\d+)\s*(h|hr|hour)", dur)

        if m_sec:
            seconds += int(m_sec.group(1))
        if m_min:
            seconds += int(m_min.group(1)) * 60
        if m_hr:
            seconds += int(m_hr.group(1)) * 3600

        if seconds <= 0:
            # Fallback to plain integer as minutes
            digits = re.findall(r"\d+", dur)
            if digits:
                seconds = int(digits[0]) * 60
            else:
                return ToolResult(success=False, message=f"Could not parse timer duration from '{duration}'.")

        title = label or f"{duration} Timer"
        t = timer_manager.set_timer(seconds, label=title)
        return ToolResult(
            success=True,
            message=f"Timer set for {duration} ({title}). I will alert you when it completes.",
            data=t
        )


class SetReminderTool(BaseTool):
    name = "set_reminder"
    description = "Set a persistent calendar reminder at a specific time or date (e.g. 'tomorrow at 5 PM to work on ResQR')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "What to be reminded of"},
            "target_time": {"type": "string", "description": "When to be reminded (e.g. 'in 2 hours', 'tomorrow 5 PM', 'today 9 PM')"}
        },
        "required": ["title", "target_time"]
    }

    def execute(self, title: str, target_time: str) -> ToolResult:
        now = datetime.now()
        due_dt = None
        tt = target_time.lower()

        # Handle "in X hours/minutes"
        if "in " in tt:
            m_hr = re.search(r"in\s+(\d+)\s*hour", tt)
            m_min = re.search(r"in\s+(\d+)\s*min", tt)
            delta = timedelta()
            if m_hr:
                delta += timedelta(hours=int(m_hr.group(1)))
            if m_min:
                delta += timedelta(minutes=int(m_min.group(1)))
            if delta.total_seconds() > 0:
                due_dt = now + delta

        # Handle "tomorrow at 5 PM"
        if not due_dt and "tomorrow" in tt:
            base_date = (now + timedelta(days=1)).date()
            time_match = re.search(r"(\d+)(?::(\d+))?\s*(am|pm)?", tt)
            if time_match:
                hr = int(time_match.group(1))
                mn = int(time_match.group(2) or 0)
                meridiem = time_match.group(3)
                if meridiem == "pm" and hr < 12:
                    hr += 12
                elif meridiem == "am" and hr == 12:
                    hr = 0
                due_dt = datetime.combine(base_date, datetime.min.time().replace(hour=hr, minute=mn))

        if not due_dt:
            # Default to 1 hour from now
            due_dt = now + timedelta(hours=1)

        rem_id = timer_manager.set_reminder(title=title, due_time=due_dt)
        due_formatted = due_dt.strftime("%A, %B %d at %I:%M %p")
        return ToolResult(
            success=True,
            message=f"Reminder scheduled for {due_formatted}: '{title}'.",
            data={"id": rem_id, "title": title, "due_time": due_dt.isoformat()}
        )


class ListRemindersTool(BaseTool):
    name = "list_reminders"
    description = "List all pending reminders and active countdown timers."
    parameters_schema = {"type": "object", "properties": {}}

    def execute(self) -> ToolResult:
        reminders = timer_manager.get_pending()
        if not reminders:
            return ToolResult(success=True, message="You have no pending reminders or active timers.")

        lines = []
        for r in reminders:
            due = r["due_time"][:16].replace("T", " ")
            lines.append(f"- ID {r['id']}: '{r['title']}' due at {due}")

        return ToolResult(
            success=True,
            message=f"You have {len(reminders)} pending reminder(s):\n" + "\n".join(lines),
            data={"reminders": reminders}
        )


class CancelReminderTool(BaseTool):
    name = "cancel_reminder"
    description = "Cancel a reminder or timer by its title or ID."
    parameters_schema = {
        "type": "object",
        "properties": {
            "identifier": {"type": "string", "description": "Title or ID of the timer/reminder to cancel (e.g. '10 minutes', 'call client')"}
        },
        "required": ["identifier"]
    }

    def execute(self, identifier: str) -> ToolResult:
        success = timer_manager.cancel_reminder_or_timer(identifier)
        if success:
            return ToolResult(success=True, message=f"Cancelled reminder/timer matching '{identifier}'.")
        return ToolResult(success=False, message=f"No matching reminder or timer found for '{identifier}'.")
