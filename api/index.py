"""
Vercel Serverless Function Entry Point for JARVIS.
Routes web interface and API requests to FastAPI app instance.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.web_server import app

# Vercel recognizes 'app', 'application', or 'handler'
application = app
handler = app
