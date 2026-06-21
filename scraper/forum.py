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
    "paylater", "pinjol", "galbay", "utang", "ditagih", "cicilan",
]
REDDIT_SUBREDDITS: list[str] = ["indonesia", "finansial"]

KASKUS_QUERIES: list[str] = [
    "paylater", "pinjol", "galbay", "gagal bayar", "utang",
    "ditagih", "cicilan",
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

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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

                # Scroll to load more
                for _ in range(3):
                    await page.mouse.wheel(0, 1500)
                    await page.wait_for_timeout(2000)

                # Extract posts via Reddit's shreddit-post web components
                post_handles = await page.query_selector_all('shreddit-post, [data-testid="post-container"], article')
                log.info("Found %d post elements for r/%s q=%s", len(post_handles), subreddit, query)

                for handle in post_handles[:max_posts]:
                    try:
                        # Try to get title
                        title = ""
                        for sel in ['[slot="title"]', 'a[data-testid="post-title"]', 'h3', 'h2 a']:
                            el = await handle.query_selector(sel)
                            if el:
                                title = await el.inner_text()
                                break

                        # Get URL
                        post_url = await handle.evaluate('el => el.href || el.querySelector("a")?.href || ""')

                        # Get score
                        score = ""
                        for sel in ['[slot="score"]', '[data-testid="post-vote-score"]', 'span.score']:
                            el = await handle.query_selector(sel)
                            if el:
                                score = await el.inner_text()
                                break

                        # Get comment count
                        comments = ""
                        for sel in ['[slot="comments"]', 'a[data-testid="comments-page-link"]', 'span.comments']:
                            el = await handle.query_selector(sel)
                            if el:
                                comments = await el.inner_text()
                                break

                        # Get post id
                        post_id = await handle.evaluate('el => el.getAttribute("id") || el.getAttribute("data-post-id") || ""')

                        if title:
                            posts.append({
                                "source": "reddit",
                                "subreddit": subreddit,
                                "query": query,
                                "post_id": post_id,
                                "title": title.strip()[:200],
                                "url": post_url,
                                "score": score,
                                "num_comments": comments,
                                "scraped_at": time.time(),
                            })
                    except Exception as e:
                        log.warning("Error extracting post: %s", e)

            except Exception as e:
                log.warning("Error scraping r/%s q=%s: %s", subreddit, query, e)
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
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                for child in data.get("data", {}).get("children", []):
                    d = child.get("data", {})
                    posts.append({
                        "source": "reddit",
                        "subreddit": subreddit,
                        "query": query,
                        "post_id": d.get("id"),
                        "title": (d.get("title") or "")[:200],
                        "selftext": (d.get("selftext") or "")[:1000],
                        "url": "https://www.reddit.com" + d.get("permalink", ""),
                        "score": d.get("score", 0),
                        "num_comments": d.get("num_comments", 0),
                        "created_utc": d.get("created_utc"),
                        "scraped_at": time.time(),
                    })
        except Exception as e:
            log.warning("Reddit JSON fallback failed: %s", e)
        return posts

    async def _scrape_kaskus_playwright(self, query: str, max_threads: int) -> list[dict]:
        """Scrape Kaskus via Playwright (render SPA)."""
        from playwright.async_api import async_playwright
        threads = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
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

                # Scroll
                for _ in range(2):
                    await page.mouse.wheel(0, 1500)
                    await page.wait_for_timeout(2000)

                # Extract thread links
                thread_handles = await page.query_selector_all('a[href*="/thread/"], a[href*="/@"]')
                log.info("Found %d thread links for query=%s", len(thread_handles), query)

                for handle in thread_handles[:max_threads]:
                    try:
                        href = await handle.evaluate('el => el.href')
                        title = await handle.inner_text()
                        if href and title and len(title.strip()) > 10:
                            threads.append({
                                "source": "kaskus",
                                "query": query,
                                "title": title.strip()[:200],
                                "url": href,
                                "scraped_at": time.time(),
                            })
                    except Exception:
                        pass
            except Exception as e:
                log.warning("Error scraping Kaskus q=%s: %s", query, e)
            finally:
                await browser.close()

        return threads

    def run(self, max_threads: int = 20, max_posts: int = 20) -> dict[str, Any]:
        """Jalankan scraping Reddit + Kaskus via Playwright."""
        # Reddit - skip jika tidak accessible (timeout/blocked di network)
        all_reddit = []
        reddit_accessible = True
        for sub in tqdm(REDDIT_SUBREDDITS, desc="Reddit subreddits"):
            if not reddit_accessible:
                break
            for query in REDDIT_QUERIES:
                if not reddit_accessible:
                    break
                try:
                    posts = asyncio.run(
                        self._scrape_reddit_playwright(sub, query, max_posts)
                    )
                    if not posts:
                        posts = self._scrape_reddit_fallback_json(sub, query, max_posts)
                    all_reddit.extend(posts)
                except Exception as e:
                    if "timeout" in str(e).lower() or "connection" in str(e).lower():
                        log.warning("Reddit tidak accessible (network): %s. Skip.", e)
                        reddit_accessible = False
                        break
                    log.warning("Reddit %s/%s error: %s", sub, query, e)
                self.polite_sleep()

        # Kaskus
        all_kaskus = []
        for query in tqdm(KASKUS_QUERIES, desc="Kaskus queries"):
            try:
                threads = asyncio.run(
                    self._scrape_kaskus_playwright(query, max_threads)
                )
                all_kaskus.extend(threads)
            except Exception as e:
                log.warning("Kaskus %s error: %s", query, e)
            self.polite_sleep()

        all_items = all_reddit + all_kaskus

        meta = self.meta("forum", {
            "n_reddit": len(all_reddit),
            "n_kaskus": len(all_kaskus),
            "n_total": len(all_items),
            "reddit_queries": REDDIT_QUERIES,
            "reddit_subreddits": REDDIT_SUBREDDITS,
            "kaskus_queries": KASKUS_QUERIES,
        })

        self.save_json({"meta": meta, "reddit": all_reddit}, "reddit_posts.json", subdir="raw")
        self.save_json({"meta": meta, "kaskus": all_kaskus}, "kaskus_threads.json", subdir="raw")
        self.save_json({"meta": meta, "all": all_items}, "forum_all.json", subdir="raw")

        sample = all_items[:500] if len(all_items) > 500 else all_items
        self.save_json({"meta": meta, "sample": sample}, "forum_sample.json", subdir="sample")

        log.info("Forum: %d Reddit + %d Kaskus = %d total",
                 len(all_reddit), len(all_kaskus), len(all_items))

        return {
            "status": "ok" if all_items else "no_data",
            "n_reddit": len(all_reddit),
            "n_kaskus": len(all_kaskus),
            "n_total": len(all_items),
        }
