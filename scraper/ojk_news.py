"""Scraper berita & siaran pers OJK + media besar (PRIORITAS 6).

OJK: ojk.go.id (siaran pers, info terkini, regulasi).
Media: kompas.com, detik.com, cnbcindonesia.com.

URL OJK benar:
- https://www.ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Default.aspx
- https://www.ojk.go.id/id/berita-dan-kegiatan/info-terkini/Default.aspx

Volume rendah-menengah tapi relevansi tinggi sebagai sinyal regulator & market.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.ojk_news")

OJK_LISTING_PAGES: list[dict] = [
    {
        "label": "siaran_pers",
        "url": "https://www.ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Default.aspx",
        "link_pattern": "/siaran-pers/Pages/",
    },
    {
        "label": "info_terkini",
        "url": "https://www.ojk.go.id/id/berita-dan-kegiatan/info-terkini/Default.aspx",
        "link_pattern": "/info-terkini/Pages/",
    },
]

OJK_KEYWORDS: list[str] = [
    "paylater",
    "pinjol",
    "pinjaman online",
    "fintech lending",
    "galbay",
    "gagal bayar",
    "kredit",
    "konsumen",
    "nasabah",
]

MEDIA_QUERIES: list[str] = [
    "galbay paylater",
    "pinjol gagal bayar",
    "fintech paylater",
    "pinjaman online macet",
    "ditagih paylater",
    "galbay pinjol",
    "paylater indonesia",
    "pinjol legal",
]

MEDIA_SOURCES: dict[str, str] = {
    "kompas": "https://search.kompas.com/search",
    "detik": "https://www.detik.com/search/searchall",
    "cnbc": "https://www.cnbcindonesia.com/search",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}


class OjkNewsScraper(BaseScraper):
    name = "ojk_news"

    def _fetch_page(self, url: str) -> str | None:
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code == 200:
                return response.text
            log.warning("Status %d untuk %s", response.status_code, url)
        except Exception as exc:
            log.warning("Gagal fetch %s: %s", url, exc)
        return None

    def _scrape_ojk_listing(self, page: dict, max_articles: int = 20) -> list[dict]:
        """Scrape OJK listing page, extract article links, lalu visit tiap artikel."""
        html = self._fetch_page(page["url"])
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        article_links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if page["link_pattern"] in href:
                if not href.startswith("http"):
                    href = "https://www.ojk.go.id" + href
                title = anchor.get_text(strip=True)
                if title and len(title) > 10:
                    article_links.append({"url": href, "title": title})

        article_links = article_links[:max_articles]
        log.info("OJK %s: %d article links", page["label"], len(article_links))

        articles = []
        for link in tqdm(article_links, desc=f"OJK {page['label']}"):
            html = self._fetch_page(link["url"])
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")

            content_div = (
                soup.find("div", class_=re.compile(r"content|article|post", re.I))
                or soup.find("article")
                or soup.find("main")
                or soup.find("div", id=re.compile(r"content|article", re.I))
            )
            content = ""
            if content_div:
                paragraphs = content_div.find_all("p")
                content = " ".join(paragraph.get_text(strip=True) for paragraph in paragraphs)
            if not content:
                paragraphs = soup.find_all("p")
                content = " ".join(
                    paragraph.get_text(strip=True)
                    for paragraph in paragraphs
                    if len(paragraph.get_text(strip=True)) > 20
                )

            full_text = (link["title"] + " " + content).lower()
            if any(keyword in full_text for keyword in OJK_KEYWORDS):
                articles.append(
                    {
                        "source": f"ojk_{page['label']}",
                        "url": link["url"],
                        "title": link["title"],
                        "content": content[:3000],
                        "scraped_at": time.time(),
                    }
                )
            self.polite_sleep()

        log.info("OJK %s: %d artikel relevan", page["label"], len(articles))
        return articles

    def _scrape_media_listing(self, media_name: str, search_url: str, query: str) -> list[dict]:
        """Scrape halaman pencarian media lalu extract article links."""
        try:
            params = {"q": query}
            if media_name == "detik":
                params["site"] = "all"
            elif media_name == "cnbc":
                params["query"] = query
            response = requests.get(search_url, params=params, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                log.warning("%s search '%s' status %d", media_name, query, response.status_code)
                return []
        except Exception as exc:
            log.warning("Gagal %s search '%s': %s", media_name, query, exc)
            return []

        soup = BeautifulSoup(response.text, "lxml")
        article_links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            title = anchor.get_text(strip=True)

            if media_name == "kompas" and "kompas.com/read" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "detik" and "detik.com" in href and "/berita/" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif (
                media_name == "cnbc"
                and "cnbcindonesia.com" in href
                and "connect.detik" not in href
                and "oauth" not in href
                and len(title) > 15
            ):
                article_links.append({"url": href, "title": title})

        seen = set()
        unique = []
        for link in article_links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique.append(link)

        log.info("%s '%s': %d article links", media_name, query, len(unique))
        return unique

    def _scrape_media_article(self, media_name: str, url: str, title: str) -> dict | None:
        """Visit satu artikel lalu extract content."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=20)
            if response.status_code != 200:
                return None
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        if media_name == "kompas":
            content_div = soup.find("div", class_=re.compile(r"read__content|article__content", re.I))
        elif media_name == "detik":
            content_div = soup.find("div", class_=re.compile(r"detail__body|itp_bodycontent", re.I))
        elif media_name == "cnbc":
            content_div = soup.find("div", class_=re.compile(r"detail__body|article|content", re.I))
        else:
            content_div = None

        if not content_div:
            content_div = soup.find("article") or soup.find("main")

        content = ""
        if content_div:
            paragraphs = content_div.find_all("p")
            content = " ".join(paragraph.get_text(strip=True) for paragraph in paragraphs)

        if not content:
            return None

        return {
            "source": media_name,
            "url": url,
            "title": title,
            "content": content[:3000],
            "scraped_at": time.time(),
        }

    def run(self, max_ojk_articles: int = 20, max_media_per_query: int = 10) -> dict[str, Any]:
        """Jalankan scraping OJK dan media besar."""
        ojk_articles = []
        for page in OJK_LISTING_PAGES:
            ojk_articles.extend(self._scrape_ojk_listing(page, max_articles=max_ojk_articles))

        media_articles = []
        for media_name, search_url in MEDIA_SOURCES.items():
            for query in MEDIA_QUERIES:
                links = self._scrape_media_listing(media_name, search_url, query)
                for link in links[:max_media_per_query]:
                    article = self._scrape_media_article(media_name, link["url"], link["title"])
                    if article:
                        media_articles.append(article)
                    self.polite_sleep()

        all_articles = ojk_articles + media_articles
        meta = self.meta(
            "ojk_news",
            {
                "n_ojk": len(ojk_articles),
                "n_media": len(media_articles),
                "n_total": len(all_articles),
                "ojk_keywords": OJK_KEYWORDS,
                "media_queries": MEDIA_QUERIES,
                "media_sources": list(MEDIA_SOURCES.keys()),
            },
        )

        self.save_json({"meta": meta, "ojk": ojk_articles}, "ojk_articles.json", subdir="raw")
        self.save_json({"meta": meta, "media": media_articles}, "media_articles.json", subdir="raw")
        self.save_json({"meta": meta, "all": all_articles}, "news_all.json", subdir="raw")

        sample = all_articles[:500] if len(all_articles) > 500 else all_articles
        self.save_json({"meta": meta, "sample": sample}, "news_sample.json", subdir="sample")

        log.info("News: %d OJK + %d media = %d total", len(ojk_articles), len(media_articles), len(all_articles))
        return {
            "status": "ok",
            "n_ojk": len(ojk_articles),
            "n_media": len(media_articles),
            "n_total": len(all_articles),
        }
