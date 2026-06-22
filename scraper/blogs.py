"""Scraper blog posts (Medium, financial blogs) tentang paylater/pinjol (PRIORITAS 8 - baru)."""
from __future__ import annotations

import logging
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.blogs")

BLOG_QUERIES: list[str] = [
    "paylater indonesia", "pinjol indonesia", "gagal bayar paylater",
    "tips bayar paylater", "bahaya pinjol", "financial behavior gen z",
    "cicilan online", "utang online", "kredit tanpa kartu kredit",
]


class BlogScraper(BaseScraper):
    name = "blogs"

    def _fetch(self, url: str) -> str | None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        }
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.text
        except Exception as e:
            log.warning("Gagal fetch %s: %s", url, e)
        return None

    def _scrape_medium(self, query: str, max_posts: int = 20) -> list[dict]:
        posts = []
        html = self._fetch(f"https://medium.com/search?q={requests.utils.quote(query)}")
        if not html:
            return posts
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if "medium.com" in href and len(title) > 20 and "/search" not in href and "@" not in href[:30]:
                posts.append({
                    "source": "medium", "query": query,
                    "title": title[:200],
                    "url": href if href.startswith("http") else f"https://medium.com{href}",
                    "scraped_at": time.time(),
                })
            if len(posts) >= max_posts:
                break
        seen = set()
        unique = []
        for p in posts:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        return unique[:max_posts]

    def _scrape_dailysia(self, query: str, max_posts: int = 20) -> list[dict]:
        posts = []
        html = self._fetch(f"https://dailysia.com/?s={requests.utils.quote(query)}")
        if not html:
            return posts
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)
            if "dailysia.com" in href and len(title) > 20 and href != "https://dailysia.com/":
                posts.append({
                    "source": "dailysia", "query": query,
                    "title": title[:200], "url": href,
                    "scraped_at": time.time(),
                })
            if len(posts) >= max_posts:
                break
        seen = set()
        unique = []
        for p in posts:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        return unique[:max_posts]

    def run(self, max_per_query: int = 20) -> dict[str, Any]:
        all_posts = []
        for query in tqdm(BLOG_QUERIES, desc="Blog queries"):
            try:
                for p in self._scrape_medium(query, max_posts=max_per_query):
                    all_posts.append(p)
                for p in self._scrape_dailysia(query, max_posts=max_per_query):
                    all_posts.append(p)
            except Exception as e:
                log.warning("Blog query '%s' error: %s", query, e)
            self.polite_sleep()
        seen = set()
        unique = []
        for p in all_posts:
            if p["url"] not in seen:
                seen.add(p["url"])
                unique.append(p)
        all_posts = unique
        meta = self.meta("blogs", {
            "n_total": len(all_posts), "queries": BLOG_QUERIES,
            "sources": ["medium", "dailysia"],
        })
        self.save_json({"meta": meta, "posts": all_posts}, "blogs_all.json", subdir="raw")
        sample = all_posts[:500] if len(all_posts) > 500 else all_posts
        self.save_json({"meta": meta, "posts": sample}, "blogs_sample.json", subdir="sample")
        return {
            "status": "ok" if all_posts else "no_data",
            "n_total": len(all_posts), "queries": BLOG_QUERIES,
        }
