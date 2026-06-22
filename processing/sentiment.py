"""Sentiment analysis using VADER (NLTK).

Sentiment outputs are written under data/processed/advanced/ so the main
processed folder remains focused on the curated analysis package.

Penggunaan:
    python -m processing.sentiment
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm

from config import PROCESSED_DIR, RAW_DIR

log = logging.getLogger("processing.sentiment")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

sia = SentimentIntensityAnalyzer()


def analyze_sentiment(texts: list[str]) -> list[dict]:
    """Analyze sentiment for a batch of texts."""
    results = []
    for text in tqdm(texts, desc="Sentiment analysis"):
        if not text or not isinstance(text, str):
            results.append(
                {
                    "sentiment_pos": 0,
                    "sentiment_neg": 0,
                    "sentiment_neu": 0,
                    "sentiment_compound": 0,
                    "sentiment_label": "neutral",
                }
            )
            continue
        scores = sia.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"
        results.append(
            {
                "sentiment_pos": round(scores["pos"], 4),
                "sentiment_neg": round(scores["neg"], 4),
                "sentiment_neu": round(scores["neu"], 4),
                "sentiment_compound": round(compound, 4),
                "sentiment_label": label,
            }
        )
    return results


def main(argv=None):
    out = Path(PROCESSED_DIR)
    out.mkdir(parents=True, exist_ok=True)
    advanced_out = out / "advanced"
    advanced_out.mkdir(parents=True, exist_ok=True)

    results = {}

    reviews_path = Path(RAW_DIR) / "play_reviews_all.json"
    if reviews_path.exists():
        with reviews_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        reviews = data.get("reviews", [])
        if reviews:
            df = pd.DataFrame(reviews)
            texts = df["content"].fillna("").tolist()
            sentiments = analyze_sentiment(texts)
            for i, sentiment in enumerate(sentiments):
                df.loc[df.index[i], list(sentiment.keys())] = list(sentiment.values())
            df.to_csv(advanced_out / "reviews_with_sentiment.csv", index=False, encoding="utf-8")
            results["reviews"] = {
                "total": len(df),
                "positive": int((df["sentiment_label"] == "positive").sum()),
                "negative": int((df["sentiment_label"] == "negative").sum()),
                "neutral": int((df["sentiment_label"] == "neutral").sum()),
            }

    tiktok_path = Path(RAW_DIR) / "tiktok_comments.json"
    if tiktok_path.exists():
        with tiktok_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        comments = data.get("comments", [])
        if comments:
            df = pd.DataFrame(comments)
            texts = df["text"].fillna("").tolist()
            sentiments = analyze_sentiment(texts)
            for i, sentiment in enumerate(sentiments):
                df.loc[df.index[i], list(sentiment.keys())] = list(sentiment.values())
            df.to_csv(advanced_out / "tiktok_with_sentiment.csv", index=False, encoding="utf-8")
            results["tiktok"] = {"total": len(df)}

    twitter_path = Path(RAW_DIR) / "twitter_tweets.json"
    if twitter_path.exists():
        with twitter_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        tweets = data.get("tweets", [])
        if tweets:
            df = pd.DataFrame(tweets)
            texts = df["text"].fillna("").tolist()
            sentiments = analyze_sentiment(texts)
            for i, sentiment in enumerate(sentiments):
                df.loc[df.index[i], list(sentiment.keys())] = list(sentiment.values())
            df.to_csv(advanced_out / "twitter_with_sentiment.csv", index=False, encoding="utf-8")
            results["twitter"] = {"total": len(df)}

    print("\n=== SENTIMENT RESULTS ===")
    for key, value in results.items():
        print(f"  {key:15s}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
