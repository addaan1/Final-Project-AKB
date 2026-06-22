"""Unit tests untuk sentiment analysis."""
import pytest
from processing.sentiment import analyze_sentiment


def test_sentiment_positive():
    result = analyze_sentiment(["saya sangat senang dan bahagia"])
    assert len(result) == 1
    assert result[0]["sentiment_label"] in ("positive", "neutral")
    assert result[0]["sentiment_compound"] > -1


def test_sentiment_negative():
    result = analyze_sentiment(["saya sangat kecewa dan marah"])
    assert len(result) == 1
    assert result[0]["sentiment_label"] in ("negative", "neutral")


def test_sentiment_empty():
    result = analyze_sentiment([""])
    assert len(result) == 1
    assert result[0]["sentiment_label"] == "neutral"


def test_sentiment_batch():
    texts = ["bagus sekali", "jelek banget", "biasa saja"]
    result = analyze_sentiment(texts)
    assert len(result) == 3
    for r in result:
        assert "sentiment_pos" in r
        assert "sentiment_neg" in r
        assert "sentiment_neu" in r
        assert "sentiment_compound" in r
        assert "sentiment_label" in r
