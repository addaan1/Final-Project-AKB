"""Unit tests untuk NLP preprocessing."""
import pytest
from processing.preprocess import clean_text, preprocess_texts


def test_clean_text_lowercase():
    assert clean_text("HELLO WORLD") == "hello world"


def test_clean_text_remove_urls():
    result = clean_text("cek https://example.com ya")
    assert "https" not in result
    assert "example" not in result


def test_clean_text_remove_mentions():
    result = clean_text("hai @user123 apa kabar")
    assert "@user123" not in result


def test_clean_text_remove_hashtags():
    result = clean_text("keren #galbay banget")
    assert "#galbay" not in result


def test_clean_text_slang():
    result = clean_text("yg gak bagus")
    assert "yang" in result
    assert "tidak" in result


def test_preprocess_texts_batch():
    texts = ["HELLO @user", "https://test.com #tag"]
    results = preprocess_texts(texts)
    assert len(results) == 2
    assert "@" not in results[0]
    assert "http" not in results[1]
    assert "#" not in results[1]
