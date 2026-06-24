"""Unit tests untuk Area C — VADER sentiment analysis, extended untuk Bahasa Indonesia."""
from processing.sentiment import analyze_sentiment


def test_sentiment_positive():
    result = analyze_sentiment(["saya sangat senang dan bahagia sekali"])
    assert len(result) == 1
    assert result[0]["sentiment_label"] == "positive"
    assert result[0]["sentiment_compound"] > 0.05


def test_sentiment_negative():
    result = analyze_sentiment(["saya sangat kecewa dan marah sekali"])
    assert len(result) == 1
    assert result[0]["sentiment_label"] == "negative"
    assert result[0]["sentiment_compound"] < -0.05


def test_sentiment_empty():
    result = analyze_sentiment([""])
    assert len(result) == 1
    assert result[0]["sentiment_label"] == "neutral"
    assert result[0]["sentiment_compound"] == 0


def test_sentiment_batch():
    texts = ["bagus sekali", "jelek banget", "biasa saja tidak ada apa apa"]
    result = analyze_sentiment(texts)
    assert len(result) == 3
    for r in result:
        assert "sentiment_pos" in r
        assert "sentiment_neg" in r
        assert "sentiment_neu" in r
        assert "sentiment_compound" in r
        assert "sentiment_label" in r
    assert result[0]["sentiment_label"] == "positive"
    assert result[1]["sentiment_label"] == "negative"
    assert result[2]["sentiment_label"] == "neutral"


def test_negation_flips_polarity():
    # "tidak bagus" must score negative, not positive — without extending
    # VADER's NEGATE list with Indonesian negators, the lexicon-only fix
    # alone would still mis-score this as a plain positive "bagus".
    result = analyze_sentiment(["pelayanannya tidak bagus"])
    assert result[0]["sentiment_label"] == "negative"
    assert result[0]["sentiment_compound"] < 0


def test_slang_negation_via_clean_text():
    # "gak puas" -> clean_text normalizes "gak" to "tidak" before VADER
    # scores it, so the negation above also catches common slang spellings.
    result = analyze_sentiment(["gak puas sama sekali"])
    assert result[0]["sentiment_label"] == "negative"


def test_galbay_domain_terms_score_negative():
    result = analyze_sentiment(["takut terus ditelpon dc katanya saya galbay"])
    assert result[0]["sentiment_label"] == "negative"
    assert result[0]["sentiment_compound"] < -0.05


def test_loan_disbursed_smoothly_scores_positive():
    result = analyze_sentiment(["pengajuan disetujui dan dana cair lancar"])
    assert result[0]["sentiment_label"] == "positive"


def test_batch_preserves_order_and_length():
    texts = ["bagus", "", "jelek"]
    result = analyze_sentiment(texts)
    assert len(result) == 3
    assert result[1]["sentiment_label"] == "neutral"
