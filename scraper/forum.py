"""Scraper forum: Kaskus & Reddit thread utang/paylater (PRIORITAS 3).

Reddit: Playwright render HTML (JSON API blocked).
Kaskus: Playwright render SPA (rate-limited + JS-heavy).

Volume menengah-tinggi, relevansi tinggi (diskusi panjang = konteks psikologi).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import requests
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.forum")

REDDIT_QUERIES: list[str] = [
    "paylater",
    "pinjol",
    "galbay",
    "utang",
    "ditagih",
    "cicilan",
]
REDDIT_SUBREDDITS: list[str] = ["indonesia", "finansial"]

KASKUS_QUERIES: list[str] = [
    "paylater",
    "pinjol",
    "galbay",
    "gagal bayar",
    "utang",
    "ditagih",
    "cicilan",
]


class ForumScraper(BaseScraper):
    name = "forum"

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    async def _scrape_reddit_playwright(self, subreddit: str, query: str, max_posts: int) -> list[dict]:
        """Scrape Reddit via Playwright."""
        from playwright.async_api import async_playwright

        posts = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
            )
            page = await context.new_page()

            try:
                url = f"https://www.reddit.com/r/{subreddit}/search/?q={query}&sort=relevance&t=year"
                log.info("Opening %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

                for _ in range(3):
                    await page.mouse.wheel(0, 1500)
                    await page.wait_for_timeout(2000)

                post_handles = await page.query_selector_all("shreddit-post, [data-testid='post-container'], article")
                log.info("Found %d post elements for r/%s q=%s", len(post_handles), subreddit, query)

                for handle in post_handles[:max_posts]:
                    try:
                        title = ""
                        for selector in ("[slot='title']", "a[data-testid='post-title']", "h3", "h2 a"):
                            element = await handle.query_selector(selector)
                            if element:
                                title = await element.inner_text()
                                break

                        post_url = await handle.evaluate('el => el.href || el.querySelector("a")?.href || ""')

                        score = ""
                        for selector in ("[slot='score']", "[data-testid='post-vote-score']", "span.score"):
                            element = await handle.query_selector(selector)
                            if element:
                                score = await element.inner_text()
                                break

                        comments = ""
                        for selector in ("[slot='comments']", "a[data-testid='comments-page-link']", "span.comments"):
                            element = await handle.query_selector(selector)
                            if element:
                                comments = await element.inner_text()
                                break

                        post_id = await handle.evaluate('el => el.getAttribute("id") || el.getAttribute("data-post-id") || ""')

                        if title:
                            posts.append(
                                {
                                    "source": "reddit",
                                    "subreddit": subreddit,
                                    "query": query,
                                    "post_id": post_id,
                                    "title": title.strip()[:200],
                                    "url": post_url,
                                    "score": score,
                                    "num_comments": comments,
                                    "scraped_at": time.time(),
                                }
                            )
                    except Exception as exc:
                        log.warning("Error extracting post: %s", exc)
            except Exception as exc:
                log.warning("Error scraping r/%s q=%s: %s", subreddit, query, exc)
            finally:
                await browser.close()

        return posts

    def _scrape_reddit_fallback_json(self, subreddit: str, query: str, max_posts: int) -> list[dict]:
        """Fallback: coba Reddit JSON dengan header lengkap (mungkin rate-limited)."""
        posts = []
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "sort": "relevance", "t": "year", "limit": max_posts, "raw_json": 1}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                for child in data.get("data", {}).get("children", []):
                    item = child.get("data", {})
                    posts.append(
                        {
                            "source": "reddit",
                            "subreddit": subreddit,
                            "query": query,
                            "post_id": item.get("id"),
                            "title": (item.get("title") or "")[:200],
                            "selftext": (item.get("selftext") or "")[:1000],
                            "url": "https://www.reddit.com" + item.get("permalink", ""),
                            "score": item.get("score", 0),
                            "num_comments": item.get("num_comments", 0),
                            "created_utc": item.get("created_utc"),
                            "scraped_at": time.time(),
                        }
                    )
        except Exception as exc:
            log.warning("Reddit JSON fallback failed: %s", exc)
        return posts

    async def _scrape_kaskus_playwright(self, query: str, max_threads: int) -> list[dict]:
        """Scrape Kaskus via Playwright (render SPA)."""
        from playwright.async_api import async_playwright

        threads = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="id-ID",
            )
            page = await context.new_page()

            try:
                url = f"https://www.kaskus.co.id/search?q={query}"
                log.info("Opening %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

                for _ in range(2):
                    await page.mouse.wheel(0, 1500)
                    await page.wait_for_timeout(2000)

                thread_handles = await page.query_selector_all("a[href*='/thread/'], a[href*='/@']")
                log.info("Found %d thread links for query=%s", len(thread_handles), query)

                for handle in thread_handles[:max_threads]:
                    try:
                        href = await handle.evaluate("el => el.href")
                        title = await handle.inner_text()
                        if href and title and len(title.strip()) > 10:
                            threads.append(
                                {
                                    "source": "kaskus",
                                    "query": query,
                                    "title": title.strip()[:200],
                                    "url": href,
                                    "scraped_at": time.time(),
                                }
                            )
                    except Exception:
                        pass
            except Exception as exc:
                log.warning("Error scraping Kaskus q=%s: %s", query, exc)
            finally:
                await browser.close()

        return threads

    def run(self, max_threads: int = 20, max_posts: int = 20) -> dict[str, Any]:
        """Jalankan scraping Reddit + Kaskus via Playwright."""
        all_reddit = []
        reddit_accessible = True
        for subreddit in tqdm(REDDIT_SUBREDDITS, desc="Reddit subreddits"):
            if not reddit_accessible:
                break
            for query in REDDIT_QUERIES:
                if not reddit_accessible:
                    break
                try:
                    posts = asyncio.run(self._scrape_reddit_playwright(subreddit, query, max_posts))
                    if not posts:
                        posts = self._scrape_reddit_fallback_json(subreddit, query, max_posts)
                    all_reddit.extend(posts)
                except Exception as exc:
                    if "timeout" in str(exc).lower() or "connection" in str(exc).lower():
                        log.warning("Reddit tidak accessible (network): %s. Skip.", exc)
                        reddit_accessible = False
                        break
                    log.warning("Reddit %s/%s error: %s", subreddit, query, exc)
                self.polite_sleep()

        all_kaskus = []
        for query in tqdm(KASKUS_QUERIES, desc="Kaskus queries"):
            try:
                threads = asyncio.run(self._scrape_kaskus_playwright(query, max_threads))
                all_kaskus.extend(threads)
            except Exception as exc:
                log.warning("Kaskus %s error: %s", query, exc)
            self.polite_sleep()

        all_items = all_reddit + all_kaskus
        meta = self.meta(
            "forum",
            {
                "n_reddit": len(all_reddit),
                "n_kaskus": len(all_kaskus),
                "n_total": len(all_items),
                "reddit_queries": REDDIT_QUERIES,
                "reddit_subreddits": REDDIT_SUBREDDITS,
                "kaskus_queries": KASKUS_QUERIES,
            },
        )

        self.save_json({"meta": meta, "reddit": all_reddit}, "reddit_posts.json", subdir="raw")
        self.save_json({"meta": meta, "kaskus": all_kaskus}, "kaskus_threads.json", subdir="raw")
        self.save_json({"meta": meta, "all": all_items}, "forum_all.json", subdir="raw")

        sample = all_items[:500] if len(all_items) > 500 else all_items
        self.save_json({"meta": meta, "sample": sample}, "forum_sample.json", subdir="sample")

        log.info("Forum: %d Reddit + %d Kaskus = %d total", len(all_reddit), len(all_kaskus), len(all_items))
        return {
            "status": "ok" if all_items else "no_data",
            "n_reddit": len(all_reddit),
            "n_kaskus": len(all_kaskus),
            "n_total": len(all_items),
        }
