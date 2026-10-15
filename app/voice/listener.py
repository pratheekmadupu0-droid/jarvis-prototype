"""
JARVIS Continuous Audio Listener & Wake Word Detector
Runs a resilient background thread that listens for speech, detects the wake word
(e.g. 'JARVIS' or 'Hey JARVIS'), or handles explicit Push-to-Talk commands.
"""

from __future__ import annotations
import threading
import time
import speech_recognition as sr
from typing import Callable, Optional
from app.config import Config
from app.voice.stt import stt


class VoiceListener:
    """Manages continuous background voice monitoring and wake-word trigger."""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._paused = False
        self.wake_word = Config.WAKE_WORD.lower()

        # Callbacks
        self.on_wake_word_detected: Optional[Callable[[], None]] = None
        self.on_transcription_ready: Optional[Callable[[str], None]] = None
        self.on_listening_state_changed: Optional[Callable[[str], None]] = None  # 'idle', 'listening', 'processing'
        self.on_error: Optional[Callable[[str], None]] = None

    def start(self):
        """Start background listener thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop background listener thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def pause(self):
        """Temporarily pause listening (e.g. while JARVIS is speaking)."""
        self._paused = True

    def resume(self):
        """Resume listening."""
        self._paused = False

    def trigger_push_to_talk(self):
        """Invoked by Push-to-Talk button in GUI."""
        threading.Thread(target=self._run_single_capture, daemon=True).start()

    def _run_single_capture(self):
        if self.on_listening_state_changed:
            self.on_listening_state_changed("listening")

        success, text = stt.listen_once(timeout=6.0, phrase_time_limit=12.0)

        if self.on_listening_state_changed:
            self.on_listening_state_changed("processing")

        if success and text:
            # Strip wake word if spoken
            clean = text
            if clean.lower().startswith(self.wake_word):
                clean = clean[len(self.wake_word):].strip(" ,.:;!?")
            if not clean:
                clean = text
            if self.on_transcription_ready:
                self.on_transcription_ready(clean)
        else:
            if self.on_error and "timed out" not in text.lower():
                self.on_error(text)

        if self.on_listening_state_changed:
            self.on_listening_state_changed("idle")

    def _listen_loop(self):
        """Resilient continuous listening loop."""
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8

        while self._running:
            if self._paused:
                time.sleep(0.2)
                continue

            try:
                mic = sr.Microphone()
                with mic as source:
                    try:
                        recognizer.adjust_for_ambient_noise(source, duration=0.4)
                    except Exception:
                        pass

                    while self._running:
                        if self._paused:
                            time.sleep(0.2)
                            continue

                        if self.on_listening_state_changed:
                            self.on_listening_state_changed("listening")

                        try:
                            audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=8.0)
                        except sr.WaitTimeoutError:
                            if self.on_listening_state_changed:
                                self.on_listening_state_changed("idle")
                            continue

                        if self._paused or not self._running:
                            continue

                        if self.on_listening_state_changed:
                            self.on_listening_state_changed("processing")

                        success, phrase = stt.transcribe_audio(audio)
                        if success and phrase:
                            lowered = phrase.lower()
                            # Check wake word
                            if self.wake_word in lowered:
                                if self.on_wake_word_detected:
                                    self.on_wake_word_detected()

                                # Extract command part after wake word
                                idx = lowered.find(self.wake_word)
                                command = phrase[idx + len(self.wake_word):].strip(" ,.:;!?")

                                if command:
                                    if self.on_transcription_ready:
                                        self.on_transcription_ready(command)
                                else:
                                    # Wake word alone was said
                                    if self.on_transcription_ready:
                                        self.on_transcription_ready("Hey JARVIS")
                            else:
                                # If continuous mode without strict wake word, or already in active dialog
                                pass

                        if self.on_listening_state_changed:
                            self.on_listening_state_changed("idle")

            except Exception as e:
                if self.on_listening_state_changed:
                    self.on_listening_state_changed("idle")
                time.sleep(1.0)



voice_listener = VoiceListener()
