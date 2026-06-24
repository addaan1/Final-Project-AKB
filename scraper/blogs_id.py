"""Scraper Blog Indonesia — kumparan, hipwee, brilio, cnbc, kompas, dll.

Fokus blog lokal yang banyak membahas finansial/pinjol/paylater dengan tone
Gen Z. Lebih mudah di-scrape dari Marketplace/Threads.

Output schema per post:
    {
        "source": "blog_id",
        "blog": str,         # "kumparan" | "hipwee" | "brilio" | etc
        "query": str,
        "title": str,
        "url": str,
        "snippet": str,
        "scraped_at": float,
    }
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.blogs_id")

BLOG_QUERIES: list[str] = [
    "paylater indonesia", "pinjol indonesia", "gagal bayar", "tips bayar paylater",
    "bahaya pinjol", "financial behavior gen z", "cicilan online", "utang online",
    "kredit tanpa kartu kredit", "galbay", "debt collector", "cicilan 0%",
    "self reward", "checkout bayar nanti", "pinjol ilegal", "pinjol legal",
    "bunga tinggi", "restrukturisasi", "konsolidasi utang", "gali lubang tutup lubang",
    "tips keuangan gen z", "menabung gen z", "financial freedom", "literasi keuangan",
    "tagihan paylater", "beli sekarang bayar nanti", "kartu kredit online",
    "utang pinjol", "denda telat bayar", "gagal bayar hutang",
]

BLOGS: list[dict] = [
    {
        "name": "kumparan",
        "search_url": "https://kumparan.com/search?q={q}",
    },
    {
        "name": "hipwee",
        "search_url": "https://www.hipwee.com/?s={q}",
    },
    {
        "name": "brilio",
        "search_url": "https://www.brilio.net/search/?keyword={q}",
    },
    {
        "name": "cnbc",
        "search_url": "https://www.cnbcindonesia.com/search?query={q}",
    },
    {
        "name": "kompas",
        "search_url": "https://search.kompas.com/search?q={q}",
    },
    {
        "name": "detik",
        "search_url": "https://www.detik.com/search/searchall?query={q}",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


class BlogIdScraper(BaseScraper):
    """Scraper multiple blog Indonesia."""

    name = "blogs_id"

    def _fetch(self, url: str) -> str | None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.text
            log.warning("Blog %d for %s", r.status_code, url[:60])
        except Exception as exc:
            log.warning("Blog fetch error: %s", exc)
        return None

    def _scrape_blog(self, blog: dict, query: str, max_posts: int = 20) -> list[dict]:
        """Scrape satu blog untuk satu query."""
        url = blog["search_url"].format(q=quote(query))
        html = self._fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        posts: list[dict] = []

        # Generic: find all article-like links with substantial title
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)

            # Filter: same domain, title panjang
            if (
                blog["name"] in href.lower()
                and len(title) > 25
                and "/search" not in href
                and title not in [p["title"] for p in posts]
            ):
                if not href.startswith("http"):
                    href = "https:" + href if href.startswith("//") else f"https://{blog['name']}.com{href}"
                posts.append(
                    {
                        "source": "blog_id",
                        "blog": blog["name"],
                        "query": query,
                        "title": title[:200],
                        "url": href,
                        "snippet": "",
                        "scraped_at": time.time(),
                    }
                )
                if len(posts) >= max_posts:
                    break

        return posts

    def run(self, max_per_query: int = 10) -> dict[str, Any]:
        """Scrape BLOGS × BLOG_QUERIES."""
        all_posts: list[dict] = []
        per_blog: dict[str, int] = {b["name"]: 0 for b in BLOGS}
        per_query_stats: list[dict] = []

        for blog in BLOGS:
            for query in tqdm(BLOG_QUERIES, desc=f"{blog['name']} queries"):
                try:
                    posts = self._scrape_blog(blog, query, max_per_query)
                    all_posts.extend(posts)
                    per_blog[blog["name"]] += len(posts)
                    per_query_stats.append(
                        {
                            "blog": blog["name"],
                            "query": query,
                            "n_posts": len(posts),
                        }
                    )
                except Exception as exc:
                    log.warning("%s q=%s error: %s", blog["name"], query, exc)
                self.polite_sleep()

        # Dedup
        seen: set[str] = set()
        unique: list[dict] = []
        for p in all_posts:
            if p["url"] and p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        all_posts = unique

        meta = self.meta(
            "blogs_id",
            {
                "n_total": len(all_posts),
                "per_blog": per_blog,
                "queries": BLOG_QUERIES,
                "blogs": [b["name"] for b in BLOGS],
                "per_query": per_query_stats[:30],
            },
        )

        out = {"meta": meta, "posts": all_posts}
        self.save_json(out, "blogs_id.json", subdir="raw")

        sample = all_posts[:500] if len(all_posts) > 500 else all_posts
        self.save_json({**out, "posts": sample}, "blogs_id_sample.json", subdir="sample")

        log.info("Blogs ID: %d posts dari %d blog × %d query", len(all_posts), len(BLOGS), len(BLOG_QUERIES))
        return {
            "status": "ok" if all_posts else "no_data",
            "n_total": len(all_posts),
            "per_blog": per_blog,
        }


if __name__ == "__main__":
    import sys
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    result = BlogIdScraper().run()
    print(json.dumps(result, indent=2, default=str))
