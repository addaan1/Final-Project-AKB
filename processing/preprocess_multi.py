"""Preprocessing multi-source → CSV (kolom penting saja di data/processed/).

Output CSV per source (filter kolom relevan untuk modeling & dashboard):
1. play_reviews_clean.csv     — query, app_name, category, score, content, date, is_relevant
2. ojk_media_articles.csv     — source, title, content, url
3. forum_threads.csv          — query, title, url
4. blogs_id_posts.csv         — blog, query, title, url
5. youtube_videos.csv         — query, title, channel, video_id, view_count, like_count
6. youtube_comments.csv       — query, video_title, author, text, like_count
7. threads_posts.csv          — query, text
8. google_trends.csv          — date, galbay, paylater, pinjol, tagihan, dll (5y)
9. multi_source_combined.csv  — semua source dalam 1 tabel unified

Etika:
- Hanya data publik yang sudah ada di data/raw/.
- Tidak ada PII (username sudah di-redact di scraper).
- Kolom yang tidak relevan (internal flag, dll) di-drop.

Usage:
    python -m processing.preprocess_multi
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import PROCESSED_DIR, RAW_DIR

log = logging.getLogger("processing.preprocess_multi")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log.warning("Gagal baca %s: %s", path.name, exc)
        return None


def preprocess_play() -> pd.DataFrame:
    """Ambil play_reviews_all.json, keep kolom penting."""
    path = Path(RAW_DIR) / "play_reviews_all.json"
    d = _load_json(path)
    if not d or not isinstance(d, dict):
        log.warning("play_reviews_all.json tidak ada / format salah")
        return pd.DataFrame()

    rows = d.get("reviews", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Normalize: 'at' (ISO timestamp) -> 'date' (YYYY-MM-DD) + 'year_month'
    if "at" in df.columns and "date" not in df.columns:
        df["at_parsed"] = pd.to_datetime(df["at"], errors="coerce", utc=True)
        df["date"] = df["at_parsed"].dt.strftime("%Y-%m-%d")
        df["year_month"] = df["at_parsed"].dt.strftime("%Y-%m")
        df = df.drop(columns=["at_parsed"], errors="ignore")

    # matched_categories (list) -> matched_categories_str (str)
    if "matched_categories" in df.columns and "matched_categories_str" not in df.columns:
        df["matched_categories_str"] = df["matched_categories"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else ""
        )

    keep_cols = [
        "query", "app_name", "category", "score", "content",
        "date", "year_month", "is_relevant", "matched_categories_str",
        "n_matched_categories", "thumbs_up", "version",
    ]
    df = df[[c for c in keep_cols if c in df.columns]].copy()
    df["source"] = "google_play"
    log.info("play: %d baris (columns: %s)", len(df), list(df.columns))
    return df


def preprocess_ojk_media() -> pd.DataFrame:
    """OJK + media articles — kolom penting: source, title, content, url.

    Schema files: {meta, all} untuk news_all.json, {meta, media} untuk
    media_articles.json, {meta, ojk} untuk ojk_articles.json.
    """
    rows: list[dict] = []
    seen_keys = ("articles", "all", "media", "ojk", "news")
    for f in sorted(Path(RAW_DIR).glob("ojk_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for a in items:
            rows.append(
                {
                    "source": f.stem,
                    "title": a.get("title", "")[:300],
                    "content": a.get("content", "")[:2000],
                    "url": a.get("url", ""),
                    "scraped_at": a.get("scraped_at", ""),
                }
            )
    for f in sorted(Path(RAW_DIR).glob("news_*.json")) + sorted(Path(RAW_DIR).glob("media_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for a in items:
            rows.append(
                {
                    "source": f.stem,
                    "title": a.get("title", "")[:300],
                    "content": a.get("content", "")[:2000],
                    "url": a.get("url", ""),
                    "scraped_at": a.get("scraped_at", ""),
                }
            )
    df = pd.DataFrame(rows)
    log.info("ojk_media: %d baris", len(df))
    return df


def preprocess_forum() -> pd.DataFrame:
    """Forum (Kaskus + Reddit) — kolom penting: source, query, title, url.

    Schema files: {meta, all|kaskus} untuk Kaskus, {meta, posts} untuk Reddit.
    """
    rows: list[dict] = []
    seen_keys = ("all", "kaskus", "threads", "posts", "reddit")
    for f in sorted(Path(RAW_DIR).glob("kaskus_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for t in items:
            rows.append(
                {
                    "source": f.stem,
                    "platform": "kaskus",
                    "query": t.get("query", ""),
                    "title": t.get("title", "")[:300],
                    "url": t.get("url", ""),
                    "scraped_at": t.get("scraped_at", ""),
                }
            )
    for f in sorted(Path(RAW_DIR).glob("reddit_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for p in items:
            rows.append(
                {
                    "source": f.stem,
                    "platform": "reddit",
                    "query": p.get("query", ""),
                    "title": p.get("title", "")[:300],
                    "url": p.get("url", ""),
                    "scraped_at": p.get("scraped_at", ""),
                }
            )
    for f in sorted(Path(RAW_DIR).glob("forum_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for k in items:
            rows.append(
                {
                    "source": f.stem,
                    "platform": "kaskus_or_reddit",
                    "query": k.get("query", ""),
                    "title": k.get("title", "")[:300],
                    "url": k.get("url", ""),
                    "scraped_at": k.get("scraped_at", ""),
                }
            )
    df = pd.DataFrame(rows)
    log.info("forum: %d baris", len(df))
    return df


def preprocess_blogs() -> pd.DataFrame:
    """Blog (Medium + Blog ID) — kolom penting: blog, query, title, url."""
    rows: list[dict] = []
    seen_keys = ("posts", "blog")
    for f in sorted(Path(RAW_DIR).glob("blogs_*.json")) + sorted(Path(RAW_DIR).glob("blogs_id*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = next((d[k] for k in seen_keys if isinstance(d.get(k), list)), [])
        for p in items:
            rows.append(
                {
                    "source": f.stem,
                    "blog": p.get("blog", p.get("source", "")),
                    "query": p.get("query", ""),
                    "title": p.get("title", "")[:300],
                    "url": p.get("url", ""),
                    "scraped_at": p.get("scraped_at", ""),
                }
            )
    df = pd.DataFrame(rows)
    log.info("blogs: %d baris", len(df))
    return df


def preprocess_youtube() -> tuple[pd.DataFrame, pd.DataFrame]:
    """YouTube — pisah videos & comments."""
    rows_v: list[dict] = []
    rows_c: list[dict] = []
    for f in sorted(Path(RAW_DIR).glob("youtube_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        for v in d.get("videos", []):
            rows_v.append(
                {
                    "source": f.stem,
                    "query": v.get("query", ""),
                    "title": v.get("title", "")[:300],
                    "channel": v.get("channel", ""),
                    "video_id": v.get("video_id", ""),
                    "url": v.get("url", ""),
                    "duration_sec": v.get("duration", 0),
                    "view_count": v.get("view_count", 0),
                    "like_count": v.get("like_count", 0),
                    "upload_date": v.get("upload_date", ""),
                    "scraped_at": v.get("scraped_at", ""),
                }
            )
        for c in d.get("comments", []):
            rows_c.append(
                {
                    "source": f.stem,
                    "query": c.get("query", ""),
                    "video_id": c.get("video_id", ""),
                    "video_title": c.get("video_title", "")[:200],
                    "author": c.get("author", ""),
                    "text": str(c.get("text", ""))[:1000],
                    "like_count": c.get("like_count", 0),
                    "scraped_at": c.get("scraped_at", ""),
                }
            )
    df_v = pd.DataFrame(rows_v)
    df_c = pd.DataFrame(rows_c)
    log.info("youtube: %d videos, %d comments", len(df_v), len(df_c))
    return df_v, df_c


def preprocess_threads() -> pd.DataFrame:
    """Threads (Meta) — kolom penting: query, text, url."""
    rows: list[dict] = []
    for f in sorted(Path(RAW_DIR).glob("threads_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        items = d.get("posts", [])
        for p in items:
            rows.append(
                {
                    "source": f.stem,
                    "query": p.get("query", ""),
                    "username_hash": p.get("username_hash", ""),
                    "text": p.get("text", "")[:1000],
                    "url": p.get("url", ""),
                    "scraped_at": p.get("scraped_at", ""),
                }
            )
    df = pd.DataFrame(rows)
    log.info("threads: %d baris", len(df))
    return df


def preprocess_trends() -> pd.DataFrame:
    """Google Trends — keep kolom date + semua keyword + label."""
    rows: list[dict] = []
    for f in sorted(Path(RAW_DIR).glob("google_trends_*.json")):
        d = _load_json(f)
        if not d or not isinstance(d, dict):
            continue
        for r in d.get("trends", []):
            rows.append(
                {
                    "source": f.stem,
                    "date": str(r.get("date", ""))[:10],
                    "label": r.get("label", ""),
                    **{k: v for k, v in r.items() if k not in ("date", "label", "isPartial")},
                }
            )
    df = pd.DataFrame(rows)
    log.info("trends: %d baris", len(df))
    return df


def build_multi_source_combined(
    play: pd.DataFrame,
    ojk: pd.DataFrame,
    forum: pd.DataFrame,
    blogs: pd.DataFrame,
    yt_v: pd.DataFrame,
    yt_c: pd.DataFrame,
    threads: pd.DataFrame,
    trends: pd.DataFrame,
) -> pd.DataFrame:
    """Bangun tabel unified: source, type, query/text/title, url.

    Kolom utama yang akan dipakai di modeling & dashboard.
    """
    frames: list[pd.DataFrame] = []

    if not play.empty:
        f = play[["source", "query", "app_name", "category", "content", "date", "is_relevant"]].copy()
        f = f.rename(columns={"content": "text", "app_name": "meta", "is_relevant": "flag"})
        f["type"] = "play_review"
        f["title"] = ""
        f["url"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])
        # Note: for combined, we sample to keep file manageable (< 200K rows)
        if len(f) > 100_000:
            f = pd.concat([f.head(50_000), f.tail(50_000)], ignore_index=True)
        frames[-1] = f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]]

    if not ojk.empty:
        f = ojk[["source", "title", "content", "url"]].copy()
        f["type"] = "news_article"
        f["query"] = ""
        f["text"] = f["content"]
        f["meta"] = ""
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not forum.empty:
        f = forum[["source", "query", "title", "url"]].copy()
        f["type"] = "forum_thread"
        f["text"] = ""
        f["meta"] = ""
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not blogs.empty:
        f = blogs[["source", "blog", "query", "title", "url"]].copy()
        f["type"] = "blog_post"
        f["text"] = ""
        f["meta"] = f["blog"]
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not yt_v.empty:
        f = yt_v[["source", "query", "title", "channel", "view_count"]].copy()
        f["type"] = "youtube_video"
        f["text"] = ""
        f["url"] = ""
        f["meta"] = f["channel"]
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not yt_c.empty:
        f = yt_c[["source", "query", "video_title", "text", "like_count"]].copy()
        f["type"] = "youtube_comment"
        f["title"] = f["video_title"]
        f["url"] = ""
        f["meta"] = ""
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not threads.empty:
        f = threads[["source", "query", "text", "url"]].copy()
        f["type"] = "threads_post"
        f["title"] = ""
        f["meta"] = ""
        f["category"] = ""
        f["date"] = pd.NA
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not trends.empty:
        f = trends[["source", "date", "label"]].copy()
        f["type"] = "google_trends"
        f["query"] = f["label"]
        f["title"] = f["label"]
        f["text"] = ""
        f["url"] = ""
        f["meta"] = ""
        f["category"] = ""
        f["flag"] = ""
        frames.append(f[["source", "type", "query", "title", "text", "url", "meta", "category", "date", "flag"]])

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    return combined


def main(argv=None):
    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

    log.info("=== PREPROCESS MULTI-SOURCE ===")
    play = preprocess_play()
    ojk = preprocess_ojk_media()
    forum = preprocess_forum()
    blogs = preprocess_blogs()
    yt_v, yt_c = preprocess_youtube()
    threads = preprocess_threads()
    trends = preprocess_trends()

    # Save per-source CSV (kolom penting)
    outputs: list[tuple[str, pd.DataFrame]] = [
        ("play_reviews_clean", play),
        ("ojk_media_articles", ojk),
        ("forum_threads", forum),
        ("blogs_id_posts", blogs),
        ("youtube_videos", yt_v),
        ("youtube_comments", yt_c),
        ("threads_posts", threads),
        ("google_trends", trends),
    ]

    print("\n=== PER-SOURCE CSV ===")
    for name, df in outputs:
        if df.empty:
            print(f"  {name:25s} EMPTY")
            continue
        path = Path(PROCESSED_DIR) / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  {name:25s} {len(df):>10,} rows  {size_kb:>8.1f} KB")

    # Multi-source combined
    combined = build_multi_source_combined(play, ojk, forum, blogs, yt_v, yt_c, threads, trends)
    if not combined.empty:
        path = Path(PROCESSED_DIR) / "multi_source_combined.csv"
        combined.to_csv(path, index=False, encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  {'multi_source_combined':25s} {len(combined):>10,} rows  {size_kb:>8.1f} KB")

    # Per-source summary
    total = sum(len(df) for _, df in outputs)
    print(f"\n  {'TOTAL (per-source CSV)':25s} {total:>10,} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
