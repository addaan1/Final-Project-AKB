"""Scraper post X/Twitter keyword galbay/pinjol (PRIORITAS 4).

Menggunakan Playwright untuk render X/Twitter search.
Twitter/X tanpa login biasanya menampilkan login wall.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.twitter")

QUERIES: list[str] = [
    "galbay",
    "gagal bayar",
    "paylater",
    "pinjol",
    "ditagih",
    "pinjaman online",
    "cicilan",
]

MAX_TWEETS_PER_QUERY = 20


class TwitterScraper(BaseScraper):
    name = "twitter"

    def __init__(self, sleep_seconds: float = 0.0):
        super().__init__(sleep_seconds)
        self.auth_token = self.get_env("TWITTER_AUTH_TOKEN", "")
        self.ct0 = self.get_env("TWITTER_CT0", "")
        self.logged_in = bool(self.auth_token and self.ct0)
        if self.logged_in:
            log.info("Twitter login aktif (cookies tersedia)")
        else:
            log.info("Twitter tanpa login (hanya akan dapat login wall). Set TWITTER_AUTH_TOKEN + TWITTER_CT0 di .env")

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    def _build_context_options(self) -> dict:
        """Build context options dengan cookies kalau login tersedia."""
        options = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1280, "height": 720},
            "locale": "id-ID",
        }
        if self.logged_in:
            options["storage_state"] = {
                "cookies": [
                    {"name": "auth_token", "value": self.auth_token, "domain": ".x.com", "path": "/"},
                    {"name": "ct0", "value": self.ct0, "domain": ".x.com", "path": "/"},
                ],
                "origins": [{"origin": "https://x.com", "localStorage": []}],
            }
        return options

    async def _scrape_twitter_playwright(self, query: str, max_tweets: int) -> list[dict]:
        """Scrape X/Twitter via Playwright. Pakai cookies kalau tersedia."""
        from playwright.async_api import async_playwright

        tweets = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context_options = self._build_context_options()
            storage_state = context_options.pop("storage_state", None)
            context = await browser.new_context(**context_options)
            if storage_state:
                await context.add_cookies(storage_state["cookies"])
            page = await context.new_page()

            try:
                url = f"https://x.com/search?q={query}&src=typed_query&f=live"
                log.info("Opening %s (login=%s)", url, self.logged_in)
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(8000)

                if "onboarding" in page.url or "login" in page.url:
                    log.warning("Twitter login wall (tidak ada cookies). Skip.")
                    return tweets

                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(2000)

                article_handles = await page.query_selector_all("article[data-testid='tweet']")
                log.info("Found %d tweet articles for q=%s", len(article_handles), query)

                for handle in article_handles[:max_tweets]:
                    try:
                        text_element = await handle.query_selector("[data-testid='tweetText']")
                        text = await text_element.inner_text() if text_element else ""

                        user_element = await handle.query_selector("[data-testid='User-Name'] a")
                        username = (await user_element.inner_text()).strip().replace("@", "") if user_element else ""

                        time_element = await handle.query_selector("time")
                        timestamp = await time_element.get_attribute("datetime") if time_element else ""

                        link_element = await handle.query_selector("a[href*='/status/']")
                        href = await link_element.get_attribute("href") if link_element else ""
                        tweet_url = f"https://x.com{href}" if href and href.startswith("/") else (href or "")

                        like_element = await handle.query_selector("[data-testid='like'] span")
                        likes = await like_element.inner_text() if like_element else ""
                        retweet_element = await handle.query_selector("[data-testid='retweet'] span")
                        retweets = await retweet_element.inner_text() if retweet_element else ""

                        if text:
                            tweets.append(
                                {
                                    "query": query,
                                    "text": text.strip()[:1000],
                                    "username_hash": self._redact_username(username) if username else "anon",
                                    "tweet_url": tweet_url,
                                    "timestamp": timestamp,
                                    "likes": likes,
                                    "retweets": retweets,
                                    "scraped_at": time.time(),
                                }
                            )
                    except Exception as exc:
                        log.warning("Error extracting tweet: %s", exc)
            except Exception as exc:
                log.warning("Error scraping Twitter q=%s: %s", query, exc)
            finally:
                await browser.close()

        return tweets

    def run(self, max_tweets: int = MAX_TWEETS_PER_QUERY) -> dict[str, Any]:
        """Scrape Twitter/X via Playwright."""
        all_tweets = []
        per_query = []
        twitter_accessible = True

        for query in tqdm(QUERIES, desc="Twitter/X queries"):
            if not twitter_accessible:
                break
            try:
                tweets = asyncio.run(self._scrape_twitter_playwright(query, max_tweets))
                all_tweets.extend(tweets)
                per_query.append({"query": query, "n_tweets": len(tweets)})
            except Exception as exc:
                if "timeout" in str(exc).lower() or "connection" in str(exc).lower():
                    log.warning("Twitter tidak accessible (network): %s. Skip.", exc)
                    twitter_accessible = False
                    break
                log.warning("Twitter %s error: %s", query, exc)
                per_query.append({"query": query, "n_tweets": 0, "error": str(exc)})
            self.polite_sleep()

        meta = self.meta(
            "twitter_playwright",
            {
                "n_tweets": len(all_tweets),
                "queries": QUERIES,
                "max_tweets_per_query": max_tweets,
                "per_query": per_query,
                "logged_in": self.logged_in,
            },
        )

        self.save_json({"meta": meta, "tweets": all_tweets}, "twitter_tweets.json", subdir="raw")
        sample = all_tweets[:500] if len(all_tweets) > 500 else all_tweets
        self.save_json({"meta": meta, "tweets": sample}, "twitter_tweets_sample.json", subdir="sample")

        log.info("Twitter: %d tweets (login=%s)", len(all_tweets), self.logged_in)
        return {
            "status": "ok" if all_tweets else "no_data",
            "n_tweets": len(all_tweets),
            "queries": QUERIES,
            "logged_in": self.logged_in,
        }
