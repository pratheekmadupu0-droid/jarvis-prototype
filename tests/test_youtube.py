"""
Integration tests for YouTube search using provided Google YouTube Data API v3 key.
"""

from app.integrations.youtube.youtube_client import SearchYouTubeTool, youtube_client


def test_youtube_search_api():
    tool = SearchYouTubeTool()
    res = tool.execute(query="Telugu motivational songs", autoplay=False)
    assert res.success is True
    assert "results" in res.data
    assert len(res.data["results"]) > 0


def test_youtube_play_video_structure():
    # Test payload without spawning web browser in test environment
    data = youtube_client.search_videos("Python tutorial for beginners", max_results=2)
    assert data["success"] is True
    assert len(data["results"]) > 0
    top = data["results"][0]
    assert "https://www.youtube.com" in top["url"]
