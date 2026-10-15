"""
Tests for WhatsApp Desktop Integration.
Verifies contact matching, draft preparation, confirmation requirement, and cancel safety.
"""

from app.integrations.whatsapp.whatsapp_desktop import (
    whatsapp_desktop, WhatsAppDraftTool, WhatsAppSendConfirmedTool
)
from app.memory.memory_manager import memory_manager


def test_whatsapp_installed_check():
    # We verified WhatsApp Desktop is installed on this PC
    assert whatsapp_desktop.is_installed() is True


def test_whatsapp_contact_find():
    memory_manager.remember("contact_rahul", "+919876543210")
    info = whatsapp_desktop.find_contact("Rahul")
    assert info["found"] is True
    assert info["phone_number"] == "+919876543210"


def test_whatsapp_draft_requires_confirmation():
    tool = WhatsAppDraftTool()
    res = tool.execute(recipient="Rahul", message="I will reach in ten minutes.")

    # Must require explicit confirmation
    assert res.success is True
    assert res.requires_confirmation is True
    assert "Rahul" in res.confirmation_prompt
    assert whatsapp_desktop.pending_message is not None
    assert whatsapp_desktop.pending_message["message"] == "I will reach in ten minutes."

    # Test editing draft
    whatsapp_desktop.update_pending_message("I will reach in fifteen minutes.")
    assert whatsapp_desktop.pending_message["message"] == "I will reach in fifteen minutes."

    # Test canceling draft
    whatsapp_desktop.cancel_pending_message()
    assert whatsapp_desktop.pending_message is None
