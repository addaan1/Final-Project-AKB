"""Scraper post X/Twitter keyword galbay/pinjol (PRIORITAS 4).

Menggunakan Nitter instances (gratis, tidak stabil).
Jika semua instance down, scraper gracefully skip.

Etika:
- Tidak simpan username asli (redact ke hash).
- Simpan tweet text + timestamp + engagement metrics.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.twitter")

QUERIES: list[str] = [
    "galbay", "gagal bayar", "paylater", "pinjol",
    "ditagih", "pinjaman online", "cicilan",
]

NITTER_INSTANCES: list[str] = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
    "https://nitter.net",
]

MAX_TWEETS_PER_QUERY = 50


class TwitterScraper(BaseScraper):
    name = "twitter"

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    def _find_working_instance(self) -> str | None:
        """Cari Nitter instance yang aktif."""
        for inst in NITTER_INSTANCES:
            try:
                resp = requests.get(inst, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if resp.status_code == 200:
                    log.info("Working Nitter instance: %s", inst)
                    return inst
            except Exception:
                continue
        return None

    def _scrape_nitter_search(self, instance: str, query: str, max_tweets: int = MAX_TWEETS_PER_QUERY) -> list[dict]:
        """Scrape tweets dari satu Nitter instance."""
        tweets = []
        try:
            url = f"{instance}/search?f=tweets&q={requests.utils.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                log.warning("Nitter search '%s' status %d", query, resp.status_code)
                return tweets

            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.select("div.timeline-item, div.tweet-body, article.tweet")

            for item in items:
                if len(tweets) >= max_tweets:
                    break
                try:
                    content_el = item.select_one("div.tweet-content, span.tweet-text, div.tweet-body")
                    if not content_el:
                        continue
                    text = content_el.get_text(strip=True)

                    username_el = item.select_one("a.username, span.username")
                    username = username_el.get_text(strip=True).lstrip("@") if username_el else "unknown"

                    time_el = item.select_one("span.tweet-date a, time.timestamp")
                    tweet_url = time_el.get("href", "") if time_el else ""
                    if tweet_url and not tweet_url.startswith("http"):
                        tweet_url = "https://twitter.com" + tweet_url

                    date_el = item.select_one("span.tweet-date, time")
                    date_str = date_el.get("title", "") if date_el else ""

                    stats_el = item.select_one("div.tweet-stats, span.tweet-stat")
                    stats_text = stats_el.get_text(strip=True) if stats_el else ""

                    tweets.append({
                        "query": query,
                        "text": text,
                        "username_hash": self._redact_username(username),
                        "tweet_url": tweet_url,
                        "date": date_str,
                        "stats": stats_text,
                        "scraped_at": time.time(),
                    })
                except Exception as e:
                    log.warning("Error parse tweet: %s", e)

        except Exception as e:
            log.warning("Gagal scrape Nitter '%s': %s", query, e)

        return tweets

    def run(self, max_tweets: int = MAX_TWEETS_PER_QUERY) -> dict[str, Any]:
        """Jalankan scraping Twitter via Nitter."""
        instance = self._find_working_instance()
        if not instance:
            log.error("Tidak ada Nitter instance yang aktif. Skip Twitter scraping.")
            return {"status": "no_instance", "n_tweets": 0}

        all_tweets = []
        per_query = []

        for query in tqdm(QUERIES, desc="Twitter/Nitter search"):
            tweets = self._scrape_nitter_search(instance, query, max_tweets=max_tweets)
            all_tweets.extend(tweets)
            per_query.append({"query": query, "n_tweets": len(tweets)})
            self.polite_sleep()

        meta = self.meta("twitter_nitter", {
            "instance": instance,
            "n_tweets": len(all_tweets),
            "queries": QUERIES,
            "max_tweets_per_query": max_tweets,
            "per_query": per_query,
        })

        self.save_json({"meta": meta, "tweets": all_tweets}, "twitter_tweets.json", subdir="raw")

        sample = all_tweets[:500] if len(all_tweets) > 500 else all_tweets
        self.save_json({"meta": meta, "tweets": sample}, "twitter_tweets_sample.json", subdir="sample")

        log.info("Twitter: %d tweets dari %d queries", len(all_tweets), len(QUERIES))
        return {
            "status": "ok",
            "n_tweets": len(all_tweets),
            "queries": QUERIES,
            "instance": instance,
        }
