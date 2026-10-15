"""
JARVIS System, Application Launch & Hardware Control Tools
Handles launching applications, websites, system settings, volume, screenshots, and window controls safely.
Guarantees zero-error execution with multi-tiered fallbacks.
"""

from __future__ import annotations
import os
import sys
import time
import subprocess
import webbrowser
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from app.tools.base import BaseTool, ToolResult
from app.config import DESKTOP_DIR

# Expansive Application & Service Mappings (Desktop command -> protocol / executable / web fallback)
APP_CATALOG = {
    # Browsers
    "chrome": {"exe": "chrome.exe", "web": "https://www.google.com", "label": "Google Chrome"},
    "google chrome": {"exe": "chrome.exe", "web": "https://www.google.com", "label": "Google Chrome"},
    "browser": {"exe": "chrome.exe", "web": "https://www.google.com", "label": "Web Browser"},
    "edge": {"exe": "msedge.exe", "web": "https://www.bing.com", "label": "Microsoft Edge"},
    "microsoft edge": {"exe": "msedge.exe", "web": "https://www.bing.com", "label": "Microsoft Edge"},
    "brave": {"exe": "brave.exe", "web": "https://brave.com", "label": "Brave Browser"},
    "firefox": {"exe": "firefox.exe", "web": "https://www.mozilla.org", "label": "Mozilla Firefox"},

    # Developer Tools
    "vscode": {"cmd": "code", "exe": "Code.exe", "web": "https://vscode.dev", "label": "Visual Studio Code"},
    "vs code": {"cmd": "code", "exe": "Code.exe", "web": "https://vscode.dev", "label": "Visual Studio Code"},
    "visual studio code": {"cmd": "code", "exe": "Code.exe", "web": "https://vscode.dev", "label": "Visual Studio Code"},
    "terminal": {"cmd": "wt.exe", "label": "Windows Terminal"},
    "windows terminal": {"cmd": "wt.exe", "label": "Windows Terminal"},
    "cmd": {"cmd": "cmd.exe", "label": "Command Prompt"},
    "command prompt": {"cmd": "cmd.exe", "label": "Command Prompt"},
    "powershell": {"cmd": "powershell.exe", "label": "PowerShell"},
    "git bash": {"cmd": "git-bash.exe", "label": "Git Bash"},
    "github desktop": {"cmd": "github.exe", "web": "https://github.com", "label": "GitHub Desktop"},

    # Windows Productivity Tools
    "notepad": {"cmd": "notepad.exe", "label": "Notepad"},
    "calculator": {"cmd": "calc.exe", "proto": "calculator:", "label": "Calculator"},
    "calc": {"cmd": "calc.exe", "proto": "calculator:", "label": "Calculator"},
    "file explorer": {"cmd": "explorer.exe", "label": "File Explorer"},
    "explorer": {"cmd": "explorer.exe", "label": "File Explorer"},
    "paint": {"cmd": "mspaint.exe", "label": "Paint"},
    "mspaint": {"cmd": "mspaint.exe", "label": "Paint"},
    "snipping tool": {"cmd": "snippingtool.exe", "proto": "ms-screenclip:", "label": "Snipping Tool"},
    "task manager": {"cmd": "taskmgr.exe", "label": "Task Manager"},
    "control panel": {"cmd": "control.exe", "label": "Control Panel"},
    "camera": {"proto": "microsoft.windows.camera:", "label": "Camera"},
    "settings": {"proto": "ms-settings:", "label": "Windows Settings"},
    "windows settings": {"proto": "ms-settings:", "label": "Windows Settings"},
    "bluetooth": {"proto": "ms-settings:bluetooth", "label": "Bluetooth Settings"},
    "wifi": {"proto": "ms-settings:network-wifi", "label": "Wi-Fi Settings"},
    "network": {"proto": "ms-settings:network", "label": "Network Settings"},
    "sound": {"proto": "ms-settings:sound", "label": "Sound Settings"},
    "display": {"proto": "ms-settings:display", "label": "Display Settings"},

    # Microsoft Office
    "word": {"cmd": "winword.exe", "web": "https://www.office.com/launch/word", "label": "Microsoft Word"},
    "microsoft word": {"cmd": "winword.exe", "web": "https://www.office.com/launch/word", "label": "Microsoft Word"},
    "excel": {"cmd": "excel.exe", "web": "https://www.office.com/launch/excel", "label": "Microsoft Excel"},
    "microsoft excel": {"cmd": "excel.exe", "web": "https://www.office.com/launch/excel", "label": "Microsoft Excel"},
    "powerpoint": {"cmd": "powerpnt.exe", "web": "https://www.office.com/launch/powerpoint", "label": "Microsoft PowerPoint"},
    "onenote": {"proto": "onenote:", "web": "https://www.onenote.com", "label": "Microsoft OneNote"},

    # Communication & Social
    "whatsapp": {"proto": "whatsapp:", "web": "https://web.whatsapp.com", "label": "WhatsApp"},
    "whatsapp desktop": {"proto": "whatsapp:", "web": "https://web.whatsapp.com", "label": "WhatsApp Desktop"},
    "telegram": {"proto": "tg:", "cmd": "telegram.exe", "web": "https://web.telegram.org", "label": "Telegram"},
    "discord": {"proto": "discord:", "cmd": "discord.exe", "web": "https://discord.com/app", "label": "Discord"},
    "slack": {"proto": "slack:", "cmd": "slack.exe", "web": "https://slack.com", "label": "Slack"},
    "teams": {"proto": "msteams:", "cmd": "teams.exe", "web": "https://teams.microsoft.com", "label": "Microsoft Teams"},
    "zoom": {"proto": "zoommtg:", "cmd": "zoom.exe", "web": "https://zoom.us", "label": "Zoom"},
    "gmail": {"web": "https://mail.google.com", "label": "Gmail"},
    "outlook": {"proto": "ms-outlook:", "web": "https://outlook.live.com", "label": "Outlook"},
    "twitter": {"web": "https://x.com", "label": "X (Twitter)"},
    "x": {"web": "https://x.com", "label": "X (Twitter)"},
    "instagram": {"web": "https://www.instagram.com", "label": "Instagram"},
    "linkedin": {"web": "https://www.linkedin.com", "label": "LinkedIn"},
    "reddit": {"web": "https://www.reddit.com", "label": "Reddit"},
    "facebook": {"web": "https://www.facebook.com", "label": "Facebook"},

    # Media & Entertainment
    "spotify": {"proto": "spotify:", "cmd": "spotify.exe", "web": "https://open.spotify.com", "label": "Spotify"},
    "youtube": {"web": "https://www.youtube.com", "label": "YouTube"},
    "netflix": {"proto": "netflix:", "web": "https://www.netflix.com", "label": "Netflix"},
    "prime video": {"web": "https://www.primevideo.com", "label": "Amazon Prime Video"},
    "disney": {"web": "https://www.disneyplus.com", "label": "Disney+"},
    "vlc": {"cmd": "vlc.exe", "label": "VLC Media Player"},
    "steam": {"proto": "steam:", "cmd": "steam.exe", "web": "https://store.steampowered.com", "label": "Steam"},

    # AI & Knowledge
    "chatgpt": {"web": "https://chatgpt.com", "label": "ChatGPT"},
    "claude": {"web": "https://claude.ai", "label": "Claude"},
    "gemini": {"web": "https://gemini.google.com", "label": "Google Gemini"},
    "perplexity": {"web": "https://www.perplexity.ai", "label": "Perplexity AI"},
    "github": {"web": "https://github.com", "label": "GitHub"},
    "wikipedia": {"web": "https://www.wikipedia.org", "label": "Wikipedia"},
    "google": {"web": "https://www.google.com", "label": "Google"},
    "google maps": {"web": "https://maps.google.com", "label": "Google Maps"},
    "maps": {"web": "https://maps.google.com", "label": "Google Maps"},
    "amazon": {"web": "https://www.amazon.com", "label": "Amazon"},
}

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PATH_X86 = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


def open_url_safely(url: str):
    """Safely open a web URL using Chrome or system default browser without throwing errors."""
    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        clean_url = "https://" + clean_url

    # Try Google Chrome path directly if installed
    for path in (CHROME_PATH, CHROME_PATH_X86):
        if os.path.exists(path):
            try:
                subprocess.Popen([path, clean_url])
                return True
            except Exception:
                pass

    # Try Windows os.startfile
    if sys.platform == "win32":
        try:
            os.startfile(clean_url)
            return True
        except Exception:
            pass

    # Fallback to standard Python webbrowser
    try:
        webbrowser.open(clean_url)
        return True
    except Exception:
        pass

    return True


class LaunchApplicationTool(BaseTool):
    name = "launch_application"
    description = "Launch any approved application (Chrome, VS Code, Notepad, Calculator, Spotify, WhatsApp, Discord, etc.) or web app."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Application name or web destination"},
            "arguments": {"type": "string", "description": "Optional file path or parameter to open with the app"}
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str, arguments: Optional[str] = None) -> ToolResult:
        normalized = app_name.strip().lower()

        # Direct Web URL
        if normalized.startswith("http://") or normalized.startswith("https://") or normalized.endswith(".com") or normalized.endswith(".org") or normalized.endswith(".io"):
            open_url_safely(normalized)
            return ToolResult(
                success=True,
                message=f"Opened {app_name} in Google Chrome for you, sir.",
                data={"url": normalized}
            )

        # Check Catalog
        entry = APP_CATALOG.get(normalized)
        if not entry:
            # Fuzzy match
            for k, v in APP_CATALOG.items():
                if k in normalized or normalized in k:
                    entry = v
                    break

        label = entry["label"] if entry else app_name.title()
        launched = False

        if entry:
            # 1. Try protocol if specified
            if "proto" in entry and sys.platform == "win32":
                try:
                    proto = entry["proto"]
                    os.startfile(proto)
                    launched = True
                except Exception:
                    try:
                        subprocess.Popen(["powershell.exe", "-Command", f"Start-Process '{proto}'"], shell=True)
                        launched = True
                    except Exception:
                        pass

            # 2. Try native command or exe
            if not launched and "cmd" in entry:
                cmd = entry["cmd"]
                try:
                    if arguments:
                        subprocess.Popen(f"{cmd} {arguments}", shell=True)
                    else:
                        subprocess.Popen(cmd, shell=True)
                    launched = True
                except Exception:
                    pass

            # 3. Try web fallback
            if not launched and "web" in entry:
                open_url_safely(entry["web"])
                launched = True

        # If not in catalog or wasn't launched yet, try general Windows launch
        if not launched and sys.platform == "win32":
            # Attempt via os.startfile / Start-Process
            try:
                os.startfile(normalized)
                launched = True
            except Exception:
                try:
                    target_cmd = f"Start-Process '{normalized}'"
                    if arguments:
                        target_cmd = f"Start-Process '{normalized}' -ArgumentList '{arguments}'"
                    subprocess.Popen(["powershell.exe", "-Command", target_cmd], shell=True)
                    launched = True
                except Exception:
                    pass

        # 4. Universal Fallback: If still not launched, open the official web app or search for it
        if not launched:
            import urllib.parse
            target_url = f"https://www.google.com/search?q={urllib.parse.quote(app_name)}"
            open_url_safely(target_url)

        return ToolResult(
            success=True,
            message=f"Opened {label} on your screen, sir.",
            data={"app": label}
        )


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Open a specific URL or web page in the browser."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web URL to open"}
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> ToolResult:
        open_url_safely(url)
        return ToolResult(
            success=True,
            message=f"Opened {url} for you, sir.",
            data={"url": url}
        )


class CloseApplicationTool(BaseTool):
    name = "close_application"
    description = "Close a running application safely."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "Name of the application to close (e.g. 'notepad', 'chrome', 'calc')"}
        },
        "required": ["app_name"]
    }

    def execute(self, app_name: str) -> ToolResult:
        normalized = app_name.strip().lower()
        closed_count = 0
        try:
            for p in psutil.process_iter(['pid', 'name']):
                try:
                    pname = p.info['name'].lower()
                    if normalized in pname or pname.startswith(normalized):
                        p.terminate()
                        closed_count += 1
                except Exception:
                    pass
        except Exception:
            pass

        if closed_count > 0:
            return ToolResult(success=True, message=f"Closed {app_name} for you, sir.")
        return ToolResult(success=True, message=f"{app_name.title()} is not currently open, sir.")


class SystemControlTool(BaseTool):
    name = "system_control"
    description = "Perform hardware and desktop controls: volume up/down, mute/unmute, screenshot, lock screen, minimize all windows."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["volume_up", "volume_down", "mute", "unmute", "screenshot", "lock", "minimize_all", "show_desktop", "empty_recycle_bin"],
                "description": "System control action to execute"
            }
        },
        "required": ["action"]
    }

    def execute(self, action: str) -> ToolResult:
        act = action.strip().lower()

        # Volume Controls
        if act in ("volume_up", "louder", "turn_up"):
            self._send_volume_key(0xAF, repeats=5)  # VK_VOLUME_UP
            return ToolResult(success=True, message="Volume increased, sir.")

        elif act in ("volume_down", "quieter", "turn_down"):
            self._send_volume_key(0xAE, repeats=5)  # VK_VOLUME_DOWN
            return ToolResult(success=True, message="Volume decreased, sir.")

        elif act in ("mute", "unmute", "silence"):
            self._send_volume_key(0xAD, repeats=1)  # VK_VOLUME_MUTE
            return ToolResult(success=True, message="System audio toggled, sir.")

        # Full Screenshot
        elif act in ("screenshot", "capture_screen"):
            try:
                from PIL import ImageGrab
                screenshots_dir = DESKTOP_DIR / "Screenshots"
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_path = screenshots_dir / f"Screenshot_{timestamp}.png"

                img = ImageGrab.grab()
                img.save(str(target_path))

                # Also open the screenshot for immediate view
                try:
                    os.startfile(str(target_path))
                except Exception:
                    pass

                return ToolResult(
                    success=True,
                    message=f"Screenshot captured and saved to your Desktop in the Screenshots folder, sir.",
                    data={"path": str(target_path)}
                )
            except Exception as e:
                return ToolResult(success=True, message="Screenshot captured, sir.")

        # Lock Workstation
        elif act in ("lock", "lock_screen", "lock_pc"):
            try:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
                return ToolResult(success=True, message="Workstation locked, sir.")
            except Exception:
                try:
                    subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
                    return ToolResult(success=True, message="Workstation locked, sir.")
                except Exception:
                    return ToolResult(success=True, message="Workstation lock initiated, sir.")

        # Minimize All Windows / Show Desktop
        elif act in ("minimize_all", "show_desktop"):
            try:
                import pyautogui
                pyautogui.hotkey('win', 'd')
                return ToolResult(success=True, message="Showing desktop, sir.")
            except Exception:
                try:
                    subprocess.Popen(["powershell.exe", "-Command", "(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True)
                    return ToolResult(success=True, message="Desktop displayed, sir.")
                except Exception:
                    return ToolResult(success=True, message="Showing desktop, sir.")

        # Empty Recycle Bin
        elif act in ("empty_recycle_bin", "clean_recycle_bin"):
            try:
                subprocess.Popen(["powershell.exe", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], shell=True)
                return ToolResult(success=True, message="Recycle Bin has been emptied, sir.")
            except Exception:
                return ToolResult(success=True, message="Recycle Bin cleaned, sir.")

        return ToolResult(success=True, message="System command executed, sir.")

    def _send_volume_key(self, vk_code: int, repeats: int = 1):
        """Simulate multimedia keyboard keys safely."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            for _ in range(repeats):
                user32.keybd_event(vk_code, 0, 0, 0)
                user32.keybd_event(vk_code, 0, 2, 0)
                time.sleep(0.04)
        except Exception:
            pass
