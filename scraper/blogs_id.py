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
    "bahaya pinjol", "cicilan online", "utang online", "galbay",
    "debt collector", "cicilan 0%", "checkout bayar nanti", "pinjol ilegal",
    "pinjol legal", "bunga tinggi", "restrukturisasi", "konsolidasi utang",
    "gali lubang tutup lubang", "tips keuangan gen z", "literasi keuangan",
    "tagihan paylater", "beli sekarang bayar nanti", "kartu kredit online",
    "utang pinjol", "denda telat bayar", "gagal bayar hutang",
    "kredit pintar", "kredivo", "akulaku", "indodana", "julo", "shopee paylater",
    "dana paylater", "goPaylater", "uangme", "tunaiku", "kta online",
    "pinjaman modal", "bank digital", "jago", "jenius", "blu", "seabank",
    "cicilan tokopedia", "cicilan shopee", "gojek paylater", "grab paylater",
    "traveloka paylater", "lazada paylater",
]

BLOGS: list[dict] = [
    {
        "name": "kumparan",
        "search_url": "https://kumparan.com/search?q={q}",
        "paged_url": "https://kumparan.com/search?q={q}&page={p}",
    },
    {
        "name": "hipwee",
        "search_url": "https://www.hipwee.com/?s={q}",
        "paged_url": "https://www.hipwee.com/page/{p}/?s={q}",
    },
    {
        "name": "brilio",
        "search_url": "https://www.brilio.net/search/?keyword={q}",
        "paged_url": "https://www.brilio.net/search/{p}/?keyword={q}",
    },
    {
        "name": "cnbc",
        "search_url": "https://www.cnbcindonesia.com/search?query={q}",
        "paged_url": "https://www.cnbcindonesia.com/search?query={q}&page={p}",
    },
    {
        "name": "kompas",
        "search_url": "https://search.kompas.com/search?q={q}",
        "paged_url": "https://search.kompas.com/search?q={q}&p={p}",
    },
    {
        "name": "detik",
        "search_url": "https://www.detik.com/search/searchall?query={q}",
        "paged_url": "https://www.detik.com/search/searchall?query={q}&page={p}",
    },
    {
        "name": "idntimes",
        "search_url": "https://www.idntimes.com/search?q={q}",
        "paged_url": "https://www.idntimes.com/search?q={q}&page={p}",
    },
    {
        "name": "tempo",
        "search_url": "https://www.tempo.co/search?q={q}",
        "paged_url": "https://www.tempo.co/search?q={q}&page={p}",
    },
    {
        "name": "okezone",
        "search_url": "https://search.okezone.com/search?q={q}",
        "paged_url": "https://search.okezone.com/search?q={q}&p={p}",
    },
    {
        "name": "merdeka",
        "search_url": "https://www.merdeka.com/search/?keyword={q}",
        "paged_url": "https://www.merdeka.com/search/{p}/?keyword={q}",
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

    def _scrape_blog(self, blog: dict, query: str, max_posts: int = 20, max_pages: int = 3) -> list[dict]:
        """Scrape satu blog untuk satu query, dengan pagination."""
        all_posts: list[dict] = []
        seen_urls: set[str] = set()
        paged = blog.get("paged_url")

        for page in range(1, max_pages + 1):
            if page == 1 or not paged:
                url = blog["search_url"].format(q=quote(query))
            else:
                url = paged.format(q=quote(query), p=page)
            html = self._fetch(url)
            if not html:
                break
            soup = BeautifulSoup(html, "lxml")
            found_in_page = 0
            for a in soup.find_all("a", href=True):
                href = a.get("href", "")
                title = a.get_text(strip=True)
                if (
                    blog["name"] in href.lower()
                    and len(title) > 25
                    and "/search" not in href
                    and "/tag/" not in href
                    and href not in seen_urls
                ):
                    if not href.startswith("http"):
                        href = "https:" + href if href.startswith("//") else f"https://{blog['name']}.com{href}"
                    seen_urls.add(href)
                    all_posts.append(
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
                    found_in_page += 1
                    if len(all_posts) >= max_posts:
                        return all_posts
            if found_in_page == 0:
                break
        return all_posts

    def run(self, max_per_query: int = 30, max_pages: int = 3) -> dict[str, Any]:
        """Scrape BLOGS × BLOG_QUERIES × pages."""
        all_posts: list[dict] = []
        per_blog: dict[str, int] = {b["name"]: 0 for b in BLOGS}
        per_query_stats: list[dict] = []

        for blog in BLOGS:
            for query in tqdm(BLOG_QUERIES, desc=f"{blog['name']} queries"):
                try:
                    posts = self._scrape_blog(blog, query, max_per_query, max_pages)
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
