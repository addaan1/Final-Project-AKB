"""Unit tests untuk scraper Twitter (Nitter)."""
import pytest
from scraper.twitter import TwitterScraper


def test_twitter_scraper_init():
    s = TwitterScraper()
    assert s.name == "twitter"


def test_redact_username():
    result = TwitterScraper._redact_username("elonmusk")
    assert isinstance(result, str)
    assert len(result) == 12
