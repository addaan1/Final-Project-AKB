"""Visualization: matplotlib/seaborn charts.

Output ke data/processed/charts/:
- top_keywords.png
- sentiment_distribution.png
- timeline_monthly.png
- score_distribution.png
- relevant_rate_by_category.png

Penggunaan:
    python -m processing.visualize
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from config import RAW_DIR, PROCESSED_DIR
from scraper.fintech_reviews import GALBAY_KEYWORDS

log = logging.getLogger("processing.visualize")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

CHARTS_DIR = Path(PROCESSED_DIR) / "charts"


def plot_top_keywords(df: pd.DataFrame, out_path: Path, top_n: int = 20):
    """Bar chart: top N keyword frequency."""
    rows = []
    for cat, kws in GALBAY_KEYWORDS.items():
        for kw in kws:
            n = int(df["content"].fillna("").str.lower().str.contains(kw, regex=False).sum())
            rows.append({"keyword": kw, "count": n, "category": cat})
    freq = pd.DataFrame(rows).sort_values("count", ascending=False).head(top_n)

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=freq, x="count", y="keyword", hue="category", palette="Reds_r", ax=ax, legend=False)
    ax.set_title(f"Top {top_n} Keyword Galbay Frequency", fontsize=14, fontweight="bold")
    ax.set_xlabel("Occurrence Count")
    ax.set_ylabel("")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Saved %s", out_path)


def plot_sentiment_distribution(df: pd.DataFrame, out_path: Path):
    """Pie chart: sentiment distribution."""
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()
    labels = []
    for text in df["content"].fillna("")[:5000]:
        score = sia.polarity_scores(str(text))["compound"]
        if score >= 0.05:
            labels.append("positive")
        elif score <= -0.05:
            labels.append("negative")
        else:
            labels.append("neutral")
    counts = pd.Series(labels).value_counts()

    fig, ax = plt.subplots(figsize=(8, 8))
    colors = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}
    ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%",
           colors=[colors.get(l, "#333") for l in counts.index], startangle=90)
    ax.set_title("Sentiment Distribution (sample 5000 reviews)", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Saved %s", out_path)


def plot_timeline(df: pd.DataFrame, out_path: Path):
    """Line chart: review count per month."""
    if "at" not in df.columns:
        return
    df2 = df.copy()
    df2["at"] = pd.to_datetime(df2["at"], errors="coerce", utc=True)
    df2["year_month"] = df2["at"].dt.to_period("M")
    monthly = df2.groupby("year_month").size().reset_index(name="count")
    monthly["year_month"] = monthly["year_month"].astype(str)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(monthly["year_month"], monthly["count"], marker="o", color="#e74c3c", linewidth=2)
    ax.set_title("Review Timeline (Monthly)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel("Review Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Saved %s", out_path)


def plot_score_distribution(df: pd.DataFrame, out_path: Path):
    """Stacked bar chart: score distribution per app."""
    ct = pd.crosstab(df["query"], df["score"])
    fig, ax = plt.subplots(figsize=(14, 6))
    ct.plot(kind="bar", stacked=True, ax=ax, colormap="RdYlGn")
    ax.set_title("Score Distribution per App", fontsize=14, fontweight="bold")
    ax.set_xlabel("App")
    ax.set_ylabel("Review Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Saved %s", out_path)


def plot_relevant_rate(df: pd.DataFrame, out_path: Path):
    """Bar chart: relevant rate per category."""
    if "category" not in df.columns or "is_relevant" not in df.columns:
        return
    g = df.groupby("category").agg(
        total=("is_relevant", "count"),
        relevant=("is_relevant", "sum"),
    ).reset_index()
    g["rate"] = (g["relevant"] / g["total"] * 100).round(2)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=g, x="category", y="rate", palette="Reds_r", ax=ax)
    ax.set_title("Galbay Relevant Rate by App Category", fontsize=14, fontweight="bold")
    ax.set_xlabel("Category")
    ax.set_ylabel("Relevant Rate (%)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    log.info("Saved %s", out_path)


def main(argv=None):
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    reviews_path = Path(RAW_DIR) / "play_reviews_all.json"
    if not reviews_path.exists():
        log.error("No reviews data found at %s", reviews_path)
        return 1

    with reviews_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data.get("reviews", []))
    if df.empty:
        log.error("No reviews to visualize")
        return 1

    plot_top_keywords(df, CHARTS_DIR / "top_keywords.png")
    plot_sentiment_distribution(df, CHARTS_DIR / "sentiment_distribution.png")
    plot_timeline(df, CHARTS_DIR / "timeline_monthly.png")
    plot_score_distribution(df, CHARTS_DIR / "score_distribution.png")
    plot_relevant_rate(df, CHARTS_DIR / "relevant_rate_by_category.png")

    print(f"\n=== CHARTS SAVED to {CHARTS_DIR} ===")
    for f in sorted(CHARTS_DIR.glob("*.png")):
        print(f"  {f.name:40s} {f.stat().st_size/1e3:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
