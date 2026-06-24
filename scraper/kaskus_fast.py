"""Scraper Kaskus (only) — tanpa Playwright, lebih cepat & reliable.

Menggunakan requests + BeautifulSoup langsung ke endpoint search Kaskus. Anti-bot
Kaskus lebih lemah dari TikTok/Tokopedia. Output schema:
    {
        "query": str,
        "title": str,
        "url": str,
        "category": str,    # "personal" / "leisure" / etc
        "author": str,
        "replies": int,
        "views": int,
        "scraped_at": float,
    }

Etika:
    - Hanya thread title (bukan full content) untuk hemat bandwidth.
    - Respect rate-limit (1 detik per request).
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.kaskus_fast")

KASKUS_QUERIES: list[str] = [
    "paylater", "pinjol", "galbay", "gagal bayar", "utang", "ditagih",
    "cicilan", "self reward", "FOMO", "checkout", "bunga tinggi",
    "debt collector", "tagihan", "kartu kredit", "kredit",
    "pinjaman online", "shopee paylater", "kredivo", "indodana",
    "limit paylater", "gali lubang", "restrukturisasi", "konsolidasi",
    "cicil", "beli sekarang bayar nanti", "bunga 0", "pinjam",
    "tagih", "nagih", "bayar", "lunas", "denda",
]

KASKUS_SEARCH_URL = "https://www.kaskus.co.id/search?q={q}&forum_id=&type=thread"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


class KaskusFastScraper(BaseScraper):
    """Scraper Kaskus via requests + BeautifulSoup (no Playwright)."""

    name = "kaskus_fast"

    def _fetch(self, url: str) -> str | None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning("Kaskus %s status %d", url[:60], r.status_code)
        except Exception as exc:
            log.warning("Kaskus fetch error: %s", exc)
        return None

    def _parse_replies(self, text: str) -> int:
        """Parse '23 Replies' -> 23."""
        if not text:
            return 0
        m = re.search(r"(\d+)\s*repl", text.lower())
        return int(m.group(1)) if m else 0

    def _parse_views(self, text: str) -> int:
        """Parse '1.2K Views' -> 1200."""
        if not text:
            return 0
        m = re.search(r"([\d.,]+)\s*([KkMm]?)\s*views?", text, re.I)
        if not m:
            return 0
        num = m.group(1).replace(",", "").replace(".", "")
        try:
            n = int(num)
        except ValueError:
            return 0
        suffix = m.group(2).lower()
        if suffix == "k":
            n *= 1000
        elif suffix == "m":
            n *= 1_000_000
        return n

    def _scrape_query(self, query: str, max_pages: int = 2) -> list[dict]:
        """Scrape search results untuk satu query."""
        threads = []
        for page in range(1, max_pages + 1):
            url = f"{KASKUS_SEARCH_URL.format(q=quote(query))}&page={page}"
            html = self._fetch(url)
            if not html:
                break

            soup = BeautifulSoup(html, "lxml")

            # Multiple selector strategies (Kaskus sering ganti class)
            items = []
            for selector in [
                "div.qaItem",
                "article.qaItem",
                "div.SearchItem",
                "a[href*='/thread/']",
            ]:
                items = soup.select(selector)
                if items:
                    break

            page_count = 0
            for item in items:
                try:
                    # Title
                    title = ""
                    for tsel in ["h2", "h3", ".qaTitle", ".SearchItem-title", "a"]:
                        tel = item.select_one(tsel)
                        if tel:
                            title = tel.get_text(strip=True)
                            if title and len(title) > 5:
                                break
                    if not title or len(title) < 5:
                        continue

                    # URL
                    href = ""
                    anchor = item.select_one("a[href*='/thread/']")
                    if anchor:
                        href = anchor.get("href", "")
                    if not href:
                        anchor = item.select_one("a")
                        if anchor:
                            href = anchor.get("href", "")

                    # Replies & views
                    text_content = item.get_text(" ", strip=True)
                    replies = self._parse_replies(text_content)
                    views = self._parse_views(text_content)

                    threads.append(
                        {
                            "query": query,
                            "title": title[:200],
                            "url": href if href.startswith("http") else f"https://www.kaskus.co.id{href}",
                            "author": "",
                            "replies": replies,
                            "views": views,
                            "scraped_at": time.time(),
                        }
                    )
                    page_count += 1
                except Exception as exc:
                    log.debug("Parse error: %s", exc)

            if page_count == 0:
                break  # No more results
            self.polite_sleep()

        return threads

    def run(self, max_pages: int = 2, max_per_query: int = 40) -> dict[str, Any]:
        """Scrape KASKUS_QUERIES dengan pagination."""
        all_threads: list[dict] = []
        per_query: list[dict] = []

        for query in tqdm(KASKUS_QUERIES, desc="Kaskus queries"):
            try:
                threads = self._scrape_query(query, max_pages=max_pages)
                threads = threads[:max_per_query]
                all_threads.extend(threads)
                per_query.append({"query": query, "n_threads": len(threads)})
            except Exception as exc:
                log.warning("Kaskus query '%s' error: %s", query, exc)
                per_query.append({"query": query, "n_threads": 0, "error": str(exc)})
            self.polite_sleep()

        # Dedup by URL
        seen: set[str] = set()
        unique: list[dict] = []
        for t in all_threads:
            if t["url"] and t["url"] not in seen:
                seen.add(t["url"])
                unique.append(t)
        all_threads = unique

        meta = self.meta(
            "kaskus_fast",
            {
                "n_total": len(all_threads),
                "queries": KASKUS_QUERIES,
                "max_pages": max_pages,
                "max_per_query": max_per_query,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "threads": all_threads}
        self.save_json(out, "kaskus_fast.json", subdir="raw")

        sample = all_threads[:500] if len(all_threads) > 500 else all_threads
        self.save_json({**out, "threads": sample}, "kaskus_fast_sample.json", subdir="sample")

        log.info("Kaskus fast: %d threads (unique) dari %d query", len(all_threads), len(KASKUS_QUERIES))
        return {
            "status": "ok" if all_threads else "no_data",
            "n_total": len(all_threads),
            "queries": KASKUS_QUERIES,
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    result = KaskusFastScraper().run(max_pages=pages)
    print(result)
