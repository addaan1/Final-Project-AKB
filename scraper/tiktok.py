"""Scraper komentar TikTok #galbay #paylater #pinjol (PRIORITAS 2).

Menggunakan Playwright untuk render TikTok web (lebih reliable dari TikTokApi
tanpa ms_tokens). Fokus Gen Z audience.

Etika:
- Tidak simpan username asli (redact ke user_id_hash).
- Simpan teks komentar + timestamp + video metadata.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import Any

from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.tiktok")

HASHTAGS: list[str] = [
    "galbay", "gagalbayar", "paylater", "pinjol",
    "gagalbayar", "pinjamanonline", "selfreward", "fomo",
    "checkout", "bayarnanti", "ditagih", "utang",
]

MAX_VIDEOS_PER_HASHTAG = 5
MAX_COMMENTS_PER_VIDEO = 20


class TikTokScraper(BaseScraper):
    name = "tiktok"

    def __init__(self, sleep_seconds: float = 0.0):
        super().__init__(sleep_seconds)
        ms_tokens_str = self.get_env("TIKTOK_MS_TOKENS", "")
        self.ms_tokens = [t.strip() for t in ms_tokens_str.split(",") if t.strip()] if ms_tokens_str else []
        if self.ms_tokens:
            log.info("TikTok login: %d ms_tokens tersedia", len(self.ms_tokens))
        else:
            log.info("TikTok tanpa login (anti-bot mungkin block). Set TIKTOK_MS_TOKENS di .env.")

    @staticmethod
    def _redact_username(username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()[:12]

    async def _scrape_hashtag_playwright(self, hashtag: str, max_videos: int, max_comments: int) -> list[dict]:
        """Scrape satu hashtag via Playwright."""
        from playwright.async_api import async_playwright
        comments = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 720},
                locale="id-ID",
            )
            page = await context.new_page()

            try:
                # Buka search page
                url = f"https://www.tiktok.com/search?q=%23{hashtag}"
                log.info("Opening %s", url)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)

                # Scroll untuk load lebih banyak video
                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(2000)

                # Extract video links
                video_links = await page.eval_on_selector_all(
                    'a[href*="/video/"]',
                    'els => els.slice(0, 10).map(el => el.href)'
                )
                video_links = list(set(video_links))[:max_videos]
                log.info("Found %d videos for #%s", len(video_links), hashtag)

                # Visit each video to get comments
                for vurl in video_links:
                    try:
                        await page.goto(vurl, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(5000)

                        # Get video description
                        desc_selectors = ['[data-e2e="browse-video-desc"]', 'span[data-text="true"]', 'div.video-meta-title']
                        video_desc = ""
                        for sel in desc_selectors:
                            try:
                                el = await page.query_selector(sel)
                                if el:
                                    video_desc = await el.inner_text()
                                    break
                            except Exception:
                                pass

                        # Scroll to load comments
                        for _ in range(2):
                            await page.mouse.wheel(0, 1500)
                            await page.wait_for_timeout(2000)

                        # Extract comments
                        comment_selectors = [
                            '[data-e2e="comment-level-1"] p',
                            'p[data-e2e="comment-text"]',
                            'div.comment-text',
                            'span.comment-text',
                        ]
                        for sel in comment_selectors:
                            comment_texts = await page.eval_on_selector_all(
                                sel, 'els => els.slice(0, 20).map(el => el.innerText)'
                            )
                            for text in comment_texts[:max_comments]:
                                if text and len(text) > 3:
                                    comments.append({
                                        "text": text.strip(),
                                        "username_hash": self._redact_username(str(hash(text))),
                                        "hashtag": hashtag,
                                        "video_url": vurl,
                                        "video_desc": video_desc[:200],
                                        "scraped_at": __import__("time").time(),
                                    })
                            if comment_texts:
                                break
                    except Exception as e:
                        log.warning("Error scraping video %s: %s", vurl, e)
                    self.polite_sleep()

            except Exception as e:
                log.warning("Error scraping hashtag #%s: %s", hashtag, e)
            finally:
                await browser.close()

        return comments

    def run(self, max_videos: int = MAX_VIDEOS_PER_HASHTAG, max_comments: int = MAX_COMMENTS_PER_VIDEO) -> dict[str, Any]:
        """Scrape TikTok via Playwright."""
        all_comments = []
        per_hashtag = []

        for ht in tqdm(HASHTAGS, desc="TikTok hashtags"):
            try:
                comments = asyncio.run(
                    self._scrape_hashtag_playwright(ht, max_videos, max_comments)
                )
                all_comments.extend(comments)
                per_hashtag.append({"hashtag": ht, "n_comments": len(comments)})
            except Exception as e:
                log.warning("Gagal scrape #%s: %s", ht, e)
                per_hashtag.append({"hashtag": ht, "n_comments": 0, "error": str(e)})
            self.polite_sleep()

        meta = self.meta("tiktok", {
            "n_comments": len(all_comments),
            "hashtags": HASHTAGS,
            "max_videos_per_hashtag": max_videos,
            "max_comments_per_video": max_comments,
            "per_hashtag": per_hashtag,
        })

        self.save_json({"meta": meta, "comments": all_comments}, "tiktok_comments.json", subdir="raw")
        sample = all_comments[:500] if len(all_comments) > 500 else all_comments
        self.save_json({"meta": meta, "comments": sample}, "tiktok_comments_sample.json", subdir="sample")

        log.info("TikTok: %d komentar dari %d hashtag", len(all_comments), len(HASHTAGS))
        return {
            "status": "ok" if all_comments else "no_data",
            "n_comments": len(all_comments),
            "hashtags": HASHTAGS,
        }
