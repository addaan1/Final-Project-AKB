"""Area A — Multinomial Naive Bayes sentiment classifier, from scratch.

Tokenizer, vocab building, Laplace-smoothed training, evaluation, and
top predictive words. No external ML library: this is the handwritten
Naive Bayes required for the final project's modelling section.

Penggunaan (dari scripts/analyze.py):
    from sentiment_model import tokenize, stratified_split, train_naive_bayes, evaluate, top_predictive_words
"""
from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np
import pandas as pd

STOPWORDS = set('''yang di ke dari dan atau ini itu untuk dengan pada saya aku kamu dia mereka kami kita
ada tidak ga gak ngga nggak engga tdk udah sudah belum lagi juga aja saja kok sih deh dong ya yaa
nya kah pun para per se the a an is are was do does si bang min admin app aplikasi nih tuh gitu gini
bisa bukan kalo kalau karena biar buat dapat dapet jadi jd klo nya banget bgt kan akan masih mau
lah loh org orang tp tapi dr dgn utk yg krn pada oleh sd sampai hingga agar supaya kpd kepada
'''.split())

TOKEN_RE = re.compile(r"[a-zA-Z]+")


def tokenize(text: str, stopwords: set[str] = STOPWORDS, min_len: int = 3) -> list[str]:
    """Lowercase, keep alphabetic tokens, drop stopwords and very short tokens."""
    return [w for w in TOKEN_RE.findall(str(text).lower()) if len(w) >= min_len and w not in stopwords]


def stratified_split(df: pd.DataFrame, label_col: str, test_size: float = 0.2, seed: int = 42):
    """Train/test split that preserves each label's proportion.

    A plain random permutation (the original approach) can leave a small or
    imbalanced test set skewed toward one class, making accuracy/F1 noisy.
    """
    rng = np.random.RandomState(seed)
    train_parts, test_parts = [], []
    for _, group in df.groupby(label_col):
        idx = rng.permutation(len(group))
        cut = int(len(group) * (1 - test_size))
        train_parts.append(group.iloc[idx[:cut]])
        test_parts.append(group.iloc[idx[cut:]])
    train = pd.concat(train_parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    test = pd.concat(test_parts).sample(frac=1, random_state=seed).reset_index(drop=True)
    return train, test


def build_vocab(tokenized_docs, min_df: int = 5) -> dict[str, int]:
    """Vocabulary of tokens that appear in at least `min_df` documents."""
    df_counter = Counter()
    for toks in tokenized_docs:
        df_counter.update(set(toks))
    words = [w for w, c in df_counter.items() if c >= min_df]
    return {w: i for i, w in enumerate(words)}


def train_naive_bayes(
    train_df: pd.DataFrame,
    text_col: str = "content",
    label_col: str = "label",
    min_df: int = 5,
    tokens_col: str | None = None,
) -> dict:
    """Multinomial Naive Bayes with Laplace (add-1) smoothing, from scratch.

    Returns {"vocab", "logprior", "loglik", "classes"}.
    """
    tokens = train_df[tokens_col] if tokens_col else train_df[text_col].apply(tokenize)
    classes = sorted(train_df[label_col].unique())
    vocab = build_vocab(tokens, min_df=min_df)
    V = len(vocab)

    cls_word = {c: np.ones(V) for c in classes}  # Laplace smoothing: prior count = 1
    cls_tot = {c: 0.0 for c in classes}
    cls_docs = {c: 0 for c in classes}
    for toks, label in zip(tokens, train_df[label_col]):
        cls_docs[label] += 1
        arr = cls_word[label]
        for w in toks:
            j = vocab.get(w)
            if j is not None:
                arr[j] += 1
                cls_tot[label] += 1

    n_train = len(train_df)
    logprior = {c: math.log(cls_docs[c] / n_train) for c in classes}
    loglik = {c: np.log(cls_word[c] / (cls_tot[c] + V)) for c in classes}
    return {"vocab": vocab, "logprior": logprior, "loglik": loglik, "classes": classes}


def predict_tokens(model: dict, tokens: list[str]):
    """Predict the class with highest posterior log-probability for one tokenized doc.

    Ties favor the largest class label, matching the original script's
    binary tie-break (`s1 >= s0` favored the positive class).
    """
    vocab, logprior, loglik = model["vocab"], model["logprior"], model["loglik"]
    scores = dict(logprior)
    for w in tokens:
        j = vocab.get(w)
        if j is not None:
            for c in model["classes"]:
                scores[c] += loglik[c][j]
    return max(scores.items(), key=lambda kv: (kv[1], kv[0]))[0]


def predict(model: dict, text: str):
    return predict_tokens(model, tokenize(text))


def evaluate(
    model: dict,
    test_df: pd.DataFrame,
    text_col: str = "content",
    label_col: str = "label",
    tokens_col: str | None = None,
    positive_class=1,
) -> dict:
    """Confusion-matrix metrics for binary classification, plus macro-averaged
    precision/recall/F1 across all classes (the original script only ever
    reported metrics from the positive class's point of view).
    """
    tokens = test_df[tokens_col] if tokens_col else test_df[text_col].apply(tokenize)
    preds = np.array([predict_tokens(model, t) for t in tokens])
    y = test_df[label_col].to_numpy()

    classes = model["classes"]
    per_class = {}
    for c in classes:
        tp = int(((preds == c) & (y == c)).sum())
        fp = int(((preds == c) & (y != c)).sum())
        fn = int(((preds != c) & (y == c)).sum())
        tn = int(((preds != c) & (y != c)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[c] = {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "f1": f1,
        }

    accuracy = float((preds == y).mean()) if len(y) else 0.0
    macro_precision = sum(m["precision"] for m in per_class.values()) / len(classes)
    macro_recall = sum(m["recall"] for m in per_class.values()) / len(classes)
    macro_f1 = sum(m["f1"] for m in per_class.values()) / len(classes)

    pos = per_class[positive_class]
    return {
        "accuracy": accuracy,
        "precision": pos["precision"], "recall": pos["recall"], "f1": pos["f1"],
        "macro_precision": macro_precision, "macro_recall": macro_recall, "macro_f1": macro_f1,
        "confusion": {"TP": pos["tp"], "FP": pos["fp"], "FN": pos["fn"], "TN": pos["tn"]},
        "per_class": per_class,
        "preds": preds,
    }


def top_predictive_words(model: dict, k: int = 12, class_a=0, class_b=1):
    """Words ranked by log-likelihood ratio between two classes.

    Returns (top_a, top_b): words most indicative of class_a, then of class_b,
    each as a list of (word, ratio) tuples.
    """
    inv = {i: w for w, i in model["vocab"].items()}
    ratio = model["loglik"][class_a] - model["loglik"][class_b]
    order = np.argsort(ratio)
    top_a = [(inv[i], round(float(ratio[i]), 2)) for i in order[::-1][:k]]
    top_b = [(inv[i], round(float(-ratio[i]), 2)) for i in order[:k]]
    return top_a, top_b


def cross_validate(
    df: pd.DataFrame,
    text_col: str = "content",
    label_col: str = "label",
    k: int = 5,
    min_df: int = 5,
    seed: int = 42,
):
    """Stratified k-fold cross-validation.

    A single 80/20 split (the original approach) gives one noisy accuracy
    number; averaging over k folds gives a mean +/- std that is far more
    defensible in a report.
    """
    rng = np.random.RandomState(seed)
    df = df.reset_index(drop=True)
    df = df.assign(_tokens=df[text_col].apply(tokenize))

    fold_idx = np.zeros(len(df), dtype=int)
    for _, group in df.groupby(label_col):
        idx = rng.permutation(group.index.to_numpy())
        for fi, fold in enumerate(np.array_split(idx, k)):
            fold_idx[fold] = fi

    fold_metrics = []
    for fi in range(k):
        test_mask = fold_idx == fi
        train_df, test_df = df[~test_mask], df[test_mask]
        model = train_naive_bayes(train_df, label_col=label_col, min_df=min_df, tokens_col="_tokens")
        fold_metrics.append(evaluate(model, test_df, label_col=label_col, tokens_col="_tokens"))

    accs = [m["accuracy"] for m in fold_metrics]
    f1s = [m["macro_f1"] for m in fold_metrics]
    summary = {
        "k": k,
        "accuracy_mean": float(np.mean(accs)), "accuracy_std": float(np.std(accs)),
        "macro_f1_mean": float(np.mean(f1s)), "macro_f1_std": float(np.std(f1s)),
    }
    return fold_metrics, summary
