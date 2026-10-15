"""
JARVIS Futuristic HUD Stylesheet & Design System
Dark charcoal, holographic cyan, electric blue, and cyber accents.
"""

# Palette Constants
COLOR_BG_DARK = "#070B11"
COLOR_BG_PANEL = "#0D131D"
COLOR_BG_CARD = "#121A27"
COLOR_CYAN = "#00F0FF"
COLOR_BLUE = "#0077FF"
COLOR_AMBER = "#FFB703"
COLOR_RED = "#FF3366"
COLOR_TEXT = "#E0F7FA"
COLOR_TEXT_MUTED = "#80A0B5"

QSS_STYLESHEET = """
QMainWindow {
    background-color: #070B11;
    color: #E0F7FA;
    font-family: 'Segoe UI', 'Consolas', sans-serif;
}

QWidget {
    color: #E0F7FA;
    font-family: 'Segoe UI', 'Consolas', sans-serif;
}

QFrame.glass-panel {
    background-color: rgba(13, 19, 29, 0.85);
    border: 1px solid rgba(0, 240, 255, 0.25);
    border-radius: 12px;
}

QFrame.glass-card {
    background-color: rgba(18, 26, 39, 0.7);
    border: 1px solid rgba(0, 240, 255, 0.15);
    border-radius: 8px;
}

QLabel {
    color: #E0F7FA;
}

QLabel.title-label {
    font-size: 18px;
    font-weight: bold;
    color: #00F0FF;
    letter-spacing: 2px;
}

QLabel.subtitle-label {
    font-size: 11px;
    color: #80A0B5;
    letter-spacing: 1px;
}

QPushButton {
    background-color: rgba(0, 240, 255, 0.08);
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 6px;
    color: #00F0FF;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 16px;
}

QPushButton:hover {
    background-color: rgba(0, 240, 255, 0.2);
    border: 1px solid #00F0FF;
    box-shadow: 0 0 10px rgba(0, 240, 255, 0.5);
}

QPushButton:pressed {
    background-color: rgba(0, 240, 255, 0.35);
}

QPushButton.danger-btn {
    background-color: rgba(255, 51, 102, 0.15);
    border: 1px solid rgba(255, 51, 102, 0.5);
    color: #FF3366;
}

QPushButton.danger-btn:hover {
    background-color: rgba(255, 51, 102, 0.3);
    border: 1px solid #FF3366;
}

QPushButton.action-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077FF, stop:1 #00F0FF);
    color: #070B11;
    border: none;
    font-weight: bold;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: rgba(7, 11, 17, 0.9);
    border: 1px solid rgba(0, 240, 255, 0.3);
    border-radius: 6px;
    color: #E0F7FA;
    padding: 8px;
    font-size: 13px;
    selection-background-color: #00F0FF;
    selection-color: #070B11;
}

QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #00F0FF;
}

QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollBar:vertical {
    border: none;
    background: rgba(7, 11, 17, 0.5);
    width: 6px;
    margin: 0px;
    border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: rgba(0, 240, 255, 0.3);
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #00F0FF;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QProgressBar {
    border: 1px solid rgba(0, 240, 255, 0.3);
    border-radius: 4px;
    background-color: rgba(7, 11, 17, 0.8);
    text-align: center;
    color: #00F0FF;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077FF, stop:1 #00F0FF);
    border-radius: 3px;
}
"""
