"""Unit tests untuk scraper YouTube."""
import os
import pytest
from scraper.youtube import YouTubeScraper, SEARCH_QUERIES


def test_youtube_scraper_init_no_key():
    """Tanpa API key, scraper tetap bisa di-init tapi tidak bisa jalan."""
    old = os.environ.pop("YOUTUBE_API_KEY", None)
    try:
        s = YouTubeScraper()
        assert s.name == "youtube"
        assert s.api_key == ""
    finally:
        if old:
            os.environ["YOUTUBE_API_KEY"] = old


def test_youtube_search_queries():
    assert len(SEARCH_QUERIES) > 0
    assert all(isinstance(q, str) for q in SEARCH_QUERIES)
