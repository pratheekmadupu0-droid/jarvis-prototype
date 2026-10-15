"""
JARVIS — Complete Personal AI Voice Assistant
Entry point for the application. Launches the cinematic initialization screen
and transitions to the futuristic HUD dashboard.
"""

from __future__ import annotations
import sys
import os
import warnings

# Suppress benign third-party library deprecation warnings from stderr
warnings.filterwarnings("ignore")

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app.ui.init_screen import InitializationScreen
from app.ui.dashboard import JarvisDashboard
from app.ui.styles import QSS_STYLESHEET


def main():
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

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    app.setApplicationName("JARVIS AI Assistant")
    app.setStyleSheet(QSS_STYLESHEET)
    app.setQuitOnLastWindowClosed(False)

    dashboard = JarvisDashboard()
    init_screen = InitializationScreen()

    def on_init_finished():
        dashboard.show()
        dashboard.raise_()
        dashboard.activateWindow()
        init_screen.close()
        app.setQuitOnLastWindowClosed(True)

    init_screen.initialization_completed.connect(on_init_finished)
    init_screen.show()
    init_screen.raise_()
    init_screen.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
