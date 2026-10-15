"""
JARVIS Sound Wave Visualizer
Animates audio waveform bars responding to listening and speaking activity.
"""

from __future__ import annotations
import math
import random
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush


class SoundWaveWidget(QWidget):
    """Dynamic audio equalizer visualizer."""

    def __init__(self, num_bars: int = 24, parent=None):
        super().__init__(parent)
        self.num_bars = num_bars
        self.setMinimumHeight(45)
        self.setMinimumWidth(180)
        self._active = False
        self._levels = [0.1] * self.num_bars

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate_bars)
        self._timer.start(40)

    def set_active(self, active: bool):
        self._active = active

    def _animate_bars(self):
        if self._active:
            self._levels = [random.uniform(0.15, 0.95) for _ in range(self.num_bars)]
        else:
            self._levels = [max(0.08, l * 0.85) for l in self._levels]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_w = max(2.0, (w / self.num_bars) - 2.5)

        for i, lvl in enumerate(self._levels):
            x = i * (bar_w + 2.5)
            bar_h = h * lvl
            y = (h - bar_h) / 2.0

            # Gradient color from blue to cyan
            ratio = i / float(self.num_bars)
            r = int(0)
            g = int(120 + 135 * ratio)
            b = 255
            alpha = int(100 + 155 * lvl)

            painter.setBrush(QBrush(QColor(r, g, b, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(x, y, bar_w, bar_h, 1.5, 1.5)
