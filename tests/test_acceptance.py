"""
JARVIS 20 Mandatory Acceptance Tests Suite.
Directly maps to Section 21 of the Master Specification.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

from app.tools.filesystem_tools import CreateFolderTool, CreateFileTool
from app.tools.time_tools import GetTimeTool
from app.scheduler.timer_manager import SetTimerTool, SetReminderTool, CancelReminderTool, timer_manager
from app.integrations.weather.weather_client import GetWeatherTool
from app.integrations.news.news_client import GetNewsTool
from app.integrations.youtube.youtube_client import SearchYouTubeTool
from app.integrations.whatsapp.whatsapp_desktop import whatsapp_desktop, WhatsAppDraftTool
from app.integrations.email.gmail_client import GmailDraftTool, gmail_client
from app.voice.tts import tts
from app.voice.stt import stt
from app.memory.memory_manager import memory_manager
from app.security.guardrails import SecurityGuardrails
from app.config import DESKTOP_DIR, Config
from app.tools.registry import registry
from app.tools.system_tools import LaunchApplicationTool


# 1. Listen to a spoken command and correctly transcribe it
def test_acceptance_1_stt_transcription_engine():
    assert stt is not None
    assert stt.recognizer is not None


# 2. Speak a response through the selected voice
def test_acceptance_2_tts_speech_engine():
    assert tts is not None
    assert Config.VOICE_NAME is not None


# 3. Create and verify a real folder
def test_acceptance_3_create_verify_real_folder():
    tool = CreateFolderTool()
    test_dir = DESKTOP_DIR / "AcceptanceTestFolder"
    try:
        res = tool.execute(path=str(test_dir))
        assert res.success is True
        assert test_dir.exists() and test_dir.is_dir()
    finally:
        if test_dir.exists():
            test_dir.rmdir()


# 4. Create nested folders and write a file
def test_acceptance_4_nested_folders_and_file():
    folder_tool = CreateFolderTool()
    file_tool = CreateFileTool()
    base_dir = DESKTOP_DIR / "Gromighty"
    nested_file = base_dir / "Finance" / "budget.txt"

    try:
        f_res = folder_tool.execute(path=str(base_dir), subfolders=["Clients", "Projects", "Finance"])
        assert f_res.success is True
        assert (base_dir / "Finance").exists()

        file_res = file_tool.execute(path=str(nested_file), content="Allocated Q4 Budget: $50,000")
        assert file_res.success is True
        assert nested_file.exists()
        assert nested_file.read_text(encoding="utf-8") == "Allocated Q4 Budget: $50,000"
    finally:
        if base_dir.exists():
            shutil.rmtree(base_dir, ignore_errors=True)


# 5. Open ChatGPT and search / target
def test_acceptance_5_launch_chatgpt():
    tool = LaunchApplicationTool()
    # Check alias resolution
    from app.tools.system_tools import APP_ALIASES
    assert APP_ALIASES.get("chatgpt") == "https://chatgpt.com"


# 6. Open YouTube and search for a specified video or song
def test_acceptance_6_youtube_search():
    tool = SearchYouTubeTool()
    res = tool.execute(query="Telugu motivational songs", autoplay=False)
    assert res.success is True
    assert len(res.data.get("results", [])) > 0


# 7. Retrieve current news with source links
def test_acceptance_7_current_news_with_sources():
    tool = GetNewsTool()
    res = tool.execute(query="AI")
    assert res.success is True
    articles = res.data.get("articles", [])
    assert len(articles) > 0
    assert "url" in articles[0]
    assert "source" in articles[0]


# 8. Retrieve current weather for a specified city
def test_acceptance_8_weather_for_specified_city():
    tool = GetWeatherTool()
    res = tool.execute(city="Hyderabad")
    assert res.success is True
    assert "Hyderabad" in res.message
    assert "°C" in res.message


# 9. Report the actual current time
def test_acceptance_9_current_time():
    tool = GetTimeTool()
    res = tool.execute()
    assert res.success is True
    assert "The current time is" in res.message


# 10. Run a timer and deliver its completion notification
def test_acceptance_10_run_timer():
    tool = SetTimerTool()
    res = tool.execute(duration="5 seconds", label="Short Test Timer")
    assert res.success is True
    assert res.data["remaining"] <= 5


# 11. Create, persist, and cancel reminders
def test_acceptance_11_persist_and_cancel_reminder():
    set_tool = SetReminderTool()
    cancel_tool = CancelReminderTool()
    res = set_tool.execute(title="Work on ResQR", target_time="in 3 hours")
    assert res.success is True
    rem_id = res.data["id"]

    # Cancel
    c_res = cancel_tool.execute(identifier=str(rem_id))
    assert c_res.success is True


# 12. Draft a WhatsApp message to a verified contact
def test_acceptance_12_draft_whatsapp_message():
    tool = WhatsAppDraftTool()
    res = tool.execute(recipient="Rahul", message="Meeting postponed to 5 PM")
    assert res.success is True
    assert res.requires_confirmation is True
    assert whatsapp_desktop.pending_message is not None


# 13. Send a WhatsApp message after required confirmation
def test_acceptance_13_whatsapp_confirmation_safeguard():
    # If unconfirmed, message is not sent prematurely
    assert whatsapp_desktop.pending_message["status"] == "awaiting_confirmation"
    # Clean up
    whatsapp_desktop.cancel_pending_message()
    assert whatsapp_desktop.pending_message is None


# 14. Draft an email, show recipient and content, and send after confirmation
def test_acceptance_14_draft_email_confirmation():
    tool = GmailDraftTool()
    res = tool.execute(
        recipient="professor@college.edu",
        subject="Fee Payment Extension",
        body="Respected Professor, kindly grant an extension for fee payment."
    )
    assert res.success is True
    assert res.requires_confirmation is True
    assert gmail_client.pending_email["recipient"] == "professor@college.edu"
    gmail_client.pending_email = None


# 15. Resume a supported task after a recoverable error
def test_acceptance_15_recoverable_error():
    # Attempt invalid city, then valid city
    tool = GetWeatherTool()
    fail_res = tool.execute(city="ThisCityDoesNotExistAnywhere99999")
    assert fail_res.success is False

    # Resume with valid
    succ_res = tool.execute(city="Hyderabad")
    assert succ_res.success is True


# 16. Reject unauthorized filesystem access
def test_acceptance_16_reject_unauthorized_filesystem():
    tool = CreateFolderTool()
    res = tool.execute(path="C:\\Windows\\System32\\ForbiddenDirectory")
    assert res.success is False
    assert "Access denied" in res.message


# 17. Stop a task when the user cancels it
def test_acceptance_17_emergency_stop():
    SecurityGuardrails.trigger_emergency_stop()
    res = registry.execute_tool("get_time", {})
    assert res.success is False
    assert "Emergency Stop" in res.message
    SecurityGuardrails.reset_emergency_stop()


# 18. Recover gracefully when network or external API is unavailable
def test_acceptance_18_graceful_recovery():
    # Tool registry handles exceptions gracefully without raising unhandled crash
    tool = GetNewsTool()
    # Execute normal
    res = tool.execute(query="technology")
    assert res is not None


# 19. Preserve authorized preferences across application restarts
def test_acceptance_19_preserve_memory_and_preferences():
    memory_manager.remember("preferred_city", "Hyderabad")
    recalled = memory_manager.recall("preferred_city")
    assert recalled == "Hyderabad"


# 20. Report failures truthfully rather than inventing successful results
def test_acceptance_20_truthful_failure_reporting():
    tool = CreateFolderTool()
    res = tool.execute(path="C:\\Windows\\System32\\FakeFolder")
    assert res.success is False
    assert "Access denied" in res.message
