"""
JARVIS Security and Guardrails Module
Validates filesystem paths, prevents path traversal, manages action confirmations,
and provides emergency stop safeguards.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Tuple, Optional
from app.config import APPROVED_DIRECTORIES, USER_PROFILE


class SecurityGuardrails:
    """Enforces safety constraints across computer control actions."""

    _emergency_stop_triggered: bool = False

    @classmethod
    def trigger_emergency_stop(cls):
        """Immediately halts pending and active operations."""
        cls._emergency_stop_triggered = True

    @classmethod
    def reset_emergency_stop(cls):
        """Resets the emergency stop state."""
        cls._emergency_stop_triggered = False

    @classmethod
    def is_stopped(cls) -> bool:
        return cls._emergency_stop_triggered

    @classmethod
    def validate_path(cls, path_str: str, allow_create_parent: bool = False) -> Tuple[bool, Optional[Path], str]:
        """
        Validates that a path stays within approved directories (Desktop, Documents, Downloads, Project Root).
        Protects against path traversal (e.g. C:\\Windows, System32, Root drives).
        """
        try:
            target_clean = path_str.strip().replace("/", "\\")
            # If path starts with "Desktop\" or "desktop\", strip it so it resolves relative to DESKTOP_DIR
            if target_clean.lower().startswith("desktop\\"):
                target_clean = target_clean[8:].lstrip("\\/")
            elif target_clean.lower() == "desktop":
                target_clean = ""

            target = Path(target_clean).expanduser()
            # If relative, resolve relative to user desktop by default
            if not target.is_absolute():
                target = (Path(APPROVED_DIRECTORIES[0]) / target).resolve()
            else:
                target = target.resolve()

            # Prevent system directories
            target_str = str(target).lower()
            forbidden_prefixes = [
                r"c:\windows",
                r"c:\program files",
                r"c:\program files (x86)",
                r"c:\system volume information",
                r"c:\recovery"
            ]
            for forb in forbidden_prefixes:
                if target_str.startswith(forb):
                    return False, None, f"Access denied: System directory '{target}' is protected."

            # Verify it resides within an approved folder or user profile
            is_approved = False
            for approved in APPROVED_DIRECTORIES:
                try:
                    if target == approved or approved in target.parents:
                        is_approved = True
                        break
                except Exception:
                    pass

            # Also allow subfolders directly under user profile if safe
            if not is_approved and USER_PROFILE in target.parents:
                is_approved = True

            if not is_approved:
                return False, None, f"Access denied: Target '{target}' is outside approved directories."

            return True, target, "Path approved."
        except Exception as e:
            return False, None, f"Path validation error: {str(e)}"

    @classmethod
    def sanitize_log(cls, text: str) -> str:
        """Redacts sensitive API keys, passwords, and tokens from logs."""
        if not text:
            return ""
        # Redact OpenRouter / OpenAI keys
        sanitized = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED_API_KEY]", text)
        sanitized = re.sub(r"AIza[a-zA-Z0-9_-]{35}", "[REDACTED_GOOGLE_KEY]", sanitized)
        sanitized = re.sub(r"GOCSPX-[a-zA-Z0-9_-]{20,}", "[REDACTED_SECRET]", sanitized)
        return sanitized
