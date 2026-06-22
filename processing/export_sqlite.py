"""Export semua data ke SQLite database.

Tabel:
- reviews, tiktok_comments, kaskus_threads, reddit_posts,
  twitter_tweets, ojk_news, media_news

Penggunaan:
    python -m processing.export_sqlite
"""
from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

import pandas as pd
from config import RAW_DIR, PROCESSED_DIR

log = logging.getLogger("processing.export_sqlite")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

DB_PATH = Path(PROCESSED_DIR) / "galbay.db"


def load_json(path: Path, key: str) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(key, [])


def df_to_sqlite(df: pd.DataFrame, table: str, conn: sqlite3.Connection):
    if df.empty:
        log.warning("Empty DataFrame for table %s, skip", table)
        return
    # Convert list/dict columns to JSON strings for SQLite compatibility
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x)
    df.to_sql(table, conn, if_exists="replace", index=False)
    log.info("  %s: %d rows", table, len(df))


def main(argv=None):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))
    log.info("Creating SQLite DB: %s", DB_PATH)

    # Reviews
    reviews = load_json(Path(RAW_DIR) / "play_reviews_all.json", "reviews")
    if reviews:
        df_to_sqlite(pd.DataFrame(reviews), "reviews", conn)

    # TikTok
    for key, table in [("comments", "tiktok_comments"), ("videos", "tiktok_videos")]:
        data = load_json(Path(RAW_DIR) / f"tiktok_{key}.json", key)
        if data:
            df_to_sqlite(pd.DataFrame(data), table, conn)

    # Forum
    forum_all = load_json(Path(RAW_DIR) / "forum_all.json", "all")
    if forum_all:
        df = pd.DataFrame(forum_all)
        kaskus = df[df.get("source") == "kaskus"] if "source" in df.columns else df
        reddit = df[df.get("source") == "reddit"] if "source" in df.columns else pd.DataFrame()
        if not kaskus.empty:
            df_to_sqlite(kaskus, "kaskus_threads", conn)
        if not reddit.empty:
            df_to_sqlite(reddit, "reddit_posts", conn)

    # Twitter
    tweets = load_json(Path(RAW_DIR) / "twitter_tweets.json", "tweets")
    if tweets:
        df_to_sqlite(pd.DataFrame(tweets), "twitter_tweets", conn)

    # News
    ojk = load_json(Path(RAW_DIR) / "ojk_articles.json", "ojk")
    media = load_json(Path(RAW_DIR) / "media_articles.json", "media")
    if ojk:
        df_to_sqlite(pd.DataFrame(ojk), "ojk_news", conn)
    if media:
        df_to_sqlite(pd.DataFrame(media), "media_news", conn)

    conn.close()

    size_kb = DB_PATH.stat().st_size / 1e3
    print(f"\n=== SQLite DB: {DB_PATH} ({size_kb:.1f} KB) ===")
    conn2 = sqlite3.connect(str(DB_PATH))
    cursor = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (name,) in cursor:
        cnt = conn2.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
        print(f"  {name:25s}: {cnt} rows")
    conn2.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
