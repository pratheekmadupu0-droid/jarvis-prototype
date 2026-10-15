"""
JARVIS — Complete Personal AI Voice Assistant
Entry point for the application. Launches the cinematic initialization screen
and transitions to the futuristic HUD dashboard.
Also exports FastAPI 'app', 'application', and 'handler' variables for web and
serverless deployments (e.g. Vercel, Uvicorn, ASGI runners).
"""

from __future__ import annotations
import sys
import os
import warnings

# Suppress benign third-party library deprecation warnings from stderr
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Top-level ASGI / Web Application Export (for Vercel, Uvicorn, Serverless)
# ---------------------------------------------------------------------------
try:
    from app.web_server import app
    # Vercel recognizes 'app', 'application', or 'handler'
    application = app
    handler = app
except Exception as _err:
    app = None
    application = None
    handler = None


def main():
    """Launch the local PySide6 desktop GUI assistant."""
    # Ensure window is attached to the user's interactive desktop on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            h_desktop = user32.OpenDesktopW("Default", 0, False, 0x01FF)
            if h_desktop:
                user32.SetThreadDesktop(h_desktop)
        except Exception:
            pass

    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from app.ui.init_screen import InitializationScreen
        from app.ui.dashboard import JarvisDashboard
        from app.ui.styles import QSS_STYLESHEET
    except ImportError as e:
        print(f"[JARVIS] PySide6 desktop GUI library not available: {e}")
        print("[JARVIS] To launch the web interface instead, run: python -m uvicorn app.web_server:app --reload")
        return

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    qt_app = QApplication(sys.argv)

    qt_app.setApplicationName("JARVIS AI Assistant")
    qt_app.setStyleSheet(QSS_STYLESHEET)
    qt_app.setQuitOnLastWindowClosed(False)

    dashboard = JarvisDashboard()
    init_screen = InitializationScreen()

    def on_init_finished():
        dashboard.show()
        dashboard.raise_()
        dashboard.activateWindow()
        init_screen.close()
        qt_app.setQuitOnLastWindowClosed(True)

    init_screen.initialization_completed.connect(on_init_finished)
    init_screen.show()
    init_screen.raise_()
    init_screen.activateWindow()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
