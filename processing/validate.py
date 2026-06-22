"""Data validation & deduplication.

Menghapus duplikat berdasarkan ID unik per source, validasi field required,
handle missing data. Hanya validasi in-memory, tidak menyimpan CSV.

Penggunaan:
    python -m processing.validate
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd
from config import RAW_DIR, PROCESSED_DIR

log = logging.getLogger("processing.validate")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def validate_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Validasi & dedup review Google Play."""
    initial = len(df)
    df = df.dropna(subset=["content"])
    df = df[df["content"].str.strip().str.len() > 0]
    if "review_id" in df.columns:
        df = df.drop_duplicates(subset=["review_id"], keep="first")
    if "at" in df.columns:
        df = df.dropna(subset=["at"])
    log.info("Reviews: %d -> %d (removed %d invalid/duplicate)", initial, len(df), initial - len(df))
    return df


def validate_tiktok(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip().str.len() > 0]
    if "comment_id" in df.columns:
        df = df.drop_duplicates(subset=["comment_id"], keep="first")
    log.info("TikTok: %d -> %d", initial, len(df))
    return df


def validate_forum(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    if "source" in df.columns:
        kaskus = df[df["source"] == "kaskus"]
        reddit = df[df["source"] == "reddit"]
        if "url" in kaskus.columns:
            kaskus = kaskus.drop_duplicates(subset=["url"], keep="first")
        if "post_id" in reddit.columns:
            reddit = reddit.drop_duplicates(subset=["post_id"], keep="first")
        df = pd.concat([kaskus, reddit], ignore_index=True)
    log.info("Forum: %d -> %d", initial, len(df))
    return df


def validate_twitter(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.strip().str.len() > 0]
    if "tweet_url" in df.columns:
        df = df.drop_duplicates(subset=["tweet_url"], keep="first")
    log.info("Twitter: %d -> %d", initial, len(df))
    return df


def validate_news(df: pd.DataFrame) -> pd.DataFrame:
    initial = len(df)
    df = df.dropna(subset=["title"])
    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"], keep="first")
    log.info("News: %d -> %d", initial, len(df))
    return df


def main(argv=None):
    out = Path(PROCESSED_DIR)
    out.mkdir(parents=True, exist_ok=True)

    results = {}

    # Reviews — validasi saja, tidak simpan CSV (sudah ada di sentiment.py)
    reviews_path = Path(RAW_DIR) / "play_reviews_all.json"
    if reviews_path.exists():
        with reviews_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("reviews", []))
        if not df.empty:
            df = validate_reviews(df)
            results["reviews"] = len(df)

    # TikTok
    tiktok_path = Path(RAW_DIR) / "tiktok_comments.json"
    if tiktok_path.exists():
        with tiktok_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("comments", []))
        if not df.empty:
            df = validate_tiktok(df)
            results["tiktok"] = len(df)

    # Forum
    forum_path = Path(RAW_DIR) / "forum_all.json"
    if forum_path.exists():
        with forum_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("all", []))
        if not df.empty:
            df = validate_forum(df)
            results["forum"] = len(df)

    # Twitter
    twitter_path = Path(RAW_DIR) / "twitter_tweets.json"
    if twitter_path.exists():
        with twitter_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("tweets", []))
        if not df.empty:
            df = validate_twitter(df)
            results["twitter"] = len(df)

    # News
    news_path = Path(RAW_DIR) / "news_all.json"
    if news_path.exists():
        with news_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        df = pd.DataFrame(data.get("all", []))
        if not df.empty:
            df = validate_news(df)
            results["news"] = len(df)

    print("\n=== VALIDATION RESULTS (in-memory, no CSV saved) ===")
    for k, v in results.items():
        print(f"  {k:15s}: {v} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
