"""Unit tests untuk scraper Forum (Kaskus + Reddit)."""
import pytest
from scraper.forum import ForumScraper


def test_forum_scraper_init():
    s = ForumScraper()
    assert s.name == "forum"


def test_forum_scraper_has_methods():
    s = ForumScraper()
    assert hasattr(s, "_scrape_kaskus_playwright")
    assert hasattr(s, "_scrape_reddit_playwright")
    assert hasattr(s, "_scrape_reddit_fallback_json")
    assert hasattr(s, "run")
