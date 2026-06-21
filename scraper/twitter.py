"""Scraper post X/Twitter keyword galbay/pinjol (PRIORITAS 4).

Menggunakan Playwright untuk render X/Twitter search.
Nitter sudah mati (empty content), jadi langsung ke Twitter/X.
Twitter/X tanpa login hanya menampilkan tweet publik terbatas.

Etika:
- Tidak simpan username asli (redact ke hash).
- Simpan tweet text + timestamp + engagement metrics.
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
    "galbay", "gagal bayar", "paylater", "pinjol",
    "ditagih", "pinjaman online", "cicilan",
]

MAX_TWEETS_PER_QUERY = 20


class TwitterScraper(BaseScraper):
    name = "twitter"

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    async def _scrape_twitter_playwright(self, query: str, max_tweets: int) -> list[dict]:
        """Scrape X/Twitter via Playwright."""
        from playwright.async_api import async_playwright
        tweets = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="id-ID",
            )
            page = await context.new_page()

            try:
                url = f"https://x.com/search?q={query}&src=typed_query&f=live"
                log.info("Opening %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(8000)

                # Scroll untuk load more
                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(2000)

                # Twitter/X menggunakan article[data-testid="tweet"]
                article_handles = await page.query_selector_all('article[data-testid="tweet"]')
                log.info("Found %d tweet articles for q=%s", len(article_handles), query)

                for handle in article_handles[:max_tweets]:
                    try:
                        # Get tweet text
                        text_el = await handle.query_selector('[data-testid="tweetText"]')
                        text = ""
                        if text_el:
                            text = await text_el.inner_text()

                        # Get username
                        user_el = await handle.query_selector('[data-testid="User-Name"] a, [data-testid="User-Names"] a')
                        username = ""
                        if user_el:
                            username = (await user_el.inner_text()).strip().replace("@", "")

                        # Get timestamp
                        time_el = await handle.query_selector('time')
                        timestamp = ""
                        if time_el:
                            timestamp = await time_el.get_attribute("datetime")

                        # Get tweet link
                        link_el = await handle.query_selector('a[href*="/status/"]')
                        tweet_url = ""
                        if link_el:
                            href = await link_el.get_attribute("href")
                            if href:
                                tweet_url = f"https://x.com{href}" if href.startswith("/") else href

                        # Get engagement
                        like_el = await handle.query_selector('[data-testid="like"] span, [aria-label*="like"]')
                        likes = ""
                        if like_el:
                            likes = await like_el.inner_text()

                        rt_el = await handle.query_selector('[data-testid="retweet"] span, [aria-label*="repost"]')
                        retweets = ""
                        if rt_el:
                            retweets = await rt_el.inner_text()

                        if text:
                            tweets.append({
                                "query": query,
                                "text": text.strip()[:1000],
                                "username_hash": self._redact_username(username) if username else "anon",
                                "tweet_url": tweet_url,
                                "timestamp": timestamp,
                                "likes": likes,
                                "retweets": retweets,
                                "scraped_at": time.time(),
                            })
                    except Exception as e:
                        log.warning("Error extracting tweet: %s", e)

            except Exception as e:
                log.warning("Error scraping Twitter q=%s: %s", query, e)
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
                tweets = asyncio.run(
                    self._scrape_twitter_playwright(query, max_tweets)
                )
                all_tweets.extend(tweets)
                per_query.append({"query": query, "n_tweets": len(tweets)})
            except Exception as e:
                if "timeout" in str(e).lower() or "connection" in str(e).lower():
                    log.warning("Twitter tidak accessible (network): %s. Skip.", e)
                    twitter_accessible = False
                    break
                log.warning("Twitter %s error: %s", query, e)
                per_query.append({"query": query, "n_tweets": 0, "error": str(e)})
            self.polite_sleep()

        meta = self.meta("twitter_playwright", {
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
            "status": "ok" if all_tweets else "no_data",
            "n_tweets": len(all_tweets),
            "queries": QUERIES,
        }
