"""
JARVIS Gmail Integration
Connects to Google Gmail API using credentials.json and OAuth2.
Supports reading unread emails, searching, drafting, and confirmed sending.
"""

from __future__ import annotations
import os
import base64
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from app.config import Config
from app.tools.base import BaseTool, ToolResult

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]


class GmailClient:
    """Manages Gmail API communication with OAuth2."""

    def __init__(self):
        self.service = None
        self.pending_email: Optional[Dict[str, Any]] = None

    def authenticate(self, interactive: bool = False) -> bool:
        """Authenticate with Google OAuth2."""
        creds = None
        token_path = Config.GMAIL_TOKEN_FILE
        credentials_path = Config.GMAIL_CREDENTIALS_FILE

        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds and interactive and credentials_path.exists():
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                    with open(token_path, 'w', encoding='utf-8') as token_file:
                        token_file.write(creds.to_json())
                except Exception as e:
                    print(f"[Gmail] OAuth interactive flow error: {e}")
                    return False

        if creds and creds.valid:
            try:
                self.service = build('gmail', 'v1', credentials=creds)
                return True
            except Exception as e:
                print(f"[Gmail] Service build error: {e}")
                return False

        return False

    def is_authorized(self) -> bool:
        return self.service is not None or (Config.GMAIL_TOKEN_FILE.exists() and self.authenticate(interactive=False))

    def list_unread_emails(self, max_results: int = 5) -> Dict[str, Any]:
        """Fetch and summarize latest unread messages."""
        if not self.is_authorized():
            return {
                "success": False,
                "error": "Gmail authorization required. Please authenticate via the Settings dialog."
            }

        try:
            results = self.service.users().messages().list(userId='me', q='is:unread', maxResults=max_results).execute()
            messages = results.get('messages', [])

            if not messages:
                return {"success": True, "count": 0, "summary": "You have no unread emails.", "emails": []}

            email_list = []
            for m in messages:
                msg = self.service.users().messages().get(userId='me', id=m['id'], format='metadata').execute()
                headers = msg.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                snippet = msg.get('snippet', '')
                email_list.append({
                    "id": m['id'],
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet
                })

            summary_lines = [f"{i}. From {e['sender']}: '{e['subject']}'" for i, e in enumerate(email_list, 1)]
            spoken = f"You have {len(email_list)} unread emails. " + ". ".join([f"From {e['sender']}: {e['subject']}" for e in email_list[:3]])

            return {
                "success": True,
                "count": len(email_list),
                "summary": spoken,
                "detailed": "\n".join(summary_lines),
                "emails": email_list
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to retrieve emails: {str(e)}"}

    def prepare_draft(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Prepare email draft requiring explicit confirmation before send."""
        draft = {
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "status": "awaiting_confirmation"
        }
        self.pending_email = draft
        return draft

    def send_confirmed_email(self) -> Tuple[bool, str]:
        """Send the prepared email after user confirms."""
        if not self.pending_email:
            return False, "No email prepared for sending."

        if not self.is_authorized():
            return False, "Gmail authorization required."

        try:
            msg = MIMEText(self.pending_email["body"])
            msg['to'] = self.pending_email["recipient"]
            msg['subject'] = self.pending_email["subject"]
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            sent_msg = self.service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
            recipient = self.pending_email["recipient"]
            self.pending_email = None
            return True, f"Email sent successfully to {recipient} (Message ID: {sent_msg.get('id')})."
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"


gmail_client = GmailClient()


class GmailUnreadTool(BaseTool):
    name = "gmail_unread_emails"
    description = "Check and summarize unread emails in Gmail."
    parameters_schema = {
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "Number of emails to retrieve"}
        }
    }

    def execute(self, max_results: int = 5) -> ToolResult:
        res = gmail_client.list_unread_emails(max_results)
        if not res.get("success"):
            return ToolResult(success=False, message=res.get("error", "Gmail error"))
        return ToolResult(success=True, message=res["summary"], data=res)


class GmailDraftTool(BaseTool):
    name = "gmail_draft_email"
    description = "Draft an email to a recipient with subject and body, and prepare it for confirmation."
    parameters_schema = {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Recipient email address"},
            "subject": {"type": "string", "description": "Email subject line"},
            "body": {"type": "string", "description": "Email body content"}
        },
        "required": ["recipient", "subject", "body"]
    }

    def execute(self, recipient: str, subject: str, body: str) -> ToolResult:
        draft = gmail_client.prepare_draft(recipient, subject, body)
        prompt = (
            f"I have prepared your email to {recipient}.\n"
            f"Subject: {subject}\n"
            f"Content: {body}\n\n"
            f"Would you like me to send this email?"
        )
        return ToolResult(
            success=True,
            message=prompt,
            requires_confirmation=True,
            confirmation_prompt=f"Send email to {recipient} with subject '{subject}'?",
            confirmation_payload=draft,
            data=draft
        )


class GmailSendConfirmedTool(BaseTool):
    name = "gmail_send_confirmed"
    description = "Send the previously confirmed email."
    parameters_schema = {
        "type": "object",
        "properties": {
            "confirmation": {"type": "boolean", "description": "Must be true"}
        },
        "required": ["confirmation"]
    }

    def execute(self, confirmation: bool = True) -> ToolResult:
        if not confirmation:
            gmail_client.pending_email = None
            return ToolResult(success=True, message="Email sending cancelled.")
        success, msg = gmail_client.send_confirmed_email()
        return ToolResult(success=success, message=msg)
