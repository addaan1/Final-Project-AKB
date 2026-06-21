"""Unit tests untuk data validation."""
import pandas as pd
import pytest
from processing.validate import validate_reviews, validate_tiktok, validate_forum, validate_twitter, validate_news


def test_validate_reviews_removes_duplicates():
    df = pd.DataFrame([
        {"review_id": "1", "content": "bagus", "at": "2025-01-01"},
        {"review_id": "1", "content": "bagus dup", "at": "2025-01-02"},
        {"review_id": "2", "content": "jelek", "at": "2025-01-03"},
    ])
    result = validate_reviews(df)
    assert len(result) == 2


def test_validate_reviews_removes_empty_content():
    df = pd.DataFrame([
        {"review_id": "1", "content": "bagus", "at": "2025-01-01"},
        {"review_id": "2", "content": "", "at": "2025-01-02"},
        {"review_id": "3", "content": None, "at": "2025-01-03"},
    ])
    result = validate_reviews(df)
    assert len(result) == 1


def test_validate_tiktok_removes_empty():
    df = pd.DataFrame([
        {"comment_id": "1", "text": "keren"},
        {"comment_id": "2", "text": ""},
        {"comment_id": "3", "text": "  "},
    ])
    result = validate_tiktok(df)
    assert len(result) == 1


def test_validate_twitter_removes_duplicates():
    df = pd.DataFrame([
        {"tweet_url": "https://x.com/1", "text": "tweet 1"},
        {"tweet_url": "https://x.com/1", "text": "tweet 1 dup"},
        {"tweet_url": "https://x.com/2", "text": "tweet 2"},
    ])
    result = validate_twitter(df)
    assert len(result) == 2
