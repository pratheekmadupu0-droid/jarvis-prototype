"""
JARVIS Central Glowing AI Core Widget
Custom PySide6 widget rendered with QPainter animating concentric rings,
arc segments, technical HUD ticks, and responsive state transitions.
"""

from __future__ import annotations
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QFont


class JarvisCoreWidget(QWidget):
    """Futuristic holographic reactor core."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)

        # States: 'idle', 'listening', 'processing', 'speaking', 'executing', 'success', 'error'
        self._state = "idle"

        # Animation parameters
        self._angle_outer = 0.0
        self._angle_inner = 0.0
        self._pulse = 0.0
        self._pulse_direction = 1

        # 60 FPS animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(16)

    def set_state(self, state: str):
        self._state = state.lower()
        self.update()

    def get_state(self) -> str:
        return self._state

    def _update_animation(self):
        # Rotation speeds based on state
        speed_factor = 1.0
        if self._state == "processing":
            speed_factor = 3.5
        elif self._state == "listening":
            speed_factor = 2.0
        elif self._state == "speaking":
            speed_factor = 2.5
        elif self._state == "executing":
            speed_factor = 2.8

        self._angle_outer = (self._angle_outer + 1.2 * speed_factor) % 360
        self._angle_inner = (self._angle_inner - 1.8 * speed_factor) % 360

        # Pulse breathing effect
        self._pulse += 0.03 * self._pulse_direction * speed_factor
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_direction = -1
        elif self._pulse <= 0.0:
            self._pulse = 0.0
            self._pulse_direction = 1

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        center_x = width / 2.0
        center_y = height / 2.0
        radius = min(width, height) / 2.0 - 15

        # Colors based on state
        if self._state == "error":
            primary = QColor(255, 51, 102)     # Crimson / red
            secondary = QColor(255, 183, 3)    # Amber
        elif self._state == "executing":
            primary = QColor(255, 183, 3)     # Amber
            secondary = QColor(0, 240, 255)    # Cyan
        elif self._state == "listening":
            primary = QColor(0, 119, 255)     # Deep Blue
            secondary = QColor(0, 240, 255)    # Cyan
        elif self._state == "speaking":
            primary = QColor(0, 240, 255)     # Glowing Cyan
            secondary = QColor(80, 220, 100)   # Emerald accent
        elif self._state == "success":
            primary = QColor(0, 255, 180)     # Neon Green/Cyan
            secondary = QColor(0, 240, 255)
        elif self._state == "processing":
            primary = QColor(138, 43, 226)    # Purple / Flux
            secondary = QColor(0, 240, 255)
        else:
            # Idle
            primary = QColor(0, 240, 255)     # Holographic Cyan
            secondary = QColor(0, 119, 255)    # Electric Blue

        # 1. Background radial glow
        glow_grad = QRadialGradient(center_x, center_y, radius)
        glow_grad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), int(40 + 25 * self._pulse)))
        glow_grad.setColorAt(0.6, QColor(secondary.red(), secondary.green(), secondary.blue(), int(15 + 10 * self._pulse)))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2))

        # 2. Outer Technical Ring with tick marks
        pen_outer = QPen(QColor(primary.red(), primary.green(), primary.blue(), 140))
        pen_outer.setWidthF(1.5)
        painter.setPen(pen_outer)
        painter.setBrush(Qt.NoBrush)

        outer_r = radius * 0.95
        painter.drawEllipse(QRectF(center_x - outer_r, center_y - outer_r, outer_r * 2, outer_r * 2))

        # Outer tick marks
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._angle_outer)
        num_ticks = 24
        for i in range(num_ticks):
            alpha = 200 if i % 4 == 0 else 70
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), alpha), 1.5 if i % 4 == 0 else 1.0))
            painter.drawLine(0, -int(outer_r), 0, -int(outer_r - (8 if i % 4 == 0 else 4)))
            painter.rotate(360 / num_ticks)
        painter.restore()

        # 3. Rotating Segmented Arcs
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self._angle_inner)
        arc_r = radius * 0.8
        arc_rect = QRectF(-arc_r, -arc_r, arc_r * 2, arc_r * 2)

        pen_arc = QPen(QColor(secondary.red(), secondary.green(), secondary.blue(), 220))
        pen_arc.setWidthF(3.0)
        painter.setPen(pen_arc)

        # Draw 3 arcs
        painter.drawArc(arc_rect, int(0 * 16), int(70 * 16))
        painter.drawArc(arc_rect, int(120 * 16), int(70 * 16))
        painter.drawArc(arc_rect, int(240 * 16), int(70 * 16))
        painter.restore()

        # 4. Inner Ring with Pulse
        pulse_r = radius * (0.55 + 0.05 * self._pulse)
        pen_inner = QPen(QColor(primary.red(), primary.green(), primary.blue(), int(180 + 75 * self._pulse)))
        pen_inner.setWidthF(2.0)
        painter.setPen(pen_inner)
        painter.drawEllipse(QRectF(center_x - pulse_r, center_y - pulse_r, pulse_r * 2, pulse_r * 2))

        # 5. Core Reactor Center Orb
        core_r = radius * 0.35
        core_grad = QRadialGradient(center_x, center_y, core_r)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
        core_grad.setColorAt(0.4, QColor(primary.red(), primary.green(), primary.blue(), 200))
        core_grad.setColorAt(1.0, QColor(secondary.red(), secondary.green(), secondary.blue(), 50))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(center_x - core_r, center_y - core_r, core_r * 2, core_r * 2))

        # 6. State Label in center or below
        painter.setFont(QFont("Consolas", 10, QFont.Bold))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 230)))
        state_text = self._state.upper()
        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(state_text)
        painter.drawText(int(center_x - text_w / 2), int(center_y + core_r + 25), state_text)
