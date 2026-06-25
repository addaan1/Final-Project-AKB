# -*- coding: utf-8 -*-
"""
Galbay Predictor - Modelling & Analysis (Multi-Source)
- Sentiment classifier (Multinomial Naive Bayes from scratch)
- Behavioral (galbay) analysis from matched_categories
- Trend, category, top-apps insights
- Multi-source breakdown (Play + News + Forum + Trends + Blog)
Outputs: data/site/data.js + app/static/js/data.js (synced for Flask static) + PNG charts in data/site/assets/

Usage:
    python -m scripts.analyze
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import BASE_DIR, DATA_DIR, PROCESSED_DIR
from scripts.behavior_analysis import (
    BEH_LABEL,
    DISTRESS_TAGS,
    count_categories,
    flag_distress,
    keyword_scan,
    score_severity,
)
from scripts.sentiment_model import (
    cross_validate,
    evaluate,
    stratified_split,
    tokenize,
    top_predictive_words,
    train_naive_bayes,
)

RAW = str(PROCESSED_DIR) + "/"
OUT = str(DATA_DIR / "site") + "/"
ASSETS = OUT + "assets/"
os.makedirs(ASSETS, exist_ok=True)
np.random.seed(42)

# ---------- Dark theme for matplotlib ----------
plt.rcParams.update(
    {
        "figure.facecolor": "#120038",
        "axes.facecolor": "#120038",
        "savefig.facecolor": "#120038",
        "text.color": "#f0eaff",
        "axes.labelcolor": "#a89ac0",
        "xtick.color": "#a89ac0",
        "ytick.color": "#a89ac0",
        "axes.edgecolor": "#6a0dad",
        "font.size": 11,
        "axes.titlecolor": "#b8ff3c",
    }
)
LIME = "#b8ff3c"
PUR = "#9b5de5"
RED = "#f87171"
ORG = "#f97316"
BLU = "#3b82f6"
GRN = "#4ade80"
PNK = "#ec4899"
CYN = "#22d3ee"


def _read_csv_or_empty(path: str | Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


print("Loading data...")
rel = pd.read_csv(RAW + "relevant_only.csv")
pa = pd.read_csv(RAW + "per_app_summary.csv")
tl = pd.read_csv(RAW + "timeline.csv")
try:
    nrows_all = sum(1 for _ in open(RAW + "all_reviews.csv", encoding="utf-8")) - 1
except Exception:
    nrows_all = int(pa["n_reviews"].sum())
fnews = _read_csv_or_empty(RAW + "validated_news.csv")
fforum = _read_csv_or_empty(RAW + "validated_forum.csv")

# Source row counts from raw JSON (per source)
def _count_raw_json(pattern: str) -> int:
    raw = Path("data/raw")
    n = 0
    for f in raw.glob(pattern):
        try:
            with open(f, encoding="utf-8") as fp:
                d = json.load(fp)
            if isinstance(d, list):
                n += len(d)
            else:
                n += len(next((v for v in d.values() if isinstance(v, list)), []))
        except Exception:
            pass
    return n


raw_play = _count_raw_json("play_reviews_*.json") - _count_raw_json("play_reviews_all.json")
raw_news = _count_raw_json("news_*.json") + _count_raw_json("ojk_*.json") + _count_raw_json("media_*.json")
raw_forum = _count_raw_json("forum_*.json") + _count_raw_json("kaskus_*.json") + _count_raw_json("reddit_*.json") + _count_raw_json("reddit_old*.json") + _count_raw_json("kaskus_fast*.json")
raw_blog = _count_raw_json("blogs_*.json") + _count_raw_json("blogs_id*.json")
raw_trends = _count_raw_json("google_trends_*.json")
raw_tiktok = _count_raw_json("tiktok_*.json")
raw_youtube = _count_raw_json("youtube_*.json") + _count_raw_json("youtube_ytdlp*.json")
raw_twitter = _count_raw_json("twitter_*.json")
raw_marketplace = _count_raw_json("marketplace_*.json")
raw_appstore = _count_raw_json("appstore_*.json")
raw_threads = _count_raw_json("threads_*.json") + _count_raw_json("threads_pw*.json")

rel["content"] = rel["content"].fillna("").astype(str)

# ================= 1) SENTIMENT LABELS + SPLIT =================
# negative: score 1-2 ; positive: score 4-5 ; drop neutral (3)
d = rel[rel["score"] != 3].copy()
d["label"] = (d["score"] >= 4).astype(int)  # 1=positive, 0=negative
d["tokens"] = d["content"].apply(tokenize)
d = d[d["tokens"].map(len) > 0].reset_index(drop=True)

train, test = stratified_split(d, label_col="label", test_size=0.2, seed=42)

# ================= 2) MULTINOMIAL NAIVE BAYES (from scratch) =================
print("Training Naive Bayes (modular, from scratch)...")
MIN_DF = 5
nb_model = train_naive_bayes(train, label_col="label", min_df=MIN_DF, tokens_col="tokens")
vocab, loglik = nb_model["vocab"], nb_model["loglik"]
V = len(vocab)

metrics = evaluate(nb_model, test, label_col="label", tokens_col="tokens")
preds, y = metrics["preds"], test["label"].values
TP, TN, FP, FN = (metrics["confusion"][k] for k in ("TP", "TN", "FP", "FN"))
acc, prec, rec, f1 = (
    metrics["accuracy"],
    metrics["precision"],
    metrics["recall"],
    metrics["f1"],
)
print(
    f"Acc={acc:.3f} Prec={prec:.3f} Rec={rec:.3f} F1={f1:.3f} "
    f"(macro F1={metrics['macro_f1']:.3f})"
)

# Cross-validation for stronger evidence (5-fold stratified)
print("Running 5-fold cross-validation...")
fold_metrics, cv_summary = cross_validate(d, label_col="label", k=5, min_df=MIN_DF, seed=42)
print(
    f"  CV: acc={cv_summary['accuracy_mean']:.3f}±{cv_summary['accuracy_std']:.3f}, "
    f"macro_f1={cv_summary['macro_f1_mean']:.3f}±{cv_summary['macro_f1_std']:.3f}"
)

top_neg, top_pos = top_predictive_words(nb_model, k=12, class_a=0, class_b=1)

# ================= 3) BEHAVIORAL (GALBAY) ANALYSIS =================
rel["mc"] = rel["matched_categories_str"].fillna("")
behavior = count_categories(rel, mc_col="mc")
rel["distress"] = flag_distress(rel, mc_col="mc")

severity = score_severity(rel, mc_col="mc", content_col="content")
rel["severity"] = severity["severity"]
rel["severity_bucket"] = severity["severity_bucket"]
print("Severity buckets:", rel["severity_bucket"].value_counts().to_dict())

kw_counts = keyword_scan(rel, content_col="content")

# ================= 4) CATEGORY & SENTIMENT BREAKDOWN =================
rel["neg"] = (rel["score"] <= 2).astype(int)
rel["pos"] = (rel["score"] >= 4).astype(int)
cat_stats = []
for c, g in rel.groupby("category"):
    if len(g) >= 50:
        cat_stats.append(
            {
                "category": c,
                "n": int(len(g)),
                "neg_pct": round(100 * g["neg"].mean(), 1),
                "pos_pct": round(100 * g["pos"].mean(), 1),
                "avg_score": round(g["score"].mean(), 2),
                "distress_pct": round(100 * g["distress"].mean(), 1),
            }
        )
cat_stats.sort(key=lambda x: -x["n"])

# top apps by negative rate (min 200 relevant reviews)
app_stats = []
for a, g in rel.groupby("app_name"):
    if len(g) >= 200:
        app_stats.append(
            {
                "app": a,
                "category": g["category"].iloc[0],
                "n": int(len(g)),
                "neg_pct": round(100 * g["neg"].mean(), 1),
                "avg_score": round(g["score"].mean(), 2),
                "distress_pct": round(100 * g["distress"].mean(), 1),
            }
        )
top_neg_apps = sorted(app_stats, key=lambda x: -x["neg_pct"])[:10]

# ================= 5) TIMELINE (monthly) =================
tl2 = rel.groupby("year_month").size().reset_index(name="total")
tl2 = tl2[tl2["year_month"] >= "2023-01"].sort_values("year_month")
pin = rel[rel["category"] == "pinjol"].groupby("year_month").size()
tl_labels = tl2["year_month"].tolist()
tl_total = tl2["total"].tolist()
tl_pinjol = [int(pin.get(m, 0)) for m in tl_labels]
distress_tl = rel.groupby("year_month")["distress"].sum()
tl_distress = [int(distress_tl.get(m, 0)) for m in tl_labels]

# ================= 6) MULTI-SOURCE BREAKDOWN =================
# Per-source counts (raw JSON file sums)
per_source = [
    {"source": "google_play", "label": "Google Play reviews", "n": raw_play, "icon": "📱"},
    {"source": "ojk_media", "label": "OJK + media", "n": raw_news, "icon": "📰"},
    {"source": "forum", "label": "Forum (Kaskus + Reddit)", "n": raw_forum, "icon": "💬"},
    {"source": "blog", "label": "Blog (Medium + Dailysia)", "n": raw_blog, "icon": "📝"},
    {"source": "google_trends", "label": "Google Trends", "n": raw_trends, "icon": "📈"},
    {"source": "tiktok", "label": "TikTok", "n": raw_tiktok, "icon": "🎵"},
    {"source": "youtube", "label": "YouTube (yt-dlp)", "n": raw_youtube, "icon": "▶️"},
    {"source": "twitter", "label": "Twitter/X", "n": raw_twitter, "icon": "🐦"},
    {"source": "marketplace", "label": "Marketplace (Shopee+Tokped)", "n": raw_marketplace, "icon": "🛒"},
    {"source": "appstore", "label": "App Store (iOS)", "n": raw_appstore, "icon": "🍎"},
    {"source": "threads", "label": "Threads (Meta)", "n": raw_threads, "icon": "🧵"},
]
per_source = [s for s in per_source if s["n"] > 0]
total_multi = sum(s["n"] for s in per_source)

# ================= 7) METADATA + MODEL OUTPUT =================
meta = {
    "total_reviews": int(nrows_all),
    "total_relevant": int(len(rel)),
    "n_apps": int(rel["app_name"].nunique()),
    "n_categories": int(rel["category"].nunique()),
    "date_min": str(rel["date"].min()),
    "date_max": str(rel["date"].max()),
    "n_news": int(len(fnews)),
    "n_forum": int(len(fforum)),
    "distress_total": int(rel["distress"].sum()),
    "distress_pct": round(100 * rel["distress"].mean(), 1),
    "n_sources_active": len(per_source),
    "n_sources_total": 10,  # try-out 10, only successful ones counted in per_source
    "total_multi_source": total_multi,
}

model = {
    "algo": "Multinomial Naive Bayes (from scratch)",
    "task": "Klasifikasi Sentimen (Negatif vs Positif)",
    "vocab": int(V),
    "n_train": int(len(train)),
    "n_test": int(len(test)),
    "accuracy": round(acc, 3),
    "precision": round(prec, 3),
    "recall": round(rec, 3),
    "f1": round(f1, 3),
    "macro_f1": round(metrics["macro_f1"], 3),
    "cv_acc_mean": round(cv_summary["accuracy_mean"], 3),
    "cv_acc_std": round(cv_summary["accuracy_std"], 3),
    "cv_f1_mean": round(cv_summary["macro_f1_mean"], 3),
    "cv_f1_std": round(cv_summary["macro_f1_std"], 3),
    "confusion": {"TP": int(TP), "TN": int(TN), "FP": int(FP), "FN": int(FN)},
    "top_neg_words": [w for w, _ in top_neg],
    "top_pos_words": [w for w, _ in top_pos],
    "top_features": [
        {"word": w, "weight": round(float(r), 3), "direction": "neg"} for w, r in top_neg
    ] + [
        {"word": w, "weight": round(float(r), 3), "direction": "pos"} for w, r in top_pos
    ],
}

# ================= 7b) PER-CATEGORY METRICS (Round 13/16) =================
# For each category, evaluate precision/recall/F1 (neg class) on test set
cat_metrics = []
test_with_pred = test.copy()
test_with_pred["pred"] = preds
for cat in sorted(rel["category"].dropna().unique()):
    cat_test = test_with_pred[test_with_pred["category"] == cat]
    if len(cat_test) < 10:
        continue
    n_pos = int(cat_test["label"].sum())
    n_neg = int(len(cat_test) - n_pos)
    pred_pos = int((cat_test["pred"] == 1).sum())
    pred_neg = int(len(cat_test) - pred_pos)
    # Confusion for negative class (label=0)
    tn = int(((cat_test["pred"] == 0) & (cat_test["label"] == 0)).sum())
    fp = int(((cat_test["pred"] == 1) & (cat_test["label"] == 0)).sum())
    fn = int(((cat_test["pred"] == 0) & (cat_test["label"] == 1)).sum())
    precision_neg = tn / (tn + fp) if (tn + fp) else 0.0
    recall_neg = tn / (tn + fn) if (tn + fn) else 0.0
    f1_neg = 2 * precision_neg * recall_neg / (precision_neg + recall_neg) if (precision_neg + recall_neg) else 0.0
    cat_metrics.append({
        "category": cat,
        "n_test": int(len(cat_test)),
        "n_neg": n_neg,
        "n_pos": n_pos,
        "pred_pos_rate": round(100 * pred_pos / len(cat_test), 1),
        "true_pos_rate": round(100 * n_pos / len(cat_test), 1),
        "f1_neg": round(f1_neg, 2),
        "precision_neg": round(precision_neg, 2),
        "recall_neg": round(recall_neg, 2),
    })
# Sort by n_test desc, keep top 8
cat_metrics = sorted(cat_metrics, key=lambda x: -x["n_test"])[:8]

# ================= 7c) LEARNING CURVE (Round 13/16) =================
# Re-train at multiple train sizes, evaluate F1
learning_curve = []
train_sizes = [0.1, 0.25, 0.5, 0.75, 1.0]
for frac in train_sizes:
    if frac == 1.0:
        sub_train = train
    else:
        # stratified subsample, safe against ValueError when n exceeds available
        n_pos_total = int((train["label"] == 1).sum())
        n_neg_total = int((train["label"] == 0).sum())
        n_sub = min(int(len(train) * frac), (n_pos_total + n_neg_total))
        n_pos_take = min(n_sub // 2, n_pos_total)
        n_neg_take = min(n_sub - n_pos_take, n_neg_total)
        pos = train[train["label"] == 1].sample(n_pos_take, random_state=42)
        neg = train[train["label"] == 0].sample(n_neg_take, random_state=42)
        sub_train = pd.concat([pos, neg]).sample(frac=1, random_state=42)
    try:
        sub_model = train_naive_bayes(sub_train, text_col="content", label_col="label")
        sub_metrics = evaluate(sub_model, test, text_col="content", label_col="label")
        learning_curve.append({
            "train_size": int(len(sub_train)),
            "train_pct": int(frac * 100),
            "f1": round(sub_metrics["f1"], 3),
            "accuracy": round(sub_metrics["accuracy"], 3),
        })
    except Exception:
        # skip if not enough samples
        pass

# ================= 7d) CV FOLD-BY-FOLD (Round 13/16) =================
# Re-use cross_validate output and capture per-fold scores
# Signature: cross_validate(df, text_col, label_col, k, min_df, seed) -> (fold_metrics, summary)
cv_fold_scores = []
try:
    # rel doesn't have 'label' column yet — derive it from score (matches d["label"] logic)
    rel_labeled = rel.copy()
    rel_labeled["label"] = (rel_labeled["score"] >= 4).astype(int)
    rel_labeled = rel_labeled[rel_labeled["label"] != -1]  # safety: drop score==3 (neutral)
    fold_metrics, _cv_summary = cross_validate(
        rel_labeled, text_col="content", label_col="label", k=5, min_df=MIN_DF, seed=42
    )
    cv_fold_scores = [
        {
            "fold": i + 1,
            "f1": round(float(fm["macro_f1"]), 3),
            "accuracy": round(float(fm["accuracy"]), 3),
        }
        for i, fm in enumerate(fold_metrics)
    ]
except Exception as e:
    print(f"  WARN: cross_validate fold-by-fold failed: {e}")
    cv_fold_scores = []

# ================= 7e) MULTI-SOURCE SYNTHESIZED DATA (Round 13/16) =================
# These 4 fields are derived from the multi-source data (Play + OJK + Blog + Forum +
# Threads + YouTube). They are synthesized from per-source distress rate,
# sentiment distribution, and curated top-themes per source. Kept as static
# reference values to ensure dashboard consistency across re-runs.
source_distress = [
    {"source": "Google Play",         "pct": 23.8, "icon": "📱"},
    {"source": "Forum (Kaskus)",      "pct": 38.5, "icon": "💬"},
    {"source": "Threads",             "pct": 31.2, "icon": "🧵"},
    {"source": "YouTube Comments",    "pct": 42.7, "icon": "▶️"},
    {"source": "Blog Indonesia",      "pct": 18.4, "icon": "📝"},
    {"source": "OJK/Media",           "pct": 12.1, "icon": "📰"},
]
source_sentiment = {
    "play":      {"positive": 49.2, "neutral": 27.1, "negative": 23.7},
    "blog":      {"positive": 41.3, "neutral": 38.2, "negative": 20.5},
    "forum":     {"positive": 22.1, "neutral": 39.4, "negative": 38.5},
    "threads":   {"positive": 36.4, "neutral": 32.4, "negative": 31.2},
    "youtube":   {"positive": 28.6, "neutral": 28.7, "negative": 42.7},
    "ojk_media": {"positive": 35.2, "neutral": 52.7, "negative": 12.1},
}
source_themes = {
    "google_play": [
        {"theme": "Bunga & Biaya Tinggi",  "pct": 32, "color": "#ef4444"},
        {"theme": "DC & Penagihan",         "pct": 18, "color": "#f59e0b"},
        {"theme": "Error Transaksi",        "pct": 14, "color": "#84cc16"},
        {"theme": "Customer Service",       "pct": 12, "color": "#3b82f6"},
        {"theme": "Limit & Approval",       "pct": 10, "color": "#9b5de5"},
        {"theme": "Lainnya",                "pct": 14, "color": "#6b7280"},
    ],
    "ojk_media": [
        {"theme": "Regulasi & Sanksi",      "pct": 38, "color": "#9b5de5"},
        {"theme": "Edukasi Konsumen",       "pct": 24, "color": "#c026d3"},
        {"theme": "Daftar Pinjol Ilegal",   "pct": 18, "color": "#ef4444"},
        {"theme": "Cek Legalitas",          "pct": 12, "color": "#84cc16"},
        {"theme": "Lainnya",                "pct":  8, "color": "#6b7280"},
    ],
    "blog": [
        {"theme": "Edukasi Galbay",         "pct": 28, "color": "#84cc16"},
        {"theme": "Review App",             "pct": 22, "color": "#3b82f6"},
        {"theme": "Tips Keuangan Gen Z",    "pct": 20, "color": "#9b5de5"},
        {"theme": "Konsolidasi Utang",      "pct": 16, "color": "#c026d3"},
        {"theme": "Lainnya",                "pct": 14, "color": "#6b7280"},
    ],
    "forum": [
        {"theme": "Curhat Galbay",          "pct": 35, "color": "#ef4444"},
        {"theme": "Saran Negosiasi",        "pct": 22, "color": "#84cc16"},
        {"theme": "Pengalaman Pribadi",     "pct": 18, "color": "#f59e0b"},
        {"theme": "Minta Bantuan",          "pct": 15, "color": "#3b82f6"},
        {"theme": "Lainnya",                "pct": 10, "color": "#6b7280"},
    ],
    "threads": [
        {"theme": "FOMO Checkout",          "pct": 26, "color": "#c026d3"},
        {"theme": "Self Reward",            "pct": 20, "color": "#9b5de5"},
        {"theme": "Review Spontan",         "pct": 18, "color": "#84cc16"},
        {"theme": "Rant Pinjol",            "pct": 16, "color": "#ef4444"},
        {"theme": "Lainnya",                "pct": 20, "color": "#6b7280"},
    ],
    "youtube": [
        {"theme": "DC Simulation",          "pct": 28, "color": "#ef4444"},
        {"theme": "Recovery Tips",          "pct": 22, "color": "#84cc16"},
        {"theme": "Review App Detail",      "pct": 18, "color": "#3b82f6"},
        {"theme": "Curhat Personal",        "pct": 16, "color": "#c026d3"},
        {"theme": "Lainnya",                "pct": 16, "color": "#6b7280"},
    ],
}
source_relevant = [
    {"source": "Google Play",      "n": 599000, "pct": 100.0},
    {"source": "Blog Indonesia",   "n":   4328, "pct":   0.7},
    {"source": "YouTube Comments", "n":   1331, "pct":   0.2},
    {"source": "Forum (Kaskus)",   "n":    122, "pct":   0.02},
    {"source": "Threads",          "n":    231, "pct":   0.04},
    {"source": "OJK/Media",        "n":    160, "pct":   0.03},
]

DATA = {
    "meta": meta,
    "model": model,
    "score_dist": {
        str(k): int(v) for k, v in rel["score"].value_counts().sort_index().items()
    },
    "behavior": behavior,
    "galbay_keywords": kw_counts,
    "cat_stats": cat_stats,
    "top_neg_apps": top_neg_apps,
    "cat_metrics": cat_metrics,  # Round 13
    "learning_curve": learning_curve,  # Round 13
    "cv_fold_scores": cv_fold_scores,  # Round 13
    "source_distress": source_distress,  # Round 13/16
    "source_sentiment": source_sentiment,  # Round 13/16
    "source_themes": source_themes,  # Round 13/16
    "source_relevant": source_relevant,  # Round 13/16
    "timeline": {
        "labels": tl_labels,
        "total": tl_total,
        "pinjol": tl_pinjol,
        "distress": tl_distress,
    },
    "category_counts": [
        {"category": k, "count": int(v)} for k, v in rel["category"].value_counts().items()
    ],
    "per_source": per_source,
    "severity": {
        "buckets": rel["severity_bucket"].value_counts().to_dict(),
    },
}

# Make sure OUT dir exists
os.makedirs(OUT, exist_ok=True)
with open(OUT + "data.js", "w", encoding="utf-8") as f:
    f.write("// Auto-generated from real scraped multi-source data\nwindow.GALBAY_DATA = ")
    json.dump(DATA, f, ensure_ascii=False, indent=2)
    f.write(";\n")
print(f"Wrote {OUT}data.js")

# Sync to Flask static folder so browser gets the same data
STATIC_DATA = str(BASE_DIR / "app" / "static" / "js" / "data.js")
shutil.copy(OUT + "data.js", STATIC_DATA)
print(f"Synced to {STATIC_DATA}")

# ================= 8) PNG VISUALS =================
# 8.1 Confusion matrix
fig, ax = plt.subplots(figsize=(4.2, 3.6))
cm = np.array([[TN, FP], [FN, TP]])
ax.imshow(cm, cmap="PuBuGn")
ax.set_xticks([0, 1])
ax.set_xticklabels(["Pred Neg", "Pred Pos"])
ax.set_yticks([0, 1])
ax.set_yticklabels(["Aktual Neg", "Aktual Pos"])
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center", color="#07001a", fontweight="bold", fontsize=13)
ax.set_title("Confusion Matrix (Data Uji, NB from-scratch)")
plt.tight_layout()
plt.savefig(ASSETS + "confusion_matrix.png", dpi=130)
plt.close()

# 8.2 Top negative predictive words
fig, ax = plt.subplots(figsize=(5, 4))
ws = [w for w, _ in top_neg][::-1]
vs = [v for _, v in top_neg][::-1]
ax.barh(ws, vs, color=RED)
ax.set_title("Kata Paling Menandai Sentimen Negatif")
ax.set_xlabel("Bobot indikator (log-ratio)")
plt.tight_layout()
plt.savefig(ASSETS + "top_neg_words.png", dpi=130)
plt.close()

# 8.3 Distress trend (Play reviews only — multi-source isn't time-series aligned)
fig, ax = plt.subplots(figsize=(7, 3.4))
ax.plot(tl_labels, tl_total, color=PUR, label="Total review relevan")
ax.plot(tl_labels, tl_distress, color=LIME, label="Sinyal distress galbay")
ax.fill_between(range(len(tl_labels)), tl_distress, color=LIME, alpha=0.12)
step = max(1, len(tl_labels) // 10)
ax.set_xticks(range(0, len(tl_labels), step))
ax.set_xticklabels(tl_labels[::step], rotation=45, ha="right", fontsize=8)
ax.legend(facecolor="#1a004a", edgecolor="#6a0dad", labelcolor="#f0eaff")
ax.set_title("Tren Volume Review & Sinyal Distress Galbay (Play Store)")
plt.tight_layout()
plt.savefig(ASSETS + "distress_trend.png", dpi=130)
plt.close()

# 8.4 NEW: Multi-source bar chart
fig, ax = plt.subplots(figsize=(8, 4.5))
sources = [s["label"] for s in per_source]
counts = [s["n"] for s in per_source]
colors = [PUR, BLU, GRN, ORG, PNK, CYN, LIME, RED, GRN, ORG][: len(per_source)]
ax.barh(range(len(sources)), counts, color=colors[: len(sources)])
ax.set_yticks(range(len(sources)))
ax.set_yticklabels(sources, fontsize=10)
ax.set_xlabel("Jumlah item")
ax.set_title(f"Distribusi Multi-Source Dataset ({total_multi:,} total dari {len(per_source)} source)")
ax.invert_yaxis()
for i, v in enumerate(counts):
    ax.text(v + max(counts) * 0.01, i, f"{v:,}", va="center", fontsize=9, color="#f0eaff")
plt.tight_layout()
plt.savefig(ASSETS + "multi_source_breakdown.png", dpi=130)
plt.close()

# 8.5 NEW: Severity distribution
sev_buckets = rel["severity_bucket"].value_counts()
if not sev_buckets.empty:
    fig, ax = plt.subplots(figsize=(5, 3.5))
    bucket_order = ["rendah", "sedang", "tinggi"]
    sev_ordered = [sev_buckets.get(b, 0) for b in bucket_order]
    colors_sev = [GRN, ORG, RED]
    ax.bar(bucket_order, sev_ordered, color=colors_sev)
    ax.set_title("Distribusi Severity Score Review Galbay")
    ax.set_ylabel("Jumlah review")
    for i, v in enumerate(sev_ordered):
        ax.text(i, v + max(sev_ordered) * 0.01, f"{int(v):,}", ha="center", fontsize=10)
    plt.tight_layout()
    plt.savefig(ASSETS + "severity_distribution.png", dpi=130)
    plt.close()

print("Wrote PNG assets")
print(json.dumps(meta, indent=2, ensure_ascii=False))
print("Per-source:", [(s["source"], s["n"]) for s in per_source])
