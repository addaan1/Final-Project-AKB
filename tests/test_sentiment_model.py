"""Unit tests untuk Area A — Naive Bayes sentiment classifier (from scratch)."""
import math

import numpy as np
import pandas as pd
import pytest

from scripts.sentiment_model import (
    build_vocab,
    cross_validate,
    evaluate,
    predict,
    predict_tokens,
    stratified_split,
    tokenize,
    top_predictive_words,
    train_naive_bayes,
)

POSITIVE_SENTENCES = [
    "aplikasi ini sangat bagus dan membantu sekali",
    "pelayanan ramah proses cepat puas sekali pakai aplikasi ini",
    "mantap banget aplikasinya membantu sekali untuk kebutuhan saya",
    "suka banget aplikasi ini cepat dan mudah digunakan",
    "pencairan dana lancar dan customer service sangat ramah",
    "sangat puas dengan pelayanan aplikasi ini bagus sekali",
    "proses approval cepat dan mudah sangat membantu sekali",
    "aplikasi terbaik pelayanan memuaskan dan sangat membantu",
    "senang sekali pakai aplikasi ini sangat membantu keuangan",
    "rekomendasi banget aplikasi ini bagus dan terpercaya sekali",
]
NEGATIVE_SENTENCES = [
    "aplikasi ini sangat buruk dan mengecewakan sekali",
    "pelayanan jelek proses lambat kecewa pakai aplikasi ini",
    "parah banget aplikasinya error terus mengecewakan sekali",
    "benci banget aplikasi ini lambat dan ribet digunakan",
    "debt collector teror terus dan customer service sangat buruk",
    "sangat kecewa dengan pelayanan aplikasi ini buruk sekali",
    "proses penagihan kasar dan ribet sangat mengecewakan sekali",
    "aplikasi terburuk pelayanan mengecewakan dan sangat buruk",
    "menyesal sekali pakai aplikasi ini sangat merugikan keuangan",
    "jangan pakai aplikasi ini buruk dan tidak terpercaya sekali",
]


def _toy_df():
    rows = [{"content": s, "label": 1} for s in POSITIVE_SENTENCES]
    rows += [{"content": s, "label": 0} for s in NEGATIVE_SENTENCES]
    return pd.DataFrame(rows)


class TestTokenize:
    def test_lowercases_and_drops_short_stopwords(self):
        # "aplikasi" and "ini" are themselves in STOPWORDS (reviews are
        # almost always about "the app"), so only content words remain.
        assert tokenize("Aplikasi INI Sangat Bagus") == ["sangat", "bagus"]

    def test_drops_tokens_below_min_len(self):
        assert "di" not in tokenize("aku di sini")
        assert "ok" not in tokenize("ok bagus")  # len 2, default min_len=3

    def test_keeps_alphabetic_only(self):
        assert tokenize("bagus123 sekali!!!") == ["bagus", "sekali"]

    def test_empty_text(self):
        assert tokenize("") == []


class TestBuildVocab:
    def test_min_df_filters_rare_tokens(self):
        docs = [["bagus", "mantap"], ["bagus", "keren"], ["bagus"]]
        vocab = build_vocab(docs, min_df=2)
        assert "bagus" in vocab
        assert "mantap" not in vocab  # appears in only 1 doc
        assert "keren" not in vocab

    def test_vocab_indices_are_unique_and_contiguous(self):
        docs = [["a", "b"], ["a", "c"], ["a", "b", "c"]]
        vocab = build_vocab(docs, min_df=1)
        assert sorted(vocab.values()) == list(range(len(vocab)))


class TestStratifiedSplit:
    def test_preserves_label_proportion(self):
        df = pd.DataFrame({"label": [1] * 80 + [0] * 20})
        train, test = stratified_split(df, label_col="label", test_size=0.25, seed=1)
        train_ratio = train["label"].mean()
        test_ratio = test["label"].mean()
        assert train_ratio == pytest.approx(0.8, abs=0.02)
        assert test_ratio == pytest.approx(0.8, abs=0.02)

    def test_no_overlap_between_train_and_test(self):
        df = pd.DataFrame({"label": [1] * 50 + [0] * 50, "id": range(100)})
        train, test = stratified_split(df, label_col="label", test_size=0.2, seed=1)
        assert set(train["id"]) & set(test["id"]) == set()
        assert len(train) + len(test) == 100


class TestTrainAndPredict:
    def test_separates_obviously_positive_and_negative_text(self):
        df = _toy_df()
        model = train_naive_bayes(df, text_col="content", label_col="label", min_df=1)
        assert predict(model, "aplikasi sangat bagus membantu dan memuaskan") == 1
        assert predict(model, "aplikasi sangat buruk mengecewakan dan ribet") == 0

    def test_laplace_smoothing_avoids_zero_probability(self):
        df = _toy_df()
        model = train_naive_bayes(df, text_col="content", label_col="label", min_df=1)
        # a word seen only in the negative class must still have a finite
        # (non -inf) log-likelihood under the positive class, thanks to add-1
        # smoothing — this is the whole point of Laplace smoothing.
        neg_only_word = "teror"
        j = model["vocab"][neg_only_word]
        assert math.isfinite(model["loglik"][1][j])
        assert model["loglik"][1][j] < model["loglik"][0][j]

    def test_tie_breaks_toward_larger_class_label(self):
        model = {
            "vocab": {}, "classes": [0, 1],
            "logprior": {0: -0.1, 1: -0.1},
            "loglik": {0: np.array([]), 1: np.array([])},
        }
        assert predict_tokens(model, []) == 1


class TestEvaluate:
    def test_metrics_match_known_confusion_matrix(self):
        model = train_naive_bayes(_toy_df(), text_col="content", label_col="label", min_df=1)
        test_df = pd.DataFrame(
            {
                "content": ["sangat bagus membantu memuaskan", "sangat buruk mengecewakan ribet"],
                "label": [1, 0],
            }
        )
        metrics = evaluate(model, test_df, text_col="content", label_col="label")
        assert metrics["accuracy"] == 1.0
        assert metrics["confusion"] == {"TP": 1, "TN": 1, "FP": 0, "FN": 0}
        assert metrics["macro_f1"] == pytest.approx(1.0)

    def test_top_predictive_words_orientation(self):
        model = train_naive_bayes(_toy_df(), text_col="content", label_col="label", min_df=1)
        top_neg, top_pos = top_predictive_words(model, k=5, class_a=0, class_b=1)
        neg_words = {w for w, _ in top_neg}
        pos_words = {w for w, _ in top_pos}
        assert "buruk" in neg_words or "mengecewakan" in neg_words
        assert "bagus" in pos_words or "membantu" in pos_words
        assert neg_words.isdisjoint(pos_words)


class TestCrossValidate:
    def test_returns_k_folds_with_bounded_accuracy(self):
        fold_metrics, summary = cross_validate(_toy_df(), text_col="content", label_col="label", k=4, min_df=1)
        assert summary["k"] == 4
        assert len(fold_metrics) == 4
        assert 0.0 <= summary["accuracy_mean"] <= 1.0
