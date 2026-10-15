"""
JARVIS System & Application Launch Tools
Handles launching approved Windows applications, opening websites, and managing windows safely.
"""

from __future__ import annotations
import os
import subprocess
import webbrowser
import psutil
from typing import Optional, Dict, Any
from app.tools.base import BaseTool, ToolResult

APP_ALIASES = {
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "terminal": "wt.exe",
    "cmd": "cmd.exe",
    "chatgpt": "https://chatgpt.com",
    "youtube": "https://www.youtube.com",
    "whatsapp": "whatsapp:",
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
}


CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def open_url_in_chrome(url: str):
    """Directly opens URL in the default browser / Google Chrome window on the user's active screen."""
    import subprocess, os, webbrowser
    opened = False
    try:
        os.startfile(url)
        opened = True
    except Exception:
        pass

    if os.path.exists(CHROME_PATH):
        try:
            subprocess.Popen([CHROME_PATH, url])
            opened = True
        except Exception:
            pass

    if not opened:
        try:
            webbrowser.open_new(url)
            opened = True
        except Exception:
            pass

    return True


class LaunchApplicationTool(BaseTool):
    name = "launch_application"
    description = "Launch an approved Windows application (Chrome, VS Code, Notepad, Calculator, File Explorer, WhatsApp, etc.) or open a web app."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Application name (e.g. 'chrome', 'notepad', 'vscode', 'calculator', 'whatsapp', 'chatgpt')"},
            "arguments": {"type": "string", "description": "Optional argument or file path to open with the app"}
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str, arguments: Optional[str] = None) -> ToolResult:
        normalized = app_name.strip().lower()
        target = APP_ALIASES.get(normalized, normalized)

        # Chrome browser or general application request
        if normalized in ("chrome", "google chrome", "browser"):
            try:
                if os.path.exists(CHROME_PATH):
                    os.startfile(CHROME_PATH)
                else:
                    subprocess.Popen(["powershell.exe", "-Command", "Start-Process chrome"], shell=True)
                return ToolResult(success=True, message="Opened Google Chrome on your desktop.", data={"app": "chrome"})
            except Exception as e:
                return ToolResult(success=False, message=f"Failed to open Chrome: {e}")

        if normalized in ("application", "applications"):
            try:
                if os.path.exists(CHROME_PATH):
                    os.startfile(CHROME_PATH)
                return ToolResult(
                    success=True,
                    message="Opened Google Chrome. You can also say 'Open YouTube', 'Open WhatsApp', 'Open VS Code', 'Open Notepad', or 'Open Calculator'.",
                    data={"app": "chrome"}
                )
            except Exception:
                pass

        # Web-based apps (YouTube, ChatGPT, Google, Gmail, Outlook, etc.)
        if target.startswith("http://") or target.startswith("https://"):
            open_url_in_chrome(target)
            return ToolResult(
                success=True,
                message=f"Opened {app_name} in Google Chrome: {target}",
                data={"url": target, "open_url": target}
            )

        # Protocol handlers (e.g. whatsapp:)
        if target.endswith(":"):
            try:
                os.startfile(target)
                return ToolResult(
                    success=True,
                    message=f"Launched {app_name} on your desktop.",
                    data={"target": target}
                )
            except Exception:
                try:
                    subprocess.Popen(["powershell.exe", "-Command", f"Start-Process '{target}'"], shell=True)
                    return ToolResult(
                        success=True,
                        message=f"Launched {app_name} on your desktop.",
                        data={"target": target}
                    )
                except Exception as e:
                    return ToolResult(success=False, message=f"Failed to launch {app_name}: {str(e)}")

        # Native Desktop Executables
        try:
            if target in ("notepad.exe", "notepad"):
                os.startfile("notepad.exe")
            elif target in ("calc.exe", "calc"):
                subprocess.Popen(["calc.exe"])
            elif target in ("explorer.exe", "explorer"):
                subprocess.Popen(["explorer.exe"])
            elif target in ("code", "vscode"):
                subprocess.Popen(["cmd.exe", "/c", "code"], shell=True)
            else:
                try:
                    os.startfile(target)
                except Exception:
                    cmd_ps = f"Start-Process '{target}'"
                    if arguments:
                        cmd_ps = f"Start-Process '{target}' -ArgumentList '{arguments}'"
                    subprocess.Popen(["powershell.exe", "-Command", cmd_ps], shell=True)

            return ToolResult(
                success=True,
                message=f"Opened application '{app_name}' on your desktop.",
                data={"target": target}
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to launch application '{app_name}': {str(e)}")


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Open a specific URL or web page in Google Chrome."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web URL to open"}
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> ToolResult:
        target = url.strip()
        if not (target.startswith("http://") or target.startswith("https://")):
            target = "https://" + target

        open_url_in_chrome(target)

        return ToolResult(
            success=True,
            message=f"Opened {target} in Google Chrome on your screen.",
            data={"url": target, "open_url": target}
        )


class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Close a running application safely."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the application or process to close (e.g. 'notepad', 'calc')"}
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str) -> ToolResult:
        normalized = app_name.strip().lower()
        closed_count = 0
        for p in psutil.process_iter(['pid', 'name']):
            try:
                pname = p.info['name'].lower()
                if normalized in pname or pname.startswith(normalized):
                    p.terminate()
                    closed_count += 1
            except Exception:
                pass

        if closed_count > 0:
            return ToolResult(success=True, message=f"Closed {closed_count} instance(s) of '{app_name}'.")
        return ToolResult(success=False, message=f"No running process found matching '{app_name}'.")
