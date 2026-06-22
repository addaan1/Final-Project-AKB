"""Unit tests untuk scraper Blog."""
import pytest
from scraper.blogs import BlogScraper, BLOG_QUERIES


def test_blog_scraper_init():
    s = BlogScraper()
    assert s.name == "blogs"


def test_blog_queries_not_empty():
    assert len(BLOG_QUERIES) > 0
    assert all(isinstance(q, str) for q in BLOG_QUERIES)
