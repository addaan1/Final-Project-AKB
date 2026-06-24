"""Scraper Threads (Meta) — public posts via HTML scrape.

Threads.net adalah Twitter-like platform dari Meta. Anti-bot lebih lemah dari
TikTok/Instagram. Bisa scrape hashtag search via HTML (server-rendered) atau
graphql endpoint.

Output schema per post:
    {
        "source": "threads",
        "query": str,
        "username_hash": str,     # PII redacted
        "text": str,
        "likes": int,
        "replies": int,
        "reposts": int,
        "url": str,
        "timestamp": str,
        "scraped_at": float,
    }

Etika:
    - Username di-redact ke hash.
    - Hanya public posts (no auth, no login).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any
from urllib.parse import quote

import requests
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.threads")

THREADS_QUERIES: list[str] = [
    "galbay", "gagal bayar", "paylater", "pinjol", "utang", "cicilan",
    "self reward", "FOMO", "checkout", "bunga tinggi", "debt collector",
    "tagihan", "kartu kredit", "kredit", "pinjaman online", "kredivo",
    "indodana", "akulaku", "julo", "koinworks", "amartha",
    "gali lubang", "restrukturisasi", "konsolidasi",
]

THREADS_SEARCH_URL = "https://www.threads.net/search?q={q}&serp_type=default"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _redact(text: str) -> str:
    if not text:
        return "anon"
    return hashlib.sha256(text.encode()).hexdigest()[:12]


class ThreadsScraper(BaseScraper):
    """Scraper Threads.net via HTML (no auth)."""

    name = "threads"

    def _fetch(self, url: str) -> str | None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning("Threads %d for %s", r.status_code, url[:60])
        except Exception as exc:
            log.warning("Threads fetch error: %s", exc)
        return None

    def _scrape_query(self, query: str) -> list[dict]:
        """Scrape hashtag/search result. Threads HTML berisi post text + meta."""
        url = THREADS_SEARCH_URL.format(q=quote(query))
        html = self._fetch(url)
        if not html:
            return []

        posts: list[dict] = []

        # Threads search HTML biasanya berisi text posts di JSON embedded
        # atau di attribute data-* . Mari extract dengan regex pattern.
        # Pattern: "text":"...","timestamp":"..." atau <span>text</span>

        # Strategy 1: extract dari window.__INITIAL_DATA__ (jika ada)
        initial_data = re.search(
            r"window\.__INITIAL_DATA__\s*=\s*(\{.+?\});",
            html,
            re.DOTALL,
        )
        if initial_data:
            try:
                init = json.loads(initial_data.group(1))
                # Recursively find posts
                def find_posts(obj, depth=0):
                    if depth > 10:
                        return
                    if isinstance(obj, dict):
                        # Threads post biasanya punya 'caption' atau 'text' + 'like_count'
                        if "text" in obj and isinstance(obj["text"], str) and len(obj["text"]) > 10:
                            posts.append(
                                {
                                    "source": "threads",
                                    "query": query,
                                    "username_hash": _redact(str(obj.get("user", {}).get("username", ""))),
                                    "text": obj.get("text", "")[:2000],
                                    "likes": int(obj.get("like_count", 0) or 0),
                                    "replies": int(obj.get("reply_count", 0) or 0),
                                    "reposts": int(obj.get("repost_count", 0) or 0),
                                    "url": obj.get("url", ""),
                                    "timestamp": obj.get("taken_at", ""),
                                    "scraped_at": time.time(),
                                }
                            )
                        for v in obj.values():
                            find_posts(v, depth + 1)
                    elif isinstance(obj, list):
                        for v in obj:
                            find_posts(v, depth + 1)

                find_posts(init)
            except Exception as exc:
                log.debug("INITIAL_DATA parse error: %s", exc)

        # Strategy 2: extract from meta tags (iframes, OpenGraph)
        if not posts:
            og_desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if og_desc:
                posts.append(
                    {
                        "source": "threads",
                        "query": query,
                        "username_hash": "anon",
                        "text": og_desc.group(1)[:2000],
                        "likes": 0,
                        "replies": 0,
                        "reposts": 0,
                        "url": url,
                        "timestamp": "",
                        "scraped_at": time.time(),
                    }
                )

        # Strategy 3: extract from HTML (look for text in spans)
        if not posts:
            text_spans = re.findall(
                r'<span[^>]*>([^<]{20,500})</span>',
                html,
            )
            for text in text_spans[:5]:
                if any(kw.lower() in text.lower() for kw in [query, "galbay", "pinjol", "paylater"]):
                    posts.append(
                        {
                            "source": "threads",
                            "query": query,
                            "username_hash": "anon",
                            "text": text,
                            "likes": 0,
                            "replies": 0,
                            "reposts": 0,
                            "url": url,
                            "timestamp": "",
                            "scraped_at": time.time(),
                        }
                    )

        return posts

    def run(self, max_per_query: int = 20) -> dict[str, Any]:
        """Scrape THREADS_QUERIES."""
        all_posts: list[dict] = []
        per_query: list[dict] = []

        for query in tqdm(THREADS_QUERIES, desc="Threads queries"):
            try:
                posts = self._scrape_query(query)[:max_per_query]
                all_posts.extend(posts)
                per_query.append({"query": query, "n_posts": len(posts)})
            except Exception as exc:
                log.warning("Threads q=%s error: %s", query, exc)
                per_query.append({"query": query, "n_posts": 0, "error": str(exc)})
            time.sleep(1.5)  # respect rate limit

        meta = self.meta(
            "threads",
            {
                "n_total": len(all_posts),
                "queries": THREADS_QUERIES,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "posts": all_posts}
        self.save_json(out, "threads_posts.json", subdir="raw")

        sample = all_posts[:500] if len(all_posts) > 500 else all_posts
        self.save_json({**out, "posts": sample}, "threads_posts_sample.json", subdir="sample")

        log.info("Threads: %d posts dari %d query", len(all_posts), len(THREADS_QUERIES))
        return {
            "status": "ok" if all_posts else "no_data",
            "n_total": len(all_posts),
            "queries": THREADS_QUERIES,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = ThreadsScraper().run()
    print(json.dumps(result, indent=2))
