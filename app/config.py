"""
JARVIS System Configuration Module
Handles loading environment variables, system paths, and dynamic runtime settings.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import tempfile

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"

if os.environ.get("VERCEL"):
    DATA_DIR = Path(tempfile.gettempdir()) / "jarvis_data"
else:
    DATA_DIR = PROJECT_ROOT / "data"

try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    DATA_DIR = Path(tempfile.gettempdir())

DB_PATH = DATA_DIR / "jarvis.db"

# User System Paths (Checking real Windows Registry / OneDrive shell mappings)
USER_PROFILE = Path(os.environ.get("USERPROFILE", Path.home()))

def _get_shell_path(folder_name: str, fallback_subpath: str) -> Path:
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            val, _ = winreg.QueryValueEx(key, folder_name)
            expanded = os.path.expandvars(val)
            p = Path(expanded)
            if p.exists():
                return p
    except Exception:
        pass
    onedrive_p = USER_PROFILE / "OneDrive" / fallback_subpath
    if onedrive_p.exists():
        return onedrive_p
    return USER_PROFILE / fallback_subpath

DESKTOP_DIR = _get_shell_path("Desktop", "Desktop")
DOCUMENTS_DIR = _get_shell_path("Personal", "Documents")
DOWNLOADS_DIR = USER_PROFILE / "Downloads"

# Approved Workspace Paths for safe computer control
APPROVED_DIRECTORIES = [
    DESKTOP_DIR,
    DOCUMENTS_DIR,
    DOWNLOADS_DIR,
    PROJECT_ROOT,
    USER_PROFILE / "Desktop",
    USER_PROFILE / "Documents"
]

# Load .env file
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Config:
    """System configuration holder."""

    # AI Reasoning
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "nvidia/nemotron-3.5-lightning:free")
    AI_FALLBACK_MODEL: str = os.getenv("AI_FALLBACK_MODEL", "openrouter/free")

    # APIs
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "f82b5de2fc55bee8f06bbf7842563a71")
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "f1bbed74f85740c28b53c758d9cd0a3d")
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "AIzaSyCwh00LcWExmzICPFYfpoWMW3DZjhRxUmk")

    # Integrations
    GMAIL_CREDENTIALS_FILE: Path = PROJECT_ROOT / os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    GMAIL_TOKEN_FILE: Path = DATA_DIR / os.getenv("GMAIL_TOKEN_FILE", "token.json")

    # Preferences
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Hyderabad")
    WAKE_WORD: str = os.getenv("WAKE_WORD", "jarvis").lower()
    SAFE_MODE: bool = os.getenv("SAFE_MODE", "true").lower() in ("true", "1", "yes")

    # Voice Output
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")  # 'edge-tts' or 'pyttsx3'
    VOICE_NAME: str = os.getenv("VOICE_NAME", "en-US-ChristopherNeural")
    VOICE_RATE: str = os.getenv("VOICE_RATE", "+0%")
    VOICE_PITCH: str = os.getenv("VOICE_PITCH", "+0Hz")

    # Speech Recognition
    STT_ENGINE: str = os.getenv("STT_ENGINE", "google")  # 'google' or 'whisper'

    @classmethod
    def get_dict(cls) -> dict:
        return {
            "ai_api_key_set": bool(cls.AI_API_KEY),
            "ai_base_url": cls.AI_BASE_URL,
            "ai_model": cls.AI_MODEL,
            "weather_api_key_set": bool(cls.WEATHER_API_KEY),
            "news_api_key_set": bool(cls.NEWS_API_KEY),
            "youtube_api_key_set": bool(cls.YOUTUBE_API_KEY),
            "gmail_credentials_exists": cls.GMAIL_CREDENTIALS_FILE.exists(),
            "default_city": cls.DEFAULT_CITY,
            "tts_engine": cls.TTS_ENGINE,
            "voice_name": cls.VOICE_NAME,
            "safe_mode": cls.SAFE_MODE,
        }

    @classmethod
    def update(cls, key: str, value: any):
        if hasattr(cls, key):
            setattr(cls, key, value)
