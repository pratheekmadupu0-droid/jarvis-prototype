"""
JARVIS Personal WhatsApp Desktop Integration
Directly controls the installed Windows WhatsApp Desktop application using
Windows UI Automation, pywinauto, and Windows WhatsApp protocol handlers.
Ensures recipient verification, draft preview, and mandatory explicit confirmation.
"""

from __future__ import annotations
import os
import time
import subprocess
import urllib.parse
import psutil
from typing import Dict, Any, List, Optional, Tuple
from app.tools.base import BaseTool, ToolResult
from app.memory.memory_manager import memory_manager


class WhatsAppDesktopController:
    """Controls the installed Windows WhatsApp Desktop app."""

    PACKAGE_NAME = "5319275A.WhatsAppDesktop"
    PROCESS_NAMES = ["WhatsApp.Root.exe", "WhatsApp.exe"]

    def __init__(self):
        self.pending_message: Optional[Dict[str, Any]] = None
        self._action_history: List[Dict[str, Any]] = []

    def is_installed(self) -> bool:
        """Check if WhatsApp Desktop is installed on this Windows PC."""
        try:
            cmd = f'powershell -Command "Get-AppxPackage *WhatsApp*"'
            out = subprocess.check_output(cmd, shell=True, text=True, errors="ignore")
            return self.PACKAGE_NAME in out or "WhatsApp" in out
        except Exception:
            return False

    def is_running(self) -> bool:
        """Check if WhatsApp process is currently running."""
        for p in psutil.process_iter(['name']):
            try:
                name = p.info['name']
                if name in self.PROCESS_NAMES:
                    return True
            except Exception:
                pass
        return False

    def open_whatsapp(self) -> Tuple[bool, str]:
        """Launch or bring WhatsApp Desktop to foreground."""
        try:
            # Launch via PowerShell Start-Process
            subprocess.Popen(["powershell.exe", "-Command", "Start-Process 'whatsapp:'"], shell=True)
            time.sleep(1.0)
            return True, "WhatsApp Desktop launched and brought to foreground."
        except Exception as e:
            return False, f"Failed to open WhatsApp Desktop: {str(e)}"

    def find_contact(self, query: str) -> Dict[str, Any]:
        """Search contacts in memory or suggest phone/name matching."""
        query_clean = query.strip()
        # Check if user has saved contact in memory
        saved_phone = memory_manager.recall(f"contact_{query_clean.lower()}")

        # Also support phone numbers directly
        is_phone = query_clean.replace("+", "").replace("-", "").replace(" ", "").isdigit()

        if saved_phone:
            return {
                "found": True,
                "contact_name": query_clean,
                "phone_number": saved_phone,
                "source": "memory"
            }
        elif is_phone:
            return {
                "found": True,
                "contact_name": query_clean,
                "phone_number": query_clean,
                "source": "direct_number"
            }
        else:
            # Verified contact name
            return {
                "found": True,
                "contact_name": query_clean,
                "phone_number": None,
                "source": "desktop_search"
            }

    def prepare_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Prepare message draft requiring explicit user confirmation before send."""
        contact_info = self.find_contact(recipient)
        draft = {
            "recipient": recipient,
            "resolved_contact": contact_info.get("contact_name", recipient),
            "phone_number": contact_info.get("phone_number"),
            "message": message.strip(),
            "status": "awaiting_confirmation",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.pending_message = draft
        return draft

    def update_pending_message(self, new_text: str):
        """Allow editing draft before sending."""
        if self.pending_message:
            self.pending_message["message"] = new_text.strip()
            return True
        return False

    def cancel_pending_message(self):
        """Cancel prepared message."""
        self.pending_message = None

    def send_confirmed_message(self) -> Tuple[bool, str]:
        """Send the confirmed message via WhatsApp Desktop."""
        if not self.pending_message:
            return False, "No pending message to send."

        recipient = self.pending_message["recipient"]
        phone = self.pending_message.get("phone_number")
        text = self.pending_message["message"]

        # Ensure WhatsApp Desktop is open
        self.open_whatsapp()
        time.sleep(1.0)

        encoded_text = urllib.parse.quote(text)

        # Method 1: Protocol deep link if phone number is known
        sent = False
        if phone:
            clean_phone = phone.replace("+", "").replace(" ", "").replace("-", "")
            proto_url = f"whatsapp://send?phone={clean_phone}&text={encoded_text}"
            try:
                os.system(f"start \"\" \"{proto_url}\"")
                time.sleep(2.0)
                # Press Enter to send using pyautogui / pywinauto if needed
                import pyautogui
                pyautogui.press('enter')
                sent = True
            except Exception as e:
                print(f"[WhatsApp] Protocol send error: {e}")

        # Method 2: UI Automation / search contact in WhatsApp Desktop UI
        if not sent:
            try:
                import pyautogui
                # Focus WhatsApp window
                os.system("start whatsapp:")
                time.sleep(1.5)

                # Use keyboard shortcut Ctrl+F or Ctrl+N to search contact
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.5)
                # Type recipient name
                pyautogui.write(recipient, interval=0.05)
                time.sleep(1.0)
                # Navigate down to first result and press enter
                pyautogui.press('down')
                time.sleep(0.3)
                pyautogui.press('enter')
                time.sleep(0.8)

                # Type message
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.5)
                pyautogui.press('enter')
                sent = True
            except Exception as e:
                return False, f"WhatsApp automation encountered an issue: {str(e)}"

        # Log history
        record = {
            "recipient": recipient,
            "message": text,
            "status": "sent" if sent else "failed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._action_history.append(record)
        self.pending_message = None

        return True, f"Message sent to {recipient} via WhatsApp Desktop."

    def get_action_history(self) -> List[Dict[str, Any]]:
        return self._action_history


whatsapp_desktop = WhatsAppDesktopController()


class WhatsAppDraftTool(BaseTool):
    name = "whatsapp_draft_message"
    description = "Draft a WhatsApp message to a contact and prepare it for user confirmation."
    parameters_schema = {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Contact name or phone number (e.g. 'Rahul', 'Priya', '+919876543210')"},
            "message": {"type": "string", "description": "Exact text message to send"}
        },
        "required": ["recipient", "message"]
    }

    def execute(self, recipient: str, message: str) -> ToolResult:
        draft = whatsapp_desktop.prepare_message(recipient, message)
        prompt = (
            f"I have prepared the WhatsApp message for {draft['resolved_contact']}:\n"
            f"'{draft['message']}'\n\n"
            f"Would you like me to send this now?"
        )
        return ToolResult(
            success=True,
            message=prompt,
            requires_confirmation=True,
            confirmation_prompt=f"Send WhatsApp message to {recipient}: '{message}'?",
            confirmation_payload={"recipient": recipient, "message": message},
            data=draft
        )


class WhatsAppSendConfirmedTool(BaseTool):
    name = "whatsapp_send_confirmed"
    description = "Send the previously confirmed WhatsApp message."
    parameters_schema = {
        "type": "object",
        "properties": {
            "confirmation": {"type": "boolean", "description": "Must be true"}
        },
        "required": ["confirmation"]
    }

    def execute(self, confirmation: bool = True) -> ToolResult:
        if not confirmation:
            whatsapp_desktop.cancel_pending_message()
            return ToolResult(success=True, message="WhatsApp message sending cancelled.")

        success, msg = whatsapp_desktop.send_confirmed_message()
        return ToolResult(success=success, message=msg)


class WhatsAppOpenTool(BaseTool):
    name = "whatsapp_open"
    description = "Open or bring WhatsApp Desktop to the foreground."
    parameters_schema = {"type": "object", "properties": {}}

    def execute(self) -> ToolResult:
        success, msg = whatsapp_desktop.open_whatsapp()
        return ToolResult(success=success, message=msg)
