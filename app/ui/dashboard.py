"""
JARVIS Futuristic HUD Dashboard
Central holographic AI Core, conversation cards, step-by-step execution tracker,
dedicated WhatsApp & Gmail interfaces, timers ticker, and voice controls.
"""

from __future__ import annotations
import threading
import time
import psutil
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QScrollArea, QFrame, QSplitter, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot

from app.ui.styles import QSS_STYLESHEET
from app.ui.core_widget import JarvisCoreWidget
from app.ui.sound_wave import SoundWaveWidget
from app.ui.confirmation_dialog import request_user_confirmation
from app.ui.settings_dialog import SettingsDialog
from app.config import Config
from app.voice.tts import tts
from app.voice.listener import voice_listener
from app.ai.planner import planner
from app.security.guardrails import SecurityGuardrails
from app.scheduler.timer_manager import timer_manager
from app.integrations.whatsapp.whatsapp_desktop import whatsapp_desktop
from app.integrations.email.gmail_client import gmail_client
from app.storage.database import db


class JarvisDashboard(QMainWindow):
    """Main futuristic desktop control interface."""

    sig_transcription = Signal(str)
    sig_core_state = Signal(str)
    sig_step_update = Signal(int, int, str, str)
    sig_plan_finished = Signal(dict)
    sig_reminder_triggered = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS // ARTIFICIAL INTELLIGENCE DASHBOARD")
        self.resize(1380, 880)
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(QSS_STYLESHEET)

        # Connect internal signals for thread-safety
        self.sig_transcription.connect(self._handle_transcription_gui)
        self.sig_core_state.connect(self._handle_core_state_gui)
        self.sig_step_update.connect(self._handle_step_update_gui)
        self.sig_plan_finished.connect(self._handle_plan_finished_gui)
        self.sig_reminder_triggered.connect(self._handle_reminder_triggered_gui)

        self._build_ui()
        self._setup_integrations()

        # System telemetry timer (CPU, RAM, Time)
        self._telemetry_timer = QTimer(self)
        self._telemetry_timer.timeout.connect(self._update_telemetry)
        self._telemetry_timer.start(1000)

    def _build_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # 1. Top HUD Status Bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # 2. Middle 3-Column Splitter
        middle_splitter = QSplitter(Qt.Horizontal)
        middle_splitter.setHandleWidth(2)

        # Left Column: Conversation History & Task Progress Tracker
        left_panel = self._create_left_panel()
        middle_splitter.addWidget(left_panel)

        # Center Column: AI Holographic Core, Audio Wave, Controls & Transcription
        center_panel = self._create_center_panel()
        middle_splitter.addWidget(center_panel)

        # Right Column: Subsystems (WhatsApp Desktop, Gmail, Reminders, Weather/News)
        right_panel = self._create_right_panel()
        middle_splitter.addWidget(right_panel)

        middle_splitter.setSizes([380, 560, 440])
        main_layout.addWidget(middle_splitter, 1)

        # 3. Bottom Command Input & Primary Controls Bar
        bottom_bar = self._create_bottom_bar()
        main_layout.addWidget(bottom_bar)

    def _create_top_bar(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "glass-panel")
        frame.setFixedHeight(50)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 4, 16, 4)

        # Logo / Title
        logo_lbl = QLabel("J.A.R.V.I.S.")
        logo_lbl.setStyleSheet("font-size: 16px; font-weight: 900; color: #00F0FF; letter-spacing: 3px;")
        layout.addWidget(logo_lbl)

        sub_lbl = QLabel("// MARK VII INTERFACE")
        sub_lbl.setStyleSheet("font-size: 10px; color: #80A0B5; letter-spacing: 1px;")
        layout.addWidget(sub_lbl)

        layout.addStretch()

        # Telemetry Labels
        self.lbl_cpu = QLabel("CPU: 0%")
        self.lbl_ram = QLabel("RAM: 0%")
        self.lbl_time = QLabel("00:00:00")
        self.lbl_status = QLabel("[ SYSTEM READY ]")

        for lbl in [self.lbl_cpu, self.lbl_ram, self.lbl_time, self.lbl_status]:
            lbl.setStyleSheet("font-family: 'Consolas'; font-size: 11px; color: #00F0FF; font-weight: 600;")
            layout.addWidget(lbl)
            layout.addSpacing(12)

        # Settings Button
        self.btn_settings = QPushButton("CONFIG")
        self.btn_settings.setFixedHeight(28)
        self.btn_settings.clicked.connect(self._open_settings)
        layout.addWidget(self.btn_settings)

        return frame

    def _create_left_panel(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "glass-panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        lbl = QLabel("CONVERSATION & TASK PIPELINE")
        lbl.setProperty("class", "subtitle-label")
        layout.addWidget(lbl)

        # Conversation History Scroll Area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(8)
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll, 2)

        # Step-by-Step Task Progress Card
        self.task_card = QFrame()
        self.task_card.setProperty("class", "glass-card")
        task_layout = QVBoxLayout(self.task_card)
        task_layout.setContentsMargins(12, 10, 12, 10)

        self.lbl_task_title = QLabel("CURRENT TASK: IDLE")
        self.lbl_task_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00F0FF;")
        task_layout.addWidget(self.lbl_task_title)

        self.task_progress_bar = QProgressBar()
        self.task_progress_bar.setFixedHeight(6)
        self.task_progress_bar.setValue(0)
        task_layout.addWidget(self.task_progress_bar)

        self.lbl_task_step = QLabel("Awaiting voice or keyboard instruction...")
        self.lbl_task_step.setStyleSheet("font-size: 11px; color: #80A0B5;")
        self.lbl_task_step.setWordWrap(True)
        task_layout.addWidget(self.lbl_task_step)

        layout.addWidget(self.task_card, 1)

        return frame

    def _create_center_panel(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "glass-panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)

        # Glowing AI Core
        self.core = JarvisCoreWidget()
        layout.addWidget(self.core, alignment=Qt.AlignCenter)

        layout.addSpacing(10)

        # Audio Frequency Wave
        self.wave = SoundWaveWidget(num_bars=36)
        self.wave.setMaximumWidth(380)
        layout.addWidget(self.wave, alignment=Qt.AlignCenter)

        layout.addSpacing(15)

        # Live Transcription Card
        trans_card = QFrame()
        trans_card.setProperty("class", "glass-card")
        trans_card.setMaximumWidth(480)
        trans_layout = QVBoxLayout(trans_card)
        trans_layout.setContentsMargins(14, 10, 14, 10)

        t_lbl = QLabel("LIVE TRANSCRIPTION")
        t_lbl.setProperty("class", "subtitle-label")
        trans_layout.addWidget(t_lbl)

        self.lbl_transcription = QLabel("\"JARVIS is standing by.\"")
        self.lbl_transcription.setStyleSheet("font-size: 14px; font-weight: 500; color: #E0F7FA; font-style: italic;")
        self.lbl_transcription.setWordWrap(True)
        trans_layout.addWidget(self.lbl_transcription)

        layout.addWidget(trans_card, alignment=Qt.AlignCenter)

        layout.addSpacing(15)

        # Controls Cluster
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Push to talk
        self.btn_ptt = QPushButton("PUSH TO TALK")
        self.btn_ptt.setProperty("class", "action-btn")
        self.btn_ptt.setFixedHeight(40)
        self.btn_ptt.clicked.connect(self._on_ptt_clicked)
        controls_layout.addWidget(self.btn_ptt)

        # Stop speech
        self.btn_stop_speech = QPushButton("STOP SPEAKING")
        self.btn_stop_speech.setFixedHeight(40)
        self.btn_stop_speech.clicked.connect(self._on_stop_speech_clicked)
        controls_layout.addWidget(self.btn_stop_speech)

        # Emergency stop
        self.btn_estop = QPushButton("EMERGENCY STOP")
        self.btn_estop.setProperty("class", "danger-btn")
        self.btn_estop.setFixedHeight(40)
        self.btn_estop.clicked.connect(self._on_emergency_stop_clicked)
        controls_layout.addWidget(self.btn_estop)

        layout.addLayout(controls_layout)

        return frame

    def _create_right_panel(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "glass-panel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. WhatsApp Desktop Card
        wa_card = QFrame()
        wa_card.setProperty("class", "glass-card")
        wa_layout = QVBoxLayout(wa_card)
        wa_layout.setContentsMargins(12, 10, 12, 10)
        wa_layout.setSpacing(6)

        wa_head = QHBoxLayout()
        wa_title = QLabel("WHATSAPP DESKTOP")
        wa_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00F0FF;")
        wa_head.addWidget(wa_title)
        wa_head.addStretch()

        self.btn_wa_open = QPushButton("OPEN APP")
        self.btn_wa_open.setFixedHeight(24)
        self.btn_wa_open.clicked.connect(lambda: whatsapp_desktop.open_whatsapp())
        wa_head.addWidget(self.btn_wa_open)
        wa_layout.addLayout(wa_head)

        self.lbl_wa_status = QLabel(f"Status: {'Active' if whatsapp_desktop.is_running() else 'Installed'}")
        self.lbl_wa_status.setStyleSheet("font-size: 10px; color: #80A0B5;")
        wa_layout.addWidget(self.lbl_wa_status)

        # WhatsApp draft preview
        self.lbl_wa_draft = QLabel("No pending messages.")
        self.lbl_wa_draft.setStyleSheet("font-size: 11px; color: #E0F7FA;")
        self.lbl_wa_draft.setWordWrap(True)
        wa_layout.addWidget(self.lbl_wa_draft)

        layout.addWidget(wa_card)

        # 2. Gmail Card
        gmail_card = QFrame()
        gmail_card.setProperty("class", "glass-card")
        gmail_layout = QVBoxLayout(gmail_card)
        gmail_layout.setContentsMargins(12, 10, 12, 10)
        gmail_layout.setSpacing(6)

        gm_head = QHBoxLayout()
        gm_title = QLabel("GMAIL SUBSYSTEM")
        gm_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00F0FF;")
        gm_head.addWidget(gm_title)
        gm_head.addStretch()

        btn_gm_check = QPushButton("CHECK UNREAD")
        btn_gm_check.setFixedHeight(24)
        btn_gm_check.clicked.connect(self._check_unread_emails)
        gm_head.addWidget(btn_gm_check)
        gmail_layout.addLayout(gm_head)

        self.lbl_gmail_status = QLabel("Authorized via OAuth" if gmail_client.is_authorized() else "Credentials ready")
        self.lbl_gmail_status.setStyleSheet("font-size: 10px; color: #80A0B5;")
        gmail_layout.addWidget(self.lbl_gmail_status)

        layout.addWidget(gmail_card)

        # 3. Active Timers & Reminders Card
        timer_card = QFrame()
        timer_card.setProperty("class", "glass-card")
        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(12, 10, 12, 10)

        t_title = QLabel("ACTIVE TIMERS & REMINDERS")
        t_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #00F0FF;")
        timer_layout.addWidget(t_title)

        self.lbl_timers = QLabel("No active timers.")
        self.lbl_timers.setStyleSheet("font-size: 11px; color: #80A0B5;")
        self.lbl_timers.setWordWrap(True)
        timer_layout.addWidget(self.lbl_timers)

        layout.addWidget(timer_card)

        # 4. Quick Actions (Weather / News)
        quick_card = QFrame()
        quick_card.setProperty("class", "glass-card")
        quick_layout = QHBoxLayout(quick_card)
        quick_layout.setContentsMargins(10, 8, 10, 8)

        btn_weather = QPushButton("WEATHER")
        btn_weather.clicked.connect(lambda: self._execute_text_command("What is the weather today?"))
        quick_layout.addWidget(btn_weather)

        btn_news = QPushButton("NEWS")
        btn_news.clicked.connect(lambda: self._execute_text_command("Give me the latest technology news."))
        quick_layout.addWidget(btn_news)

        btn_yt = QPushButton("YOUTUBE")
        btn_yt.clicked.connect(lambda: self._execute_text_command("Open YouTube"))
        quick_layout.addWidget(btn_yt)

        layout.addWidget(quick_card)

        layout.addStretch()
        return frame

    def _create_bottom_bar(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("class", "glass-panel")
        frame.setFixedHeight(64)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Enter command or speak 'Hey JARVIS'...")
        self.cmd_input.returnPressed.connect(self._on_enter_command)
        layout.addWidget(self.cmd_input, 1)

        btn_send = QPushButton("EXECUTE")
        btn_send.setProperty("class", "action-btn")
        btn_send.setFixedWidth(110)
        btn_send.clicked.connect(self._on_enter_command)
        layout.addWidget(btn_send)

        return frame

    def _setup_integrations(self):
        # Configure voice listener callbacks
        voice_listener.on_listening_state_changed = self._on_listener_state
        voice_listener.on_transcription_ready = self._on_transcription_from_worker
        voice_listener.on_wake_word_detected = lambda: self.sig_core_state.emit("listening")
        voice_listener.start()

        # Configure TTS callbacks
        def _on_tts_start():
            voice_listener.pause()
            self.sig_core_state.emit("speaking")

        def _on_tts_finish():
            voice_listener.resume()
            self.sig_core_state.emit("idle")

        tts.set_callbacks(
            on_start=_on_tts_start,
            on_finish=_on_tts_finish
        )


        # Configure planner callbacks
        planner.on_step_update = lambda s, t, d, st: self.sig_step_update.emit(s, t, d, st)
        planner.on_state_change = lambda st: self.sig_core_state.emit(st)

        # Configure scheduler callbacks
        timer_manager.on_reminder_triggered = lambda r: self.sig_reminder_triggered.emit(r)
        timer_manager.on_timer_tick = self._on_timer_tick_gui
        timer_manager.start()

    # --- GUI Update Handlers ---

    def _update_telemetry(self):
        self.lbl_cpu.setText(f"CPU: {int(psutil.cpu_percent())}%")
        self.lbl_ram.setText(f"RAM: {int(psutil.virtual_memory().percent)}%")
        self.lbl_time.setText(datetime.now().strftime("%H:%M:%S"))

    def _on_listener_state(self, state: str):
        self.sig_core_state.emit(state)

    def _on_transcription_from_worker(self, text: str):
        self.sig_transcription.emit(text)

    @Slot(str)
    def _handle_transcription_gui(self, text: str):
        self.lbl_transcription.setText(f"\"{text}\"")
        self._add_chat_bubble("USER", text)
        self._run_plan_async(text)

    @Slot(str)
    def _handle_core_state_gui(self, state: str):
        self.core.set_state(state)
        self.wave.set_active(state in ("listening", "speaking", "processing"))
        self.lbl_status.setText(f"[ {state.upper()} ]")

    @Slot(int, int, str, str)
    def _handle_step_update_gui(self, step_idx: int, total_steps: int, description: str, status: str):
        pct = int((step_idx / max(1, total_steps)) * 100)
        self.task_progress_bar.setValue(pct)
        self.lbl_task_title.setText(f"STEP {step_idx}/{total_steps}: {status.upper()}")
        self.lbl_task_step.setText(f"{description} ({status})")

    @Slot(dict)
    def _handle_plan_finished_gui(self, result: dict):
        resp = result.get("response", "")
        status = result.get("status", "")

        self._add_chat_bubble("JARVIS", resp)

        # Handle pending confirmation if required
        if result.get("requires_confirmation") and result.get("confirmation_info"):
            c_info = result["confirmation_info"]
            approved = request_user_confirmation(
                title=c_info.get("tool", "CONFIRMATION"),
                prompt=c_info.get("prompt", "Confirm action?"),
                details=json.dumps(c_info.get("payload", {}), indent=2),
                parent=self
            )
            if approved:
                if c_info.get("tool") == "whatsapp_draft_message":
                    succ, wa_res = whatsapp_desktop.send_confirmed_message()
                    tts.speak(wa_res)
                    self._add_chat_bubble("JARVIS", wa_res)
                elif c_info.get("tool") == "gmail_draft_email":
                    succ, gm_res = gmail_client.send_confirmed_email()
                    tts.speak(gm_res)
                    self._add_chat_bubble("JARVIS", gm_res)
            else:
                if c_info.get("tool") == "whatsapp_draft_message":
                    whatsapp_desktop.cancel_pending_message()
                elif c_info.get("tool") == "gmail_draft_email":
                    gmail_client.pending_email = None
                cancel_msg = "Operation cancelled per your request."
                tts.speak(cancel_msg)
                self._add_chat_bubble("JARVIS", cancel_msg)
        else:
            # Speak response
            tts.speak(resp)

    @Slot(dict)
    def _handle_reminder_triggered_gui(self, reminder: dict):
        title = reminder.get("title", "Timer")
        msg = f"Alert: Your reminder for '{title}' is due now."
        self._add_chat_bubble("JARVIS", msg)
        tts.speak(msg)
        QMessageBox.information(self, "JARVIS Alert", msg)

    def _on_timer_tick_gui(self, active_timers: list):
        if not active_timers:
            self.lbl_timers.setText("No active countdowns.")
            return
        lines = []
        for t in active_timers:
            rem = t.get("remaining", 0)
            m = rem // 60
            s = rem % 60
            lines.append(f"⏱ {t.get('title')}: {m:02d}:{s:02d}")
        self.lbl_timers.setText("\n".join(lines))

    # --- Actions ---

    def _on_enter_command(self):
        text = self.cmd_input.text().strip()
        if text:
            self.cmd_input.clear()
            self._execute_text_command(text)

    def _execute_text_command(self, text: str):
        self.lbl_transcription.setText(f"\"{text}\"")
        self._add_chat_bubble("USER", text)
        self._run_plan_async(text)

    def _run_plan_async(self, text: str):
        def worker():
            res = planner.plan_and_execute(text)
            self.sig_plan_finished.emit(res)
        threading.Thread(target=worker, daemon=True).start()

    def _on_ptt_clicked(self):
        voice_listener.trigger_push_to_talk()

    def _on_stop_speech_clicked(self):
        tts.stop()
        self.sig_core_state.emit("idle")

    def _on_emergency_stop_clicked(self):
        SecurityGuardrails.trigger_emergency_stop()
        tts.stop()
        self.sig_core_state.emit("error")
        self.lbl_task_title.setText("TASK: EMERGENCY STOPPED")
        self.lbl_task_step.setText("All ongoing computer actions and voice speech halted.")
        QMessageBox.warning(self, "Emergency Stop", "JARVIS operations have been halted immediately.")
        SecurityGuardrails.reset_emergency_stop()

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def _check_unread_emails(self):
        self._execute_text_command("Check my unread emails")

    def _add_chat_bubble(self, sender: str, message: str):
        bubble = QFrame()
        bubble.setProperty("class", "glass-card")
        layout = QVBoxLayout(bubble)
        layout.setContentsMargins(10, 8, 10, 8)

        is_user = sender == "USER"
        color = "#0077FF" if is_user else "#00F0FF"

        header = QLabel(f"[{sender}]")
        header.setStyleSheet(f"font-size: 10px; font-weight: bold; color: {color}; font-family: 'Consolas';")
        layout.addWidget(header)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("font-size: 12px; color: #E0F7FA;")
        msg_lbl.setWordWrap(True)
        layout.addWidget(msg_lbl)

        self.chat_layout.addWidget(bubble)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()
        ))
