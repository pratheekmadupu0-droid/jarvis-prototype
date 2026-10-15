"""
JARVIS Playwright Browser Controller
Provides automated web interactions using Playwright Chromium with user profile persistence.
"""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from app.config import DATA_DIR
from app.tools.base import BaseTool, ToolResult


class PlaywrightBrowser:
    """Manages browser sessions using Playwright."""

    def __init__(self):
        self.user_data_dir = DATA_DIR / "browser_profile"
        self.user_data_dir.mkdir(exist_ok=True)

    def navigate_and_extract(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL and extract text title and summary."""
        try:
            from playwright.sync_api import sync_playwright

            target = url if url.startswith("http") else f"https://{url}"

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(target, timeout=20000)
                page.wait_for_load_state("domcontentloaded")

                title = page.title()
                # Get clean text
                body_text = page.inner_text("body")
                clean_text = " ".join(body_text.split())[:1500]

                browser.close()
                return {
                    "success": True,
                    "url": target,
                    "title": title,
                    "text_sample": clean_text
                }
        except Exception as e:
            return {"success": False, "error": f"Browser navigation error: {str(e)}"}

    def search_web(self, query: str) -> Dict[str, Any]:
        """Search DuckDuckGo or Google directly."""
        try:
            import urllib.parse
            encoded = urllib.parse.quote(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded}"
            return self.navigate_and_extract(search_url)
        except Exception as e:
            return {"success": False, "error": str(e)}


browser_controller = PlaywrightBrowser()


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information, articles, and websites."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> ToolResult:
        res = browser_controller.search_web(query)
        if res.get("success"):
            return ToolResult(
                success=True,
                message=f"Web search results for '{query}':\n{res['text_sample'][:500]}...",
                data=res
            )
        return ToolResult(success=False, message=res.get("error", "Web search failed."))


class BrowserNavigateTool(BaseTool):
    name = "browser_navigate"
    description = "Navigate to a website and read its visible content."
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Web URL to navigate to"}
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> ToolResult:
        res = browser_controller.navigate_and_extract(url)
        if res.get("success"):
            return ToolResult(
                success=True,
                message=f"Visited {res['title']} ({url}).\nSummary: {res['text_sample'][:400]}...",
                data=res
            )
        return ToolResult(success=False, message=res.get("error", "Navigation failed."))
