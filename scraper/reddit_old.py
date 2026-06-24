"""Scraper Reddit via old.reddit.com JSON endpoint (no auth, posts only).

Simplified version: no comments fetch (avoid 429 rate-limit), save per-subreddit.
Target: 10K+ posts from 3 subreddit × 20 query × 25 posts = ~1.5K posts per batch.

Output schema per post:
    {
        "source": "reddit",
        "query": str,
        "subreddit": str,
        "title": str,
        "selftext": str,
        "url": str,
        "author": str,        # hash, PII redacted
        "score": int,
        "num_comments": int,
        "created_utc": float,
        "is_self": bool,
        "scraped_at": float,
    }
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.reddit_old")

REDDIT_QUERIES: list[str] = [
    "paylater", "pinjol", "galbay", "gagal bayar", "utang", "ditagih",
    "cicilan", "self reward", "FOMO", "checkout", "bunga tinggi",
    "debt collector", "tagihan", "kartu kredit", "kredit",
    "pinjaman online", "shopee paylater", "kredivo", "indodana",
    "akulaku",
]

REDDIT_SUBREDDITS: list[str] = [
    "indonesia", "finansial", "personalfinance",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GalbayScraper/1.0; +https://galbay.id)"
    ),
}


def _redact(text: str) -> str:
    if not text:
        return "anon"
    return hashlib.sha256(text.encode()).hexdigest()[:12]


class RedditOldScraper(BaseScraper):
    name = "reddit_old"

    def _fetch(self, url: str) -> dict | None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                log.warning("Reddit 429 (rate-limited)")
                time.sleep(5)
                return None
            log.warning("Reddit %d for %s", r.status_code, url[:60])
        except Exception as exc:
            log.warning("Reddit fetch error: %s", exc)
        return None

    def _scrape_query(
        self, subreddit: str, query: str, max_pages: int = 1
    ) -> list[dict]:
        """Scrape subreddit search. Return posts only (no comments for speed)."""
        posts: list[dict] = []
        after: str | None = None

        for page in range(max_pages):
            params = {
                "q": query,
                "sort": "relevance",
                "restrict_sr": "on",
                "t": "all",
                "limit": 100,  # max per page
            }
            if after:
                params["after"] = after

            url = f"https://old.reddit.com/r/{subreddit}/search.json?{urlencode(params)}"
            data = self._fetch(url)
            if not data:
                break

            children = data.get("data", {}).get("children", [])
            if not children:
                break

            for child in children:
                d = child.get("data", {})
                if not d:
                    continue
                permalink = d.get("permalink", "")
                posts.append(
                    {
                        "source": "reddit",
                        "query": query,
                        "subreddit": subreddit,
                        "title": d.get("title", ""),
                        "selftext": d.get("selftext", "")[:2000],
                        "url": f"https://www.reddit.com{permalink}" if permalink else "",
                        "author": _redact(d.get("author", "")),
                        "score": int(d.get("score", 0)),
                        "num_comments": int(d.get("num_comments", 0)),
                        "created_utc": float(d.get("created_utc", 0)),
                        "is_self": bool(d.get("is_self", False)),
                        "scraped_at": time.time(),
                    }
                )

            after = data.get("data", {}).get("after")
            if not after:
                break
            time.sleep(0.5)  # respect rate limit within pagination

        return posts

    def run(self, max_pages_per_query: int = 1) -> dict[str, Any]:
        """Scrape Reddit old.json endpoint — posts only."""
        all_posts: list[dict] = []
        per_query: list[dict] = []

        for subreddit in REDDIT_SUBREDDITS:
            for query in tqdm(REDDIT_QUERIES, desc=f"r/{subreddit}"):
                try:
                    posts = self._scrape_query(
                        subreddit, query, max_pages=max_pages_per_query
                    )
                    all_posts.extend(posts)
                    per_query.append(
                        {
                            "subreddit": subreddit,
                            "query": query,
                            "n_posts": len(posts),
                        }
                    )
                    # Periodic save (so we don't lose progress on timeout)
                    if len(all_posts) % 500 < 100:
                        meta = self.meta(
                            "reddit_old",
                            {
                                "n_posts": len(all_posts),
                                "queries": REDDIT_QUERIES,
                                "subreddits": REDDIT_SUBREDDITS,
                                "per_query": per_query,
                            },
                        )
                        self.save_json(
                            {"meta": meta, "posts": all_posts},
                            "reddit_old.json",
                            subdir="raw",
                        )
                except Exception as exc:
                    log.warning("r/%s q=%s error: %s", subreddit, query, exc)
                time.sleep(1.0)  # respect rate limit

        # Dedup
        seen: set[str] = set()
        unique: list[dict] = []
        for p in all_posts:
            if p["url"] and p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        all_posts = unique

        meta = self.meta(
            "reddit_old",
            {
                "n_posts": len(all_posts),
                "n_total": len(all_posts),
                "queries": REDDIT_QUERIES,
                "subreddits": REDDIT_SUBREDDITS,
                "max_pages_per_query": max_pages_per_query,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "posts": all_posts}
        self.save_json(out, "reddit_old.json", subdir="raw")

        sample = all_posts[:500] if len(all_posts) > 500 else all_posts
        self.save_json({**out, "posts": sample}, "reddit_old_sample.json", subdir="sample")

        log.info("Reddit old.json: %d posts (unique) dari %d sub × %d query",
                 len(all_posts), len(REDDIT_SUBREDDITS), len(REDDIT_QUERIES))
        return {
            "status": "ok" if all_posts else "no_data",
            "n_posts": len(all_posts),
            "n_total": len(all_posts),
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    result = RedditOldScraper().run(max_pages_per_query=pages)
    print(json.dumps(result, indent=2))
