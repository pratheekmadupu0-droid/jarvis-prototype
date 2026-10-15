"""
JARVIS YouTube & Media Integration
Uses Google YouTube Data API v3 and browser control to search and play videos,
songs, trailers, and tutorials.
"""

from __future__ import annotations
import requests
import webbrowser
from typing import Dict, Any, List, Optional
from app.config import Config
from app.tools.base import BaseTool, ToolResult


class YouTubeClient:
    """YouTube Data API v3 Client."""

    BASE_URL = "https://www.googleapis.com/youtube/v3/search"

    def __init__(self, api_key: str = Config.YOUTUBE_API_KEY):
        self.api_key = api_key

    def search_videos(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search videos by query string."""
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": self.api_key
        }

        try:
            res = requests.get(self.BASE_URL, params=params, timeout=10)
            data = res.json()

            items = data.get("items", [])
            results = []
            for item in items:
                video_id = item.get("id", {}).get("videoId")
                snippet = item.get("snippet", {})
                if video_id:
                    results.append({
                        "video_id": video_id,
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "description": snippet.get("description", ""),
                        "url": f"https://www.youtube.com/watch?v={video_id}"
                    })

            if not results:
                # Direct fallback YouTube search URL
                direct_search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
                return {
                    "success": True,
                    "query": query,
                    "results": [{
                        "video_id": "",
                        "title": f"YouTube Search: {query}",
                        "channel": "YouTube",
                        "url": direct_search_url
                    }]
                }

            return {
                "success": True,
                "query": query,
                "results": results
            }
        except Exception as e:
            direct_search_url = f"https://www.youtube.com/results?search_query={requests.utils.quote(query)}"
            return {
                "success": True,
                "query": query,
                "results": [{
                    "video_id": "",
                    "title": f"YouTube Search: {query}",
                    "channel": "YouTube",
                    "url": direct_search_url
                }],
                "note": f"API fallback used: {str(e)}"
            }

    def play_video(self, query: str) -> Dict[str, Any]:
        """Search and immediately open top video in Google Chrome."""
        data = self.search_videos(query, max_results=1)
        if data.get("success") and data.get("results"):
            top = data["results"][0]
            try:
                from app.tools.system_tools import open_url_in_chrome
                open_url_in_chrome(top["url"])
            except Exception as e:
                print(f"[YouTube] open error: {e}")
            return {
                "success": True,
                "title": top["title"],
                "channel": top["channel"],
                "url": top["url"],
                "open_url": top["url"]
            }
        return {"success": False, "error": "Could not find video."}


youtube_client = YouTubeClient()


class SearchYouTubeTool(BaseTool):
    name = "search_youtube"
    description = "Search YouTube for videos, songs, tutorials, or music, and optionally play the top result."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query (e.g. 'Telugu motivational songs', 'Python tutorial', 'relaxing music')"},
            "autoplay": {"type": "boolean", "description": "Whether to immediately open the top video in the browser (default true)"}
        },
        "required": ["query"]
    }

    def execute(self, query: str, autoplay: bool = True) -> ToolResult:
        if autoplay:
            res = youtube_client.play_video(query)
            if res.get("success"):
                msg = f"Playing '{res['title']}' on YouTube ({res['channel']})."
                return ToolResult(success=True, message=msg, data=res)
            return ToolResult(success=False, message="Unable to open video.")
        else:
            res = youtube_client.search_videos(query, max_results=5)
            if res.get("success"):
                titles = [f"- {v['title']} ({v['channel']})" for v in res["results"]]
                msg = f"Found {len(res['results'])} YouTube results for '{query}':\n" + "\n".join(titles)
                return ToolResult(success=True, message=msg, data=res)
            return ToolResult(success=False, message=res.get("error", "YouTube search failed."))
