"""Scraper berita & siaran pers OJK + media besar (PRIORITAS 6).

OJK: ojk.go.id (siaran pers, regulasi, berita).
Media: kompas.com, detik.com, cnbcindonesia.com.

Volume rendah-menengah tapi relevansi tinggi sebagai sinyal regulator & market.
"""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.ojk_news")

OJK_QUERIES: list[str] = [
    "paylater", "pinjol", "fintech", "gagal bayar",
    "pinjaman online", "literasi keuangan",
]

MEDIA_QUERIES: list[str] = [
    "galbay paylater", "pinjol gagal bayar", "fintech paylater",
    "pinjaman online macet", "ditagih paylater",
]

OJK_BASE_URL = "https://www.ojk.go.id"
OJK_SEARCH_URL = f"{OJK_BASE_URL}/id/berita-dan-kegiatan/siaran-pers/Pages/default.aspx"

MEDIA_SOURCES: dict[str, str] = {
    "kompas": "https://search.kompas.com/search",
    "detik": "https://www.detik.com/search/searchall",
    "cnbc": "https://www.cnbcindonesia.com/search",
}


class OjkNewsScraper(BaseScraper):
    name = "ojk_news"

    def _scrape_ojk(self, max_per_query: int = 30) -> list[dict]:
        """Scrape OJK siaran pers & berita."""
        articles = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html",
            "Accept-Language": "id-ID,id;q=0.9",
        }

        for query in tqdm(OJK_QUERIES, desc="OJK search"):
            try:
                params = {"q": query, "s": "relevance"}
                resp = requests.get(OJK_SEARCH_URL, params=params, headers=headers, timeout=15)
                if resp.status_code != 200:
                    log.warning("OJK search '%s' status %d", query, resp.status_code)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                items = soup.select("div.search-result-item, article.news-item, div.item-berita")

                if not items:
                    items = soup.select("div.row, li.search-result, div.content-item")

                count = 0
                for item in items:
                    if count >= max_per_query:
                        break
                    try:
                        title_el = item.select_one("h2 a, h3 a, a.title, a.news-title")
                        if not title_el:
                            title_el = item.select_one("a")
                        if not title_el:
                            continue

                        title = title_el.get_text(strip=True)
                        url = title_el.get("href", "")
                        if url and not url.startswith("http"):
                            url = OJK_BASE_URL + url

                        snippet_el = item.select_one("p.snippet, div.snippet, p.description, span.summary")
                        snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                        date_el = item.select_one("span.date, time, span.meta-date, span.tanggal")
                        date_str = date_el.get_text(strip=True) if date_el else ""

                        articles.append({
                            "source": "ojk",
                            "query": query,
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "date": date_str,
                            "scraped_at": time.time(),
                        })
                        count += 1
                    except Exception as e:
                        log.warning("Error parse OJK item: %s", e)

                log.info("OJK '%s': %d articles", query, count)
                self.polite_sleep()

            except Exception as e:
                log.warning("Gagal scrape OJK '%s': %s", query, e)

        return articles

    def _scrape_media(self, max_per_query: int = 30) -> list[dict]:
        """Scrape media besar (kompas, detik, cnbc)."""
        articles = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html",
        }

        for media_name, search_url in tqdm(MEDIA_SOURCES.items(), desc="Media search"):
            for query in MEDIA_QUERIES:
                try:
                    params = {"q": query}
                    if media_name == "detik":
                        params["site"] = "all"
                    elif media_name == "cnbc":
                        params["search_query"] = query

                    resp = requests.get(search_url, params=params, headers=headers, timeout=15)
                    if resp.status_code != 200:
                        log.warning("%s search '%s' status %d", media_name, query, resp.status_code)
                        continue

                    soup = BeautifulSoup(resp.text, "lxml")

                    if media_name == "kompas":
                        items = soup.select("div.search-result-item, article, div.card")
                    elif media_name == "detik":
                        items = soup.select("div.list-konten, article, div.search-result")
                    elif media_name == "cnbc":
                        items = soup.select("div.search-item, article, div.list-news")
                    else:
                        items = []

                    count = 0
                    for item in items:
                        if count >= max_per_query:
                            break
                        try:
                            title_el = item.select_one("h2 a, h3 a, a.title, a.news-title, h1 a")
                            if not title_el:
                                title_el = item.select_one("a[href]")
                            if not title_el:
                                continue

                            title = title_el.get_text(strip=True)
                            url = title_el.get("href", "")
                            if url and not url.startswith("http"):
                                if media_name == "kompas":
                                    url = "https://www.kompas.com" + url
                                elif media_name == "detik":
                                    url = "https://www.detik.com" + url
                                elif media_name == "cnbc":
                                    url = "https://www.cnbcindonesia.com" + url

                            snippet_el = item.select_one("p, div.snippet, div.summary, span.lead")
                            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                            if len(snippet) > 500:
                                snippet = snippet[:500] + "..."

                            date_el = item.select_one("span.date, time, div.date, span.meta-date")
                            date_str = date_el.get_text(strip=True) if date_el else ""

                            articles.append({
                                "source": media_name,
                                "query": query,
                                "title": title,
                                "url": url,
                                "snippet": snippet,
                                "date": date_str,
                                "scraped_at": time.time(),
                            })
                            count += 1
                        except Exception as e:
                            log.warning("Error parse %s item: %s", media_name, e)

                    log.info("%s '%s': %d articles", media_name, query, count)
                    self.polite_sleep()

                except Exception as e:
                    log.warning("Gagal scrape %s '%s': %s", media_name, query, e)

        return articles

    def run(self, max_per_query: int = 30) -> dict[str, Any]:
        """Jalankan scraping OJK + media besar."""
        ojk_articles = self._scrape_ojk(max_per_query=max_per_query)
        media_articles = self._scrape_media(max_per_query=max_per_query)

        all_articles = ojk_articles + media_articles

        meta = self.meta("ojk_news", {
            "n_ojk": len(ojk_articles),
            "n_media": len(media_articles),
            "n_total": len(all_articles),
            "ojk_queries": OJK_QUERIES,
            "media_queries": MEDIA_QUERIES,
            "media_sources": list(MEDIA_SOURCES.keys()),
        })

        self.save_json({"meta": meta, "ojk": ojk_articles}, "ojk_articles.json", subdir="raw")
        self.save_json({"meta": meta, "media": media_articles}, "media_articles.json", subdir="raw")
        self.save_json({"meta": meta, "all": all_articles}, "news_all.json", subdir="raw")

        sample = all_articles[:500] if len(all_articles) > 500 else all_articles
        self.save_json({"meta": meta, "sample": sample}, "news_sample.json", subdir="sample")

        log.info("News: %d OJK + %d media = %d total",
                 len(ojk_articles), len(media_articles), len(all_articles))

        return {
            "status": "ok",
            "n_ojk": len(ojk_articles),
            "n_media": len(media_articles),
            "n_total": len(all_articles),
        }
