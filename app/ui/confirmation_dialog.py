"""
JARVIS Action Authorization & Confirmation Modal Dialog
Prompts the user for explicit approval before sending WhatsApp messages, emails,
or executing destructive filesystem actions.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from app.ui.styles import QSS_STYLESHEET


class ConfirmationDialog(QDialog):
    """Futuristic confirmation dialog for sensitive actions."""

    def __init__(self, title: str, prompt: str, details: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"JARVIS // {title.upper()}")
        self.setModal(True)
        self.resize(520, 360)
        self.setStyleSheet(QSS_STYLESHEET)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Frame
        header = QLabel(f"SECURITY CLEARANCE // {title.upper()}")
        header.setProperty("class", "title-label")
        layout.addWidget(header)

        sub_msg = QLabel("The following operation requires explicit user authorization before execution:")
        sub_msg.setStyleSheet("color: #80A0B5; font-size: 12px;")
        sub_msg.setWordWrap(True)
        layout.addWidget(sub_msg)

        # Prompt Box
        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("color: #FFB703; font-weight: bold; font-size: 14px;")
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

        # Details Content
        if details:
            self.details_edit = QTextEdit()
            self.details_edit.setPlainText(details)
            self.details_edit.setReadOnly(True)
            self.details_edit.setMaximumHeight(140)
            layout.addWidget(self.details_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_cancel = QPushButton("CANCEL OPERATION")
        self.btn_cancel.setProperty("class", "danger-btn")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_approve = QPushButton("AUTHORIZE & EXECUTE")
        self.btn_approve.setProperty("class", "action-btn")
        self.btn_approve.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_approve)

        layout.addLayout(btn_layout)


def request_user_confirmation(title: str, prompt: str, details: str = "", parent=None) -> bool:
    dialog = ConfirmationDialog(title, prompt, details, parent)
    return dialog.exec() == QDialog.Accepted
