"""
JARVIS Speech-to-Text Module
Performs speech recognition using SpeechRecognition with Google Speech API or Whisper.
"""

from __future__ import annotations
import speech_recognition as sr
from typing import Optional, Tuple
from app.config import Config


class STTEngine:
    """Manages audio transcription."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def transcribe_audio(self, audio: sr.AudioData) -> Tuple[bool, str]:
        """Transcribe an AudioData buffer to text."""
        try:
            # Use Google Speech API by default (free, fast, high accuracy)
            text = self.recognizer.recognize_google(audio)
            return True, text.strip()
        except sr.UnknownValueError:
            return False, "Could not understand audio."
        except sr.RequestError as e:
            return False, f"Speech recognition service error: {str(e)}"
        except Exception as e:
            return False, f"Transcription error: {str(e)}"

    def listen_once(self, timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Tuple[bool, str]:
        """Listen to the microphone once synchronously."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                return self.transcribe_audio(audio)
        except sr.WaitTimeoutError:
            return False, "Listening timed out."
        except Exception as e:
            return False, f"Microphone error: {str(e)}"


stt = STTEngine()
