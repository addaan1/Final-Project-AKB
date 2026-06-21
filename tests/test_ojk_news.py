"""Unit tests untuk scraper OJK + Media."""
import pytest
from scraper.ojk_news import OjkNewsScraper


def test_ojk_scraper_init():
    s = OjkNewsScraper()
    assert s.name == "ojk_news"


def test_ojk_scraper_has_methods():
    s = OjkNewsScraper()
    assert hasattr(s, "_scrape_ojk")
    assert hasattr(s, "_scrape_media")
    assert hasattr(s, "run")
