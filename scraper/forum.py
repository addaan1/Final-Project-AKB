"""Scraper forum: Kaskus & Reddit thread utang/paylater (PRIORITAS 3).

Kaskus: BeautifulSoup + requests pada forum Kaskus (kaskus.co.id).
Reddit: public JSON endpoint (tanpa API credentials).

Volume menengah-tinggi, relevansi tinggi (diskusi panjang = konteks psikologi).
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.forum")

KASKUS_QUERIES: list[str] = [
    "paylater", "pinjol", "galbay", "gagal bayar", "utang",
    "ditagih", "cicilan", "pinjaman online",
]

REDDIT_SUBREDDITS: list[str] = ["indonesia", "finansial"]
REDDIT_QUERIES: list[str] = [
    "paylater", "pinjol", "galbay", "utang", "ditagih", "cicilan",
]

KASKUS_SEARCH_URL = "https://www.kaskus.co.id/search"
REDDIT_SEARCH_URL = "https://www.reddit.com/r/{sub}/search.json"


class ForumScraper(BaseScraper):
    name = "forum"

    def _scrape_kaskus(self, max_threads: int = 50) -> list[dict]:
        """Scrape Kaskus threads via search."""
        threads = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        }

        for query in tqdm(KASKUS_QUERIES, desc="Kaskus search"):
            try:
                params = {"q": query, "sort": "relevance", "page": 1}
                resp = requests.get(KASKUS_SEARCH_URL, params=params, headers=headers, timeout=15)
                if resp.status_code != 200:
                    log.warning("Kaskus search '%s' status %d", query, resp.status_code)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select("div.thread-list, article.thread-item, div.search-result-item")

                if not items:
                    items = soup.select("div[data-id], li.search-result")

                count = 0
                for item in items:
                    if count >= max_threads:
                        break
                    try:
                        title_el = item.select_one("h2 a, h3 a, a.thread-title, a.title")
                        if not title_el:
                            continue
                        title = title_el.get_text(strip=True)
                        url = title_el.get("href", "")
                        if url and not url.startswith("http"):
                            url = "https://www.kaskus.co.id" + url

                        snippet_el = item.select_one("p.snippet, div.snippet, span.snippet, p.description")
                        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                        meta_el = item.select_one("span.date, time, span.meta, span.timestamp")
                        date_str = meta_el.get_text(strip=True) if meta_el else ""

                        threads.append({
                            "source": "kaskus",
                            "query": query,
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "date": date_str,
                            "scraped_at": time.time(),
                        })
                        count += 1
                    except Exception as e:
                        log.warning("Error parse Kaskus item: %s", e)

                log.info("Kaskus '%s': %d threads", query, count)
                self.polite_sleep()

            except Exception as e:
                log.warning("Gagal scrape Kaskus '%s': %s", query, e)

        return threads

    def _scrape_reddit(self, max_posts: int = 50) -> list[dict]:
        """Scrape Reddit via public JSON endpoint (tanpa credentials)."""
        posts = []
        headers = {
            "User-Agent": "GalbayPredictor/1.0 (academic research; contact: adieffendy5@gmail.com)",
        }

        for sub in tqdm(REDDIT_SUBREDDITS, desc="Reddit subreddits"):
            for query in REDDIT_QUERIES:
                try:
                    url = REDDIT_SEARCH_URL.format(sub=sub)
                    params = {
                        "q": query,
                        "sort": "relevance",
                        "t": "year",
                        "limit": min(max_posts, 25),
                        "raw_json": 1,
                    }
                    resp = requests.get(url, params=params, headers=headers, timeout=15)
                    if resp.status_code == 429:
                        log.warning("Reddit rate limit hit, waiting 60s...")
                        time.sleep(60)
                        continue
                    if resp.status_code != 200:
                        log.warning("Reddit r/%s '%s' status %d", sub, query, resp.status_code)
                        continue

                    data = resp.json()
                    children = data.get("data", {}).get("children", [])
                    count = 0
                    for child in children:
                        if count >= max_posts:
                            break
                        d = child.get("data", {})
                        if d.get("stickied"):
                            continue
                        posts.append({
                            "source": "reddit",
                            "subreddit": sub,
                            "query": query,
                            "post_id": d.get("id"),
                            "title": d.get("title", ""),
                            "selftext": (d.get("selftext") or "")[:2000],
                            "url": "https://www.reddit.com" + d.get("permalink", ""),
                            "score": d.get("score", 0),
                            "num_comments": d.get("num_comments", 0),
                            "created_utc": d.get("created_utc"),
                            "author": "[deleted]",
                            "scraped_at": time.time(),
                        })
                        count += 1

                    log.info("Reddit r/%s '%s': %d posts", sub, query, count)
                    self.polite_sleep()

                except Exception as e:
                    log.warning("Gagal scrape Reddit r/%s '%s': %s", sub, query, e)

        return posts

    def run(self, max_threads: int = 50, max_posts: int = 50) -> dict[str, Any]:
        """Jalankan scraping Kaskus + Reddit."""
        kaskus_threads = self._scrape_kaskus(max_threads=max_threads)
        reddit_posts = self._scrape_reddit(max_posts=max_posts)

        all_items = kaskus_threads + reddit_posts

        meta = self.meta("forum", {
            "n_kaskus_threads": len(kaskus_threads),
            "n_reddit_posts": len(reddit_posts),
            "n_total": len(all_items),
            "kaskus_queries": KASKUS_QUERIES,
            "reddit_subreddits": REDDIT_SUBREDDITS,
            "reddit_queries": REDDIT_QUERIES,
        })

        self.save_json({"meta": meta, "kaskus": kaskus_threads}, "kaskus_threads.json", subdir="raw")
        self.save_json({"meta": meta, "reddit": reddit_posts}, "reddit_posts.json", subdir="raw")
        self.save_json({"meta": meta, "all": all_items}, "forum_all.json", subdir="raw")

        sample = all_items[:500] if len(all_items) > 500 else all_items
        self.save_json({"meta": meta, "sample": sample}, "forum_sample.json", subdir="sample")

        log.info("Forum: %d Kaskus threads + %d Reddit posts = %d total",
                 len(kaskus_threads), len(reddit_posts), len(all_items))

        return {
            "status": "ok",
            "n_kaskus": len(kaskus_threads),
            "n_reddit": len(reddit_posts),
            "n_total": len(all_items),
        }
