# -*- coding: utf-8 -*-
"""
Galbay Predictor - Modelling & Analysis (Multi-Source)
- Sentiment classifier (Multinomial Naive Bayes from scratch)
- Behavioral (galbay) analysis from matched_categories
- Trend, category, top-apps insights
- Multi-source breakdown (Play + News + Forum + Trends + Blog)
Outputs: data/site/data.js + PNG charts in data/site/assets/

Usage:
    python -m scripts.analyze
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DATA_DIR, PROCESSED_DIR
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
raw_forum = _count_raw_json("forum_*.json") + _count_raw_json("kaskus_*.json") + _count_raw_json("reddit_*.json")
raw_blog = _count_raw_json("blogs_*.json")
raw_trends = _count_raw_json("google_trends_*.json")
raw_tiktok = _count_raw_json("tiktok_*.json")
raw_youtube = _count_raw_json("youtube_*.json")
raw_twitter = _count_raw_json("twitter_*.json")
raw_marketplace = _count_raw_json("marketplace_*.json")
raw_appstore = _count_raw_json("appstore_*.json")

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
    {"source": "youtube", "label": "YouTube", "n": raw_youtube, "icon": "▶️"},
    {"source": "twitter", "label": "Twitter/X", "n": raw_twitter, "icon": "🐦"},
    {"source": "marketplace", "label": "Marketplace (Shopee+Tokped)", "n": raw_marketplace, "icon": "🛒"},
    {"source": "appstore", "label": "App Store (iOS)", "n": raw_appstore, "icon": "🍎"},
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
    "top_pos_words": [w for w, _ in top_neg[::-1]],  # reverse for display
}

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
