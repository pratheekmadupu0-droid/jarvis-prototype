"""
JARVIS Persistent SQLite Database Layer
Stores reminders, tasks history, audit logs, and user memory.
"""

from __future__ import annotations
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.config import DB_PATH


class Database:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Create tables if they don't already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Reminders & Timers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_time TEXT NOT NULL,
                    is_recurring INTEGER DEFAULT 0,
                    recurrence_pattern TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT NOT NULL
                )
            """)

            # Task & Audit history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_name TEXT NOT NULL,
                    intent TEXT,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL,
                    finished_at TEXT
                )
            """)

            # User Memory & Facts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    updated_at TEXT NOT NULL
                )
            """)

            # Persistent Key-Value Settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            conn.commit()

    # --- REMINDERS ---

    def add_reminder(self, title: str, due_time: datetime, is_recurring: bool = False, recurrence_pattern: Optional[str] = None) -> int:
        now_str = datetime.now().isoformat()
        due_str = due_time.isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders (title, due_time, is_recurring, recurrence_pattern, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
            """, (title, due_str, 1 if is_recurring else 0, recurrence_pattern, now_str))
            conn.commit()
            return cursor.lastrowid

    def get_pending_reminders(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders WHERE status = 'pending' ORDER BY due_time ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_reminder_status(self, reminder_id: int, status: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET status = ? WHERE id = ?", (status, reminder_id))
            conn.commit()

    def cancel_reminder(self, reminder_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE reminders SET status = 'cancelled' WHERE id = ?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- TASK HISTORY & AUDIT ---

    def log_task(self, task_name: str, intent: str, status: str, details: Optional[Dict[str, Any]] = None) -> int:
        now_str = datetime.now().isoformat()
        details_str = json.dumps(details or {})
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO task_history (task_name, intent, status, details, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (task_name, intent, status, details_str, now_str))
            conn.commit()
            return cursor.lastrowid

    def update_task_status(self, task_id: int, status: str, details: Optional[Dict[str, Any]] = None):
        now_str = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if details:
                cursor.execute("""
                    UPDATE task_history
                    SET status = ?, details = ?, finished_at = ?
                    WHERE id = ?
                """, (status, json.dumps(details), now_str, task_id))
            else:
                cursor.execute("""
                    UPDATE task_history
                    SET status = ?, finished_at = ?
                    WHERE id = ?
                """, (status, now_str, task_id))
            conn.commit()

    def get_recent_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM task_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            res = []
            for r in rows:
                d = dict(r)
                try:
                    d["details"] = json.loads(d["details"])
                except Exception:
                    pass
                res.append(d)
            return res

    # --- MEMORY ---

    def set_memory(self, key: str, value: str, category: str = "general"):
        now_str = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memory (key, value, category, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = excluded.updated_at
            """, (key, value, category, now_str))
            conn.commit()

    def get_memory(self, key: str) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memory WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None

    def get_all_memory(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM memory ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def delete_memory(self, key: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
            conn.commit()
            return cursor.rowcount > 0

    # --- SETTINGS ---

    def set_setting(self, key: str, value: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else default


# Global singleton instance
db = Database()
