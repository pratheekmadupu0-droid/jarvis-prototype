"""
JARVIS Text-to-Speech Engine
Supports Edge TTS (online neural voice) with seamless fallback to pyttsx3 (local Windows SAPI5 voice).
Provides asynchronous queue playback, stop interruption, and configurable speed/voice.
"""

from __future__ import annotations
import asyncio
import os
import tempfile
import threading
import queue
import time
from typing import Optional, Callable

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import pygame
except ImportError:
    pygame = None

from app.config import Config


class TTSEngine:
    """Manages audio speech synthesis and output."""

    def __init__(self):
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._is_speaking = False
        self._on_start_callback: Optional[Callable[[], None]] = None
        self._on_finish_callback: Optional[Callable[[], None]] = None

        # Initialize Pygame mixer for edge-tts audio files
        if pygame:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as e:
                print(f"[TTS] Pygame mixer init note: {e}")

        # Initialize pyttsx3 local fallback engine
        self._pyttsx3_engine = None
        if pyttsx3:
            try:
                self._pyttsx3_engine = pyttsx3.init()
                self._pyttsx3_engine.setProperty('rate', 185)
                self._pyttsx3_engine.setProperty('volume', 1.0)
            except Exception as e:
                print(f"[TTS] pyttsx3 init note: {e}")

        # Background worker thread for speech
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._worker_thread.start()

    def set_callbacks(self, on_start: Optional[Callable[[], None]] = None, on_finish: Optional[Callable[[], None]] = None):
        self._on_start_callback = on_start
        self._on_finish_callback = on_finish

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def speak(self, text: str, block: bool = False):
        """Queue text to be spoken."""
        if not text or not text.strip():
            return
        clean_text = text.strip()
        if block:
            self._speak_direct(clean_text)
        else:
            self._queue.put(clean_text)

    def stop(self):
        """Immediately interrupt and stop any ongoing speech."""
        self._stop_event.set()
        # Empty queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

        # Stop pygame playback
        try:
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass

        # Stop pyttsx3
        if self._pyttsx3_engine:
            try:
                self._pyttsx3_engine.stop()
            except Exception:
                pass

        self._is_speaking = False
        if self._on_finish_callback:
            try:
                self._on_finish_callback()
            except Exception:
                pass

    def _speech_worker(self):
        """Worker thread processing the speech queue."""
        while True:
            text = self._queue.get()
            self._stop_event.clear()
            self._speak_direct(text)
            self._queue.task_done()

    def _speak_direct(self, text: str):
        """Synthesize and play speech directly."""
        self._is_speaking = True
        if self._on_start_callback:
            try:
                self._on_start_callback()
            except Exception:
                pass

        success = False
        # Try Edge-TTS first if configured
        if Config.TTS_ENGINE == "edge-tts":
            try:
                success = self._speak_with_edge_tts(text)
            except Exception as e:
                print(f"[TTS] Edge-TTS error, falling back to pyttsx3: {e}")
                success = False

        # Fallback to pyttsx3
        if not success:
            try:
                self._speak_with_pyttsx3(text)
                success = True
            except Exception as e:
                print(f"[TTS] pyttsx3 fallback error: {e}")

        self._is_speaking = False
        if self._on_finish_callback:
            try:
                self._on_finish_callback()
            except Exception:
                pass

    def _speak_with_edge_tts(self, text: str) -> bool:
        import edge_tts
        temp_file = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{time.time()}.mp3")

        async def generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice=Config.VOICE_NAME,
                rate=Config.VOICE_RATE,
                pitch=Config.VOICE_PITCH
            )
            await communicate.save(temp_file)

        asyncio.run(generate())

        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            return False

        if self._stop_event.is_set():
            try:
                os.remove(temp_file)
            except Exception:
                pass
            return True

        # Play audio using pygame mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                if self._stop_event.is_set():
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.05)

            pygame.mixer.music.unload()
        finally:
            try:
                os.remove(temp_file)
            except Exception:
                pass

        return True

    def _speak_with_pyttsx3(self, text: str):
        if not self._pyttsx3_engine:
            if pyttsx3:
                try:
                    self._pyttsx3_engine = pyttsx3.init()
                except Exception:
                    return
            else:
                return
        if self._stop_event.is_set():
            return
        try:
            self._pyttsx3_engine.say(text)
            self._pyttsx3_engine.runAndWait()
        except Exception:
            pass


tts = TTSEngine()
