"""Unit tests untuk scraper Apple App Store."""
import pytest
from scraper.appstore_reviews import APPSTORE_IDS, AppStore, AppStoreReviewsScraper


def test_appstore_scraper_init():
    if AppStore is None:
        with pytest.raises(RuntimeError, match="app-store-scraper"):
            AppStoreReviewsScraper()
    else:
        s = AppStoreReviewsScraper()
        assert s.name == "appstore_reviews"


def test_appstore_ids_not_empty():
    assert len(APPSTORE_IDS) > 0
    for name, info in APPSTORE_IDS.items():
        assert "app_id" in info
        assert "category" in info
        assert info["app_id"].isdigit()


def test_normalize_row():
    r = {
        "reviewId": "123",
        "rating": 1,
        "title": "Buruk",
        "review": "Aplikasi jelek",
        "helpfulCount": 0,
        "date": None,
    }
    app = {"query": "Test", "app_id": "123", "category": "test"}
    norm = AppStoreReviewsScraper._normalize_row(r, app)
    assert norm["app_name"] == "Test"
    assert norm["score"] == 1
    assert norm["content"] == "Aplikasi jelek"
    assert norm["user_name"] == "[anonymized]"
