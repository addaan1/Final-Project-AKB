"""Unit tests untuk scraper TikTok."""
import pytest
from scraper.tiktok import TikTokScraper


def test_tiktok_scraper_init():
    s = TikTokScraper()
    assert s.name == "tiktok"


def test_redact_username():
    result = TikTokScraper._redact_username("testuser123")
    assert isinstance(result, str)
    assert len(result) == 12
    assert result != "testuser123"
    assert TikTokScraper._redact_username("testuser123") == result


def test_redact_consistency():
    u1 = TikTokScraper._redact_username("alice")
    u2 = TikTokScraper._redact_username("bob")
    assert u1 != u2
