"""
JARVIS User Memory and Continuity Manager
Handles permitted user facts, preferences, project directories, and common contacts.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from app.storage.database import db


class MemoryManager:
    """Manages explicit user preferences and recall."""

    def __init__(self, database=db):
        self.db = database

    def remember(self, key: str, value: str, category: str = "preference") -> str:
        """Store a fact or preference."""
        self.db.set_memory(key.strip().lower(), value.strip(), category)
        return f"Remembered: '{key}' is set to '{value}'."

    def recall(self, key: str) -> Optional[str]:
        """Retrieve a stored fact or preference."""
        return self.db.get_memory(key.strip().lower())

    def forget(self, key: str) -> bool:
        """Delete a stored memory item."""
        return self.db.delete_memory(key.strip().lower())

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all stored memories."""
        return self.db.get_all_memory()

    def summarize_memory_context(self) -> str:
        """Construct a prompt prefix string with known preferences for AI reasoning."""
        memories = self.get_all()
        if not memories:
            return ""
        lines = ["User Preferences and Permitted Memory:"]
        for m in memories:
            lines.append(f"- {m['key'].capitalize()}: {m['value']} ({m['category']})")
        return "\n".join(lines)


memory_manager = MemoryManager()
