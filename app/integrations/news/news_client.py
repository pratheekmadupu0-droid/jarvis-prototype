"""
JARVIS Live News Integration
Connects to NewsAPI to retrieve real-time news headlines, technology updates,
geographical news, and specific topic searches with verified sources and dates.
"""

from __future__ import annotations
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.config import Config
from app.tools.base import BaseTool, ToolResult


class NewsClient:
    """NewsAPI.org Client."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str = Config.NEWS_API_KEY):
        self.api_key = api_key

    def get_news(self, query: Optional[str] = None, category: Optional[str] = None, page_size: int = 5) -> Dict[str, Any]:
        """Fetch latest news articles matching query or category."""
        target_query = query.strip() if query else "technology"

        # Try everything endpoint first for query
        url = f"{self.BASE_URL}/everything"
        params = {
            "q": target_query,
            "sortBy": "publishedAt",
            "pageSize": page_size,
            "apiKey": self.api_key
        }

        try:
            res = requests.get(url, params=params, timeout=10)
            data = res.json()
            articles = data.get("articles", [])

            # If no articles with query, fallback to top-headlines
            if not articles:
                top_url = f"{self.BASE_URL}/top-headlines"
                top_params = {
                    "category": category or "general",
                    "language": "en",
                    "pageSize": page_size,
                    "apiKey": self.api_key
                }
                r2 = requests.get(top_url, params=top_params, timeout=10)
                articles = r2.json().get("articles", [])

            parsed = []
            for a in articles[:page_size]:
                title = a.get("title", "")
                if "[Removed]" in title or not title:
                    continue
                source = a.get("source", {}).get("name", "Unknown Source")
                pub_date = a.get("publishedAt", "")[:10]
                url = a.get("url", "")
                description = a.get("description", "") or title

                parsed.append({
                    "title": title,
                    "source": source,
                    "published_at": pub_date,
                    "url": url,
                    "summary": description
                })

            if not parsed:
                return {
                    "success": False,
                    "error": f"No recent news found for '{target_query}'."
                }

            # Build spoken summary & detailed list
            bullet_points = []
            spoken_items = []
            for i, p in enumerate(parsed[:3], 1):
                bullet_points.append(f"{i}. {p['title']} ({p['source']}, {p['published_at']})\n   Link: {p['url']}")
                spoken_items.append(f"{p['title']} reported by {p['source']}.")

            spoken_summary = f"Here are the latest news updates on {target_query}: " + " Next story: ".join(spoken_items)
            detailed_text = "\n\n".join(bullet_points)

            return {
                "success": True,
                "query": target_query,
                "spoken_summary": spoken_summary,
                "detailed_text": detailed_text,
                "articles": parsed
            }

        except Exception as e:
            return {"success": False, "error": f"Failed to fetch news: {str(e)}"}


news_client = NewsClient()


class GetNewsTool(BaseTool):
    name = "get_news"
    description = "Retrieve current news headlines on any topic (technology, AI, India, world, cybersecurity)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "News topic or keyword (e.g. 'technology', 'India', 'AI', 'cybersecurity')"}
        }
    }

    def execute(self, query: Optional[str] = "technology") -> ToolResult:
        res = news_client.get_news(query=query)
        if not res.get("success"):
            return ToolResult(success=False, message=res.get("error", "News unavailable."))
        return ToolResult(
            success=True,
            message=res["spoken_summary"],
            data={"articles": res["articles"], "detailed": res["detailed_text"]}
        )
