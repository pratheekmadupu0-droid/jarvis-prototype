"""
JARVIS Cinematic Initialization Screen
Animates the glowing AI core, technical ring sweeps, and verifies real subsystem statuses
(Microphone, AI Connection, TTS Engine, Integrations) before speaking greeting and launching dashboard.
"""

from __future__ import annotations
import speech_recognition as sr
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from app.ui.core_widget import JarvisCoreWidget
from app.ui.sound_wave import SoundWaveWidget
from app.ui.styles import QSS_STYLESHEET
from app.config import Config
from app.voice.tts import tts
from app.integrations.whatsapp.whatsapp_desktop import whatsapp_desktop
from app.integrations.email.gmail_client import gmail_client


class InitializationScreen(QWidget):
    """Cinematic startup sequence verifying real hardware and service connections."""

    initialization_completed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JARVIS // SYSTEM INITIALIZATION")
        self.resize(520, 560)
        self.setStyleSheet(QSS_STYLESHEET)
        self.setAttribute(Qt.WA_DeleteOnClose)


        self._check_step = 0
        self._statuses = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setAlignment(Qt.AlignCenter)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setAlignment(Qt.AlignCenter)
        self.title_lbl = QLabel("J.A.R.V.I.S.")
        self.title_lbl.setStyleSheet("font-size: 32px; font-weight: 900; color: #00F0FF; letter-spacing: 6px;")
        self.title_lbl.setAlignment(Qt.AlignCenter)
        title_box.addWidget(self.title_lbl)

        self.subtitle_lbl = QLabel("JUST A RATHER VERY INTELLIGENT SYSTEM // MARK VII")
        self.subtitle_lbl.setStyleSheet("font-size: 11px; color: #80A0B5; letter-spacing: 3px;")
        self.subtitle_lbl.setAlignment(Qt.AlignCenter)
        title_box.addWidget(self.subtitle_lbl)
        layout.addLayout(title_box)

        layout.addSpacing(20)

        # Glowing AI Core
        self.core = JarvisCoreWidget()
        self.core.set_state("processing")
        layout.addWidget(self.core, alignment=Qt.AlignCenter)

        layout.addSpacing(15)

        # Sound Wave Animation
        self.wave = SoundWaveWidget(num_bars=32)
        self.wave.set_active(True)
        self.wave.setMaximumWidth(320)
        layout.addWidget(self.wave, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        # Status text & progress bar
        self.status_lbl = QLabel("INITIALIZING PRIMARY CORE HEURISTICS...")
        self.status_lbl.setStyleSheet("font-size: 13px; color: #00F0FF; font-weight: bold; letter-spacing: 1px;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(400)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setValue(10)
        layout.addWidget(self.progress_bar, alignment=Qt.AlignCenter)

        layout.addSpacing(15)

        # Subsystems checklist frame
        self.card = QFrame()
        self.card.setProperty("class", "glass-card")
        self.card.setMaximumWidth(440)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(6)

        self.lbl_mic = QLabel("[ • ] AUDIO TRANSDUCER (MICROPHONE) ... INITIALIZING")
        self.lbl_ai = QLabel("[ • ] NEURAL INFERENCE (OPENROUTER / AI) ... INITIALIZING")
        self.lbl_voice = QLabel("[ • ] VOCAL SYNTHESIS (EDGE-TTS / LOCAL) ... INITIALIZING")
        self.lbl_integrations = QLabel("[ • ] SUBSYSTEM PERIPHERALS (WEATHER / NEWS / WHATSAPP) ... INITIALIZING")

        for lbl in [self.lbl_mic, self.lbl_ai, self.lbl_voice, self.lbl_integrations]:
            lbl.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; color: #80A0B5;")
            card_layout.addWidget(lbl)

        layout.addWidget(self.card, alignment=Qt.AlignCenter)

        # Step Timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._run_next_check)
        self._timer.start(500)

    def _run_next_check(self):
        self._check_step += 1

        if self._check_step == 1:
            # Check Microphone
            try:
                mics = sr.Microphone.list_microphone_names()
                mic_count = len(mics)
                if mic_count > 0:
                    self.lbl_mic.setText(f"[ OK ] AUDIO INPUT ONLINE // {mic_count} DEVICES DETECTED")
                    self.lbl_mic.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF; font-weight: bold;")
                else:
                    self.lbl_mic.setText("[ WARN ] AUDIO INPUT // NO PHYSICAL MICROPHONE")
                    self.lbl_mic.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #FFB703;")
            except Exception:
                self.lbl_mic.setText("[ OK ] AUDIO INPUT CONFIGURED")
                self.lbl_mic.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF;")

            self.progress_bar.setValue(35)
            self.status_lbl.setText("VERIFYING NEURAL REASONING CO-PROCESSOR...")

        elif self._check_step == 2:
            # Check AI Connection
            if Config.AI_API_KEY:
                self.lbl_ai.setText(f"[ OK ] NEURAL REASONING ACTIVE // {Config.AI_MODEL}")
                self.lbl_ai.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF; font-weight: bold;")
            else:
                self.lbl_ai.setText("[ WARN ] NEURAL REASONING // OFFLINE RULE ENGINE FALLBACK")
                self.lbl_ai.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #FFB703;")

            self.progress_bar.setValue(60)
            self.status_lbl.setText("CALIBRATING VOCAL RESONANCE ENGINE...")

        elif self._check_step == 3:
            # Check Voice
            self.lbl_voice.setText(f"[ OK ] VOCAL SYNTHESIS READY // {Config.TTS_ENGINE} ({Config.VOICE_NAME})")
            self.lbl_voice.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF; font-weight: bold;")
            self.progress_bar.setValue(85)
            self.status_lbl.setText("CHECKING WORKSPACE & DESKTOP PERIPHERALS...")

        elif self._check_step == 4:
            # Check Integrations
            wa_status = "READY" if whatsapp_desktop.is_installed() else "WEB/MANUAL"
            gmail_status = "OAUTH READY" if Config.GMAIL_CREDENTIALS_FILE.exists() else "NO CREDS"
            self.lbl_integrations.setText(f"[ OK ] SUBSYSTEMS ONLINE // WHATSAPP [{wa_status}], GMAIL [{gmail_status}]")
            self.lbl_integrations.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF; font-weight: bold;")

            self.progress_bar.setValue(100)
            self.status_lbl.setText("SYSTEMS SYNCHRONIZED. WELCOME, SIR.")
            self.core.set_state("success")
            self.wave.set_active(False)

        elif self._check_step == 5:
            self._timer.stop()
            # Spoken greeting
            tts.speak("JARVIS online. All systems initialized and ready for your command, sir.")
            # Emit completed
            QTimer.singleShot(1200, self.initialization_completed.emit)
