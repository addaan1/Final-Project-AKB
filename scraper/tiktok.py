"""Scraper komentar TikTok #galbay #paylater #pinjol (PRIORITAS 2).

Menggunakan Playwright untuk render TikTok web. Fokus Gen Z audience.

Etika:
- Tidak simpan username asli (redact ke user_id_hash).
- Simpan teks komentar + timestamp + video metadata.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.tiktok")

HASHTAGS: list[str] = [
    "galbay",
    "gagalbayar",
    "paylater",
    "pinjol",
    "gagalbayar",
    "pinjamanonline",
    "selfreward",
    "fomo",
    "checkout",
    "bayarnanti",
    "ditagih",
    "utang",
]

MAX_VIDEOS_PER_HASHTAG = 5
MAX_COMMENTS_PER_VIDEO = 20


class TikTokScraper(BaseScraper):
    name = "tiktok"

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    async def _scrape_hashtag_playwright(self, hashtag: str, max_videos: int, max_comments: int) -> list[dict]:
        """Scrape satu hashtag via Playwright."""
        from playwright.async_api import async_playwright

        comments = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="id-ID",
            )
            page = await context.new_page()

            try:
                url = f"https://www.tiktok.com/search?q=%23{hashtag}"
                log.info("Opening %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(2000)

                video_links = await page.eval_on_selector_all(
                    "a[href*='/video/']",
                    "els => els.slice(0, 10).map(el => el.href)",
                )
                video_links = list(set(video_links))[:max_videos]
                log.info("Found %d videos for #%s", len(video_links), hashtag)

                for video_url in video_links:
                    try:
                        await page.goto(video_url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(5000)

                        desc_selectors = [
                            "[data-e2e='browse-video-desc']",
                            "span[data-text='true']",
                            "div.video-meta-title",
                        ]
                        video_desc = ""
                        for selector in desc_selectors:
                            try:
                                element = await page.query_selector(selector)
                                if element:
                                    video_desc = await element.inner_text()
                                    break
                            except Exception:
                                pass

                        for _ in range(2):
                            await page.mouse.wheel(0, 1500)
                            await page.wait_for_timeout(2000)

                        comment_selectors = [
                            "[data-e2e='comment-level-1'] p",
                            "p[data-e2e='comment-text']",
                            "div.comment-text",
                            "span.comment-text",
                        ]
                        for selector in comment_selectors:
                            comment_texts = await page.eval_on_selector_all(
                                selector,
                                "els => els.slice(0, 20).map(el => el.innerText)",
                            )
                            for text in comment_texts[:max_comments]:
                                if text and len(text) > 3:
                                    comments.append(
                                        {
                                            "text": text.strip(),
                                            "username_hash": self._redact_username(str(hash(text))),
                                            "hashtag": hashtag,
                                            "video_url": video_url,
                                            "video_desc": video_desc[:200],
                                            "scraped_at": time.time(),
                                        }
                                    )
                            if comment_texts:
                                break
                    except Exception as exc:
                        log.warning("Error scraping video %s: %s", video_url, exc)
                    self.polite_sleep()
            except Exception as exc:
                log.warning("Error scraping hashtag #%s: %s", hashtag, exc)
            finally:
                await browser.close()

        return comments

    def run(self, max_videos: int = MAX_VIDEOS_PER_HASHTAG, max_comments: int = MAX_COMMENTS_PER_VIDEO) -> dict[str, Any]:
        """Scrape TikTok via Playwright."""
        all_comments = []
        per_hashtag = []

        for hashtag in tqdm(HASHTAGS, desc="TikTok hashtags"):
            try:
                comments = asyncio.run(self._scrape_hashtag_playwright(hashtag, max_videos, max_comments))
                all_comments.extend(comments)
                per_hashtag.append({"hashtag": hashtag, "n_comments": len(comments)})
            except Exception as exc:
                log.warning("Gagal scrape #%s: %s", hashtag, exc)
                per_hashtag.append({"hashtag": hashtag, "n_comments": 0, "error": str(exc)})
            self.polite_sleep()

        meta = self.meta(
            "tiktok",
            {
                "n_comments": len(all_comments),
                "hashtags": HASHTAGS,
                "max_videos_per_hashtag": max_videos,
                "max_comments_per_video": max_comments,
                "per_hashtag": per_hashtag,
            },
        )

        self.save_json({"meta": meta, "comments": all_comments}, "tiktok_comments.json", subdir="raw")
        sample = all_comments[:500] if len(all_comments) > 500 else all_comments
        self.save_json({"meta": meta, "comments": sample}, "tiktok_comments_sample.json", subdir="sample")

        log.info("TikTok: %d komentar dari %d hashtag", len(all_comments), len(HASHTAGS))
        return {
            "status": "ok" if all_comments else "no_data",
            "n_comments": len(all_comments),
            "hashtags": HASHTAGS,
        }
