"""Scraper Threads via Playwright (headless Chromium).

Threads.net search page render post text dalam `<span dir="auto">`. Anti-bot
detect headless tapi biasanya query tanpa login tetap load hasil.

Output schema per post:
    {
        "source": "threads",
        "query": str,
        "username_hash": str,    # PII redacted
        "text": str,
        "url": str,              # post URL
        "scraped_at": float,
    }
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from typing import Any
from urllib.parse import quote

from playwright.async_api import async_playwright
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.threads_pw")

THREADS_QUERIES: list[str] = [
    "galbay", "gagal bayar", "paylater", "pinjol", "utang", "cicilan",
    "self reward", "FOMO", "checkout", "bunga tinggi", "debt collector",
    "tagihan", "kartu kredit", "kredit", "pinjaman online", "kredivo",
    "indodana", "akulaku", "julo", "koinworks", "amartha",
    "gali lubang", "restrukturisasi", "konsolidasi", "bunga 0", "pinjam",
    "cicilan 0", "kartu kredit online", "beli sekarang bayar nanti",
    "literasi keuangan", "tips keuangan", "menabung", "financial freedom",
]

THREADS_SEARCH_URL = "https://www.threads.net/search?q={q}&serp_type=default"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _redact(text: str) -> str:
    if not text:
        return "anon"
    return hashlib.sha256(text.encode()).hexdigest()[:12]


class ThreadsPlaywrightScraper(BaseScraper):
    name = "threads_pw"

    async def _scrape_query(self, query: str, max_posts: int = 30) -> list[dict]:
        url = THREADS_SEARCH_URL.format(q=quote(query))
        posts: list[dict] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 800},
                locale="id-ID",
            )
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(8000)

                # Scroll untuk lazy-load posts
                for _ in range(3):
                    await page.mouse.wheel(0, 2000)
                    await page.wait_for_timeout(2000)

                # Get post text from <span dir="auto">
                spans = await page.locator("span[dir='auto']").all()
                for span in spans:
                    try:
                        text = (await span.inner_text()).strip()
                        if not text or len(text) < 15:
                            continue
                        # Filter yang terlalu generic
                        if text in ("Cari · Threads", "Threads", "Masuk", "Daftar"):
                            continue
                        posts.append(
                            {
                                "source": "threads",
                                "query": query,
                                "username_hash": "anon",
                                "text": text[:1000],
                                "url": url,
                                "scraped_at": time.time(),
                            }
                        )
                        if len(posts) >= max_posts:
                            break
                    except Exception as exc:
                        log.debug("Parse error: %s", exc)
            except Exception as exc:
                log.warning("Threads q='%s' error: %s", query, exc)
            finally:
                await browser.close()

        return posts

    def run(self, max_per_query: int = 30) -> dict[str, Any]:
        """Scrape THREADS_QUERIES via Playwright."""
        all_posts: list[dict] = []
        per_query: list[dict] = []

        for query in tqdm(THREADS_QUERIES, desc="Threads queries"):
            try:
                posts = asyncio.run(self._scrape_query(query, max_per_query))
                all_posts.extend(posts)
                per_query.append({"query": query, "n_posts": len(posts)})
            except Exception as exc:
                log.warning("Threads q='%s' error: %s", query, exc)
                per_query.append({"query": query, "n_posts": 0, "error": str(exc)})
            time.sleep(1.5)

        # Dedup by text (Threads user sering nge-tweet ulang)
        seen = set()
        unique = []
        for p in all_posts:
            if p["text"] and p["text"] not in seen:
                seen.add(p["text"])
                unique.append(p)
        all_posts = unique

        meta = self.meta(
            "threads_pw",
            {
                "n_total": len(all_posts),
                "queries": THREADS_QUERIES,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "posts": all_posts}
        self.save_json(out, "threads_pw.json", subdir="raw")

        sample = all_posts[:500] if len(all_posts) > 500 else all_posts
        self.save_json({**out, "posts": sample}, "threads_pw_sample.json", subdir="sample")

        log.info("Threads Playwright: %d posts dari %d query", len(all_posts), len(THREADS_QUERIES))
        return {
            "status": "ok" if all_posts else "no_data",
            "n_total": len(all_posts),
            "queries": THREADS_QUERIES,
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    result = ThreadsPlaywrightScraper().run(max_per_query=n)
    print(json.dumps(result, indent=2, default=str))
