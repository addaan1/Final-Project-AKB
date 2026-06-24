"""Scraper marketplace: Shopee & Tokopedia product listings (PRIORITAS 7 - baru).

Fokus listing produk yang mengandung keyword finansial/paylater/cicilan. Volume
tinggi, relevansi menengah-tinggi untuk triangulasi tren "checkout dulu bayar
nanti" — listing yang dipromosikan dengan cicilan/paylater = sinyal
konsumerisme Gen Z.

Output schema (per item):
    {
        "marketplace": "shopee" | "tokopedia",
        "query": str,
        "title": str,
        "price_idr": int,
        "price_text": str,
        "sold_text": str,            # "Terjual 1rb+", "500+"
        "rating_text": str,          # "4.9", "4.5"
        "location": str,             # "Jakarta Pusat", "Kab. Bandung"
        "url": str,
        "is_finansial_keyword": bool, # title mengandung paylater/cicilan/kredit
        "scraped_at": float,
    }

Etika:
    - Hanya scrape listing publik (tidak perlu login).
    - Tidak scrape review user individual (PII risk).
    - Rate-limit sopan (SCRAPER_SLEEP_SECONDS di .env).
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.marketplace")

QUERIES: list[str] = [
    "paylater",
    "cicilan 0%",
    "bunga 0%",
    "cicilan tanpa kartu kredit",
    "pinjaman online",
    "kredit online",
    "self reward",
    "checkout bayar nanti",
    "flash sale",
    "gadget cicilan",
]

FINANSIAL_KEYWORDS: tuple[str, ...] = (
    "paylater",
    "cicilan",
    "kredit",
    "pinjaman",
    "bunga 0",
    "bunga 0%",
    "tanpa kartu kredit",
    "0%",
    "kta",
)

SHOPEE_SEARCH_URL = "https://shopee.co.id/search?keyword={q}&page={page}"
TOKOPEDIA_SEARCH_URL = "https://www.tokopedia.com/search?q={q}&page={page}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _parse_idr_price(text: str) -> int:
    """Parse 'Rp1.250.000' atau 'Rp 1,25 juta' jadi int (rupiah)."""
    if not text:
        return 0
    cleaned = re.sub(r"[^\d,.\sa-zA-Z]", "", text).strip()
    if not cleaned:
        return 0

    juta_match = re.search(r"(\d+(?:[.,]\d+)?)\s*juta", cleaned, re.I)
    if juta_match:
        try:
            return int(float(juta_match.group(1).replace(",", ".")) * 1_000_000)
        except ValueError:
            pass
    ribu_match = re.search(r"(\d+(?:[.,]\d+)?)\s*rb", cleaned, re.I)
    if ribu_match:
        try:
            return int(float(ribu_match.group(1).replace(",", ".")) * 1_000)
        except ValueError:
            pass

    digits = re.sub(r"[^\d]", "", cleaned)
    if not digits:
        return 0
    try:
        return int(digits)
    except ValueError:
        return 0


def _is_finansial(title: str) -> bool:
    """Return True kalau title mengandung keyword finansial."""
    if not title:
        return False
    title_l = title.lower()
    return any(kw in title_l for kw in FINANSIAL_KEYWORDS)


class MarketplaceScraper(BaseScraper):
    """Scrape listing publik dari Shopee & Tokopedia via Playwright.

    Menggunakan Playwright (bukan requests) karena Shopee render awal kosong
    tanpa JS — perlu headless Chromium untuk memicu render produk.
    """

    name = "marketplace"

    def __init__(self, sleep_seconds: float = 0.0):
        super().__init__(sleep_seconds)
        self.marketplace = self.get_env("MARKETPLACE_TARGET", "both")  # shopee|tokopedia|both

    async def _scrape_shopee(
        self, query: str, max_pages: int = 2
    ) -> list[dict]:
        """Scrape listing publik Shopee untuk satu query."""
        from playwright.async_api import async_playwright

        items: list[dict] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
                locale="id-ID",
            )
            page = await context.new_page()

            for p in range(1, max_pages + 1):
                url = SHOPEE_SEARCH_URL.format(q=quote(query), page=p)
                log.info("[shopee] %s (page %d/%d)", query, p, max_pages)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(4000)

                    for _ in range(3):
                        await page.mouse.wheel(0, 1500)
                        await page.wait_for_timeout(1500)

                    card_selectors = [
                        "div[data-sqe='item']",
                        "li.shopee-search-item-result__item",
                        "div.col-xs-2-4",
                    ]
                    cards = []
                    for sel in card_selectors:
                        cards = await page.query_selector_all(sel)
                        if cards:
                            break

                    log.info("[shopee] %s: %d cards (page %d)", query, len(cards), p)

                    for card in cards:
                        try:
                            title = ""
                            for tsel in [
                                "div[data-sqe='name']",
                                "div.ieuqn3k",
                                "span.ieuqn3k",
                            ]:
                                el = await card.query_selector(tsel)
                                if el:
                                    title = (await el.inner_text()).strip()
                                    break

                            price_text = ""
                            for psel in [
                                "span[data-sqe='price']",
                                "div.zeYpNJ",
                                "span.Z5xR3a",
                            ]:
                                el = await card.query_selector(psel)
                                if el:
                                    price_text = (await el.inner_text()).strip()
                                    break

                            sold_text = ""
                            for ssel in [
                                "div[data-sqe='sold']",
                                "div.LW5xC8",
                                "span.r6HknA",
                            ]:
                                el = await card.query_selector(ssel)
                                if el:
                                    sold_text = (await el.inner_text()).strip()
                                    break

                            rating_text = ""
                            for rsel in [
                                "div[data-sqe='rating']",
                                "div.WgYpiP",
                            ]:
                                el = await card.query_selector(rsel)
                                if el:
                                    rating_text = (await el.inner_text()).strip()
                                    break

                            anchor = await card.query_selector("a")
                            href = await anchor.get_attribute("href") if anchor else ""
                            full_url = urljoin("https://shopee.co.id", href) if href else ""

                            location = ""
                            loc_el = await card.query_selector("div[data-sqe='location'], div.H2mpun")
                            if loc_el:
                                location = (await loc_el.inner_text()).strip()

                            if title and len(title) > 3:
                                items.append(
                                    {
                                        "marketplace": "shopee",
                                        "query": query,
                                        "title": title[:200],
                                        "price_idr": _parse_idr_price(price_text),
                                        "price_text": price_text,
                                        "sold_text": sold_text,
                                        "rating_text": rating_text,
                                        "location": location,
                                        "url": full_url,
                                        "is_finansial_keyword": _is_finansial(title),
                                        "scraped_at": time.time(),
                                    }
                                )
                        except Exception as exc:
                            log.debug("[shopee] card parse error: %s", exc)
                except Exception as exc:
                    log.warning("[shopee] %s page %d error: %s", query, p, exc)
                self.polite_sleep()
            await browser.close()
        return items

    async def _scrape_tokopedia(
        self, query: str, max_pages: int = 2
    ) -> list[dict]:
        """Scrape listing publik Tokopedia untuk satu query."""
        from playwright.async_api import async_playwright

        items: list[dict] = []
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=HEADERS["User-Agent"],
                viewport={"width": 1280, "height": 800},
                locale="id-ID",
            )
            page = await context.new_page()

            for p in range(1, max_pages + 1):
                url = TOKOPEDIA_SEARCH_URL.format(q=quote(query), page=p)
                log.info("[tokopedia] %s (page %d/%d)", query, p, max_pages)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await page.wait_for_timeout(5000)

                    for _ in range(3):
                        await page.mouse.wheel(0, 1500)
                        await page.wait_for_timeout(1500)

                    cards = await page.query_selector_all("div[data-testid='master-product-card'], div.css-5wh3g4, div.css-bk6tzz")
                    log.info("[tokopedia] %s: %d cards (page %d)", query, len(cards), p)

                    for card in cards:
                        try:
                            title = ""
                            for tsel in [
                                "span[data-testid='spnSRPProdName']",
                                "div[data-testid='divProductWrapper'] h2",
                                "span.css-3p5coa",
                                "h2",
                            ]:
                                el = await card.query_selector(tsel)
                                if el:
                                    title = (await el.inner_text()).strip()
                                    if title and len(title) > 3:
                                        break

                            price_text = ""
                            for psel in [
                                "span[data-testid='spnSRPProdPrice']",
                                "div[data-testid='divProductWrapper'] span.css-o5uqvq",
                                "span.css-o5uqvq",
                            ]:
                                el = await card.query_selector(psel)
                                if el:
                                    price_text = (await el.inner_text()).strip()
                                    break

                            sold_text = ""
                            for ssel in [
                                "span[data-testid='spnSRPProdSold']",
                                "span.css-1agv4wd",
                            ]:
                                el = await card.query_selector(ssel)
                                if el:
                                    sold_text = (await el.inner_text()).strip()
                                    break

                            rating_text = ""
                            for rsel in [
                                "span[data-testid='spnSRPProdRating']",
                                "span.css-1h3b0lu",
                            ]:
                                el = await card.query_selector(rsel)
                                if el:
                                    rating_text = (await el.inner_text()).strip()
                                    break

                            anchor = await card.query_selector("a")
                            href = await anchor.get_attribute("href") if anchor else ""
                            full_url = urljoin("https://www.tokopedia.com", href) if href else ""

                            location = ""
                            loc_el = await card.query_selector("span[data-testid='spnSRPLoc'], span.css-1h3b0lu")
                            if loc_el:
                                location = (await loc_el.inner_text()).strip()

                            if title and len(title) > 3:
                                items.append(
                                    {
                                        "marketplace": "tokopedia",
                                        "query": query,
                                        "title": title[:200],
                                        "price_idr": _parse_idr_price(price_text),
                                        "price_text": price_text,
                                        "sold_text": sold_text,
                                        "rating_text": rating_text,
                                        "location": location,
                                        "url": full_url,
                                        "is_finansial_keyword": _is_finansial(title),
                                        "scraped_at": time.time(),
                                    }
                                )
                        except Exception as exc:
                            log.debug("[tokopedia] card parse error: %s", exc)
                except Exception as exc:
                    log.warning("[tokopedia] %s page %d error: %s", query, p, exc)
                self.polite_sleep()
            await browser.close()
        return items

    def _run_async(self, coro):
        """Helper: jalankan coroutine di event loop (handle re-entry safe)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(coro, loop).result()
            return loop.run_until_complete(coro)
        except RuntimeError:
            return asyncio.run(coro)

    def run(
        self,
        max_pages: int = 2,
        max_per_query: int = 60,
        marketplace: str | None = None,
    ) -> dict[str, Any]:
        """Scrape Shopee & Tokopedia untuk semua QUERIES.

        Args:
            max_pages: jumlah halaman per query per marketplace (default 2).
            max_per_query: cap item per query (default 60).
            marketplace: "shopee" | "tokopedia" | "both" (override env).
        """
        target = (marketplace or self.marketplace or "both").lower()
        if target not in ("shopee", "tokopedia", "both"):
            target = "both"

        all_items: list[dict] = []
        per_query: list[dict] = []

        for query in tqdm(QUERIES, desc="Marketplace queries"):
            shopee_count = 0
            tokped_count = 0
            error_msg = None
            try:
                if target in ("shopee", "both"):
                    s_items = self._run_async(self._scrape_shopee(query, max_pages=max_pages))
                    s_items = s_items[:max_per_query]
                    all_items.extend(s_items)
                    shopee_count = len(s_items)
                if target in ("tokopedia", "both"):
                    t_items = self._run_async(self._scrape_tokopedia(query, max_pages=max_pages))
                    t_items = t_items[:max_per_query]
                    all_items.extend(t_items)
                    tokped_count = len(t_items)
            except Exception as exc:
                log.warning("Marketplace query '%s' error: %s", query, exc)
                error_msg = str(exc)
            per_query.append(
                {
                    "query": query,
                    "shopee": shopee_count,
                    "tokopedia": tokped_count,
                    "total": shopee_count + tokped_count,
                    **({"error": error_msg} if error_msg else {}),
                }
            )
            self.polite_sleep()

        # Dedup by (marketplace, url)
        seen: set[tuple[str, str]] = set()
        unique_items: list[dict] = []
        for item in all_items:
            key = (item["marketplace"], item["url"])
            if key in seen or not item.get("url"):
                continue
            seen.add(key)
            unique_items.append(item)
        all_items = unique_items

        # Summary stats
        n_shopee = sum(1 for i in all_items if i["marketplace"] == "shopee")
        n_tokped = sum(1 for i in all_items if i["marketplace"] == "tokopedia")
        n_finansial = sum(1 for i in all_items if i["is_finansial_keyword"])

        meta = self.meta(
            "marketplace",
            {
                "n_total": len(all_items),
                "n_shopee": n_shopee,
                "n_tokopedia": n_tokped,
                "n_finansial_keyword": n_finansial,
                "queries": QUERIES,
                "max_pages": max_pages,
                "max_per_query": max_per_query,
                "target": target,
                "per_query": per_query,
            },
        )

        out = {"meta": meta, "items": all_items}
        self.save_json(out, "marketplace_all.json", subdir="raw")

        sample = all_items[:1000] if len(all_items) > 1000 else all_items
        self.save_json({**out, "items": sample}, "marketplace_sample.json", subdir="sample")

        log.info(
            "Marketplace: %d items (%d shopee, %d tokopedia, %d finansial-keyword)",
            len(all_items), n_shopee, n_tokped, n_finansial,
        )
        return {
            "status": "ok" if all_items else "no_data",
            "n_total": len(all_items),
            "n_shopee": n_shopee,
            "n_tokopedia": n_tokped,
            "n_finansial_keyword": n_finansial,
            "queries": QUERIES,
            "target": target,
        }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    target = sys.argv[1] if len(sys.argv) > 1 else "both"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    result = MarketplaceScraper().run(marketplace=target, max_pages=pages)
    print(result)
