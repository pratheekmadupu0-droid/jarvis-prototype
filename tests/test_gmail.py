"""
Tests for Gmail Integration.
Verifies OAuth credentials file detection, draft composition, and confirmation safeguards.
"""

from app.integrations.email.gmail_client import gmail_client, GmailDraftTool
from app.config import Config


def test_gmail_credentials_file_exists():
    assert Config.GMAIL_CREDENTIALS_FILE.exists() is True


def test_gmail_draft_requires_confirmation():
    tool = GmailDraftTool()
    res = tool.execute(
        recipient="professor@university.edu",
        subject="Request for examination fee extension",
        body="Dear Professor, I kindly request permission to pay my examination fee next week. Regards."
    )

    assert res.success is True
    assert res.requires_confirmation is True
    assert "professor@university.edu" in res.confirmation_prompt
    assert gmail_client.pending_email is not None

    # Cancel draft
    gmail_client.pending_email = None
    assert gmail_client.pending_email is None
