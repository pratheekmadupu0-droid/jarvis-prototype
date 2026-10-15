"""
JARVIS System Settings & Configuration Dialog
Allows real-time customization of AI model, voice engine, default city,
OAuth authorization, and memory management.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QCheckBox, QTabWidget, QWidget, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from app.config import Config
from app.storage.database import db
from app.memory.memory_manager import memory_manager
from app.integrations.email.gmail_client import gmail_client
from app.integrations.whatsapp.whatsapp_desktop import whatsapp_desktop
from app.ui.styles import QSS_STYLESHEET


class SettingsDialog(QDialog):
    """Futuristic settings configurator."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JARVIS // SYSTEM CONFIGURATION")
        self.resize(600, 480)
        self.setStyleSheet(QSS_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._create_ai_tab(), "AI REASONING")
        self.tabs.addTab(self._create_voice_tab(), "VOICE & SPEECH")
        self.tabs.addTab(self._create_integrations_tab(), "INTEGRATIONS")
        self.tabs.addTab(self._create_memory_tab(), "MEMORY")

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("SAVE CHANGES")
        self.btn_save.setProperty("class", "action-btn")
        self.btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _create_ai_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel("AI Model Provider Base URL:"))
        self.edit_base_url = QLineEdit(Config.AI_BASE_URL)
        l.addWidget(self.edit_base_url)

        l.addWidget(QLabel("AI Model Name:"))
        self.edit_model = QLineEdit(Config.AI_MODEL)
        l.addWidget(self.edit_model)

        l.addWidget(QLabel("AI API Key (OpenRouter or OpenAI):"))
        self.edit_api_key = QLineEdit(Config.AI_API_KEY)
        self.edit_api_key.setEchoMode(QLineEdit.Password)
        l.addWidget(self.edit_api_key)

        self.chk_safe_mode = QCheckBox("Safe Mode (Require Confirmation for Messages & Deletions)")
        self.chk_safe_mode.setChecked(Config.SAFE_MODE)
        l.addWidget(self.chk_safe_mode)

        l.addStretch()
        return w

    def _create_voice_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel("TTS Speech Engine:"))
        self.combo_tts = QComboBox()
        self.combo_tts.addItems(["edge-tts", "pyttsx3"])
        self.combo_tts.setCurrentText(Config.TTS_ENGINE)
        l.addWidget(self.combo_tts)

        l.addWidget(QLabel("Voice Name:"))
        self.edit_voice = QLineEdit(Config.VOICE_NAME)
        l.addWidget(self.edit_voice)

        l.addWidget(QLabel("Voice Rate (e.g. +0%, +10%, -10%):"))
        self.edit_rate = QLineEdit(Config.VOICE_RATE)
        l.addWidget(self.edit_rate)

        l.addWidget(QLabel("Wake Word:"))
        self.edit_wake_word = QLineEdit(Config.WAKE_WORD)
        l.addWidget(self.edit_wake_word)

        l.addStretch()
        return w

    def _create_integrations_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel("Default City for Weather:"))
        self.edit_city = QLineEdit(Config.DEFAULT_CITY)
        l.addWidget(self.edit_city)

        l.addWidget(QLabel("Gmail Integration:"))
        btn_gmail_auth = QPushButton("AUTHORIZE GMAIL (OAUTH)")
        btn_gmail_auth.clicked.connect(self._authorize_gmail)
        l.addWidget(btn_gmail_auth)

        l.addWidget(QLabel("WhatsApp Desktop Status:"))
        wa_status = "INSTALLED" if whatsapp_desktop.is_installed() else "NOT DETECTED"
        lbl_wa = QLabel(f"WhatsApp Desktop Application: {wa_status}")
        lbl_wa.setStyleSheet("color: #00F0FF; font-weight: bold;")
        l.addWidget(lbl_wa)

        l.addStretch()
        return w

    def _create_memory_tab(self) -> QWidget:
        w = QWidget()
        l = QVBoxLayout(w)

        l.addWidget(QLabel("Stored User Memory & Preferences:"))
        self.memory_view = QTextEdit()
        self.memory_view.setReadOnly(True)
        self._refresh_memory_view()
        l.addWidget(self.memory_view)

        btn_clear = QPushButton("CLEAR ALL USER MEMORY")
        btn_clear.setProperty("class", "danger-btn")
        btn_clear.clicked.connect(self._clear_memory)
        l.addWidget(btn_clear)

        return w

    def _refresh_memory_view(self):
        items = memory_manager.get_all()
        if not items:
            self.memory_view.setPlainText("No memories currently stored.")
            return
        lines = [f"• {m['key']} = {m['value']} ({m['category']})" for m in items]
        self.memory_view.setPlainText("\n".join(lines))

    def _clear_memory(self):
        for m in memory_manager.get_all():
            memory_manager.forget(m["key"])
        self._refresh_memory_view()
        QMessageBox.information(self, "Memory", "All stored memories cleared.")

    def _authorize_gmail(self):
        success = gmail_client.authenticate(interactive=True)
        if success:
            QMessageBox.information(self, "Gmail", "Gmail successfully authorized via OAuth!")
        else:
            QMessageBox.warning(self, "Gmail", "Gmail authorization incomplete or cancelled.")

    def _save_settings(self):
        Config.AI_BASE_URL = self.edit_base_url.text().strip()
        Config.AI_MODEL = self.edit_model.text().strip()
        Config.AI_API_KEY = self.edit_api_key.text().strip()
        Config.SAFE_MODE = self.chk_safe_mode.isChecked()

        Config.TTS_ENGINE = self.combo_tts.currentText()
        Config.VOICE_NAME = self.edit_voice.text().strip()
        Config.VOICE_RATE = self.edit_rate.text().strip()
        Config.WAKE_WORD = self.edit_wake_word.text().strip().lower()

        Config.DEFAULT_CITY = self.edit_city.text().strip()
        memory_manager.remember("preferred_city", Config.DEFAULT_CITY)

        # Save to DB
        db.set_setting("ai_model", Config.AI_MODEL)
        db.set_setting("voice_name", Config.VOICE_NAME)
        db.set_setting("default_city", Config.DEFAULT_CITY)

        self.accept()
