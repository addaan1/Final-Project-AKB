<<<<<<< HEAD
"""Scraper berita & siaran pers OJK + media besar (PRIORITAS 6).

OJK: ojk.go.id (siaran pers, info terkini, regulasi).
Media: kompas.com, detik.com, cnbcindonesia.com.

URL OJK benar:
- https://www.ojk.go.id/id/berita-dan-kegiatan/siaran-pers/Default.aspx
- https://www.ojk.go.id/id/berita-dan-kegiatan/info-terkini/Default.aspx
=======
"""Scraper berita & siaran pers OJK (PRIORITAS 6).

STUB — rencana:
- OJK: scrape siaran pers & regulasi paylater/pinjol dari ojk.go.id.
- Media: crawler berita (kompas, detik, cnbc) keyword "galbay"/"paylater".
>>>>>>> origin/main

Volume rendah-menengah tapi relevansi tinggi sebagai sinyal regulator & market.
"""
from __future__ import annotations

<<<<<<< HEAD
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
    "paylater", "pinjol", "pinjaman online", "fintech lending",
    "galbay", "gagal bayar", "kredit", "konsumen", "nasabah",
]

MEDIA_QUERIES: list[str] = [
    "galbay paylater", "pinjol gagal bayar", "fintech paylater",
    "pinjaman online macet", "ditagih paylater", "galbay pinjol",
    "paylater indonesia", "pinjol legal",
]

MEDIA_SOURCES: dict[str, str] = {
    "kompas": "https://search.kompas.com/search",
    "detik": "https://www.detik.com/search/searchall",
    "cnbc": "https://www.cnbcindonesia.com/search",
    "antara": "https://www.antaranews.com/search",
    "jawapos": "https://www.jawapos.com/search",
    "tribunnews": "https://www.tribunnews.com/search",
    "republika": "https://republika.co.id/search",
    "suara": "https://www.suara.com/search",
    "kontan": "https://www.kontan.co.id/search",
    "tempo": "https://tempo.co/search",
    "merdeka": "https://www.merdeka.com/search",
    "jpnn": "https://www.jpnn.com/search",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

=======
from scraper.base import BaseScraper

>>>>>>> origin/main

class OjkNewsScraper(BaseScraper):
    name = "ojk_news"

<<<<<<< HEAD
    def _fetch_page(self, url: str) -> str | None:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            log.warning("Status %d untuk %s", r.status_code, url)
        except Exception as e:
            log.warning("Gagal fetch %s: %s", url, e)
        return None

    def _scrape_ojk_listing(self, page: dict, max_articles: int = 20) -> list[dict]:
        """Scrape OJK listing page → extract article links → visit each."""
        html = self._fetch_page(page["url"])
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        all_links = soup.find_all("a", href=True)
        article_links = []
        for a in all_links:
            href = a.get("href", "")
            if page["link_pattern"] in href:
                if not href.startswith("http"):
                    href = "https://www.ojk.go.id" + href
                title = a.get_text(strip=True)
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

            # Extract main content
            content_div = (
                soup.find("div", class_=re.compile(r"content|article|post", re.I))
                or soup.find("article")
                or soup.find("main")
                or soup.find("div", id=re.compile(r"content|article", re.I))
            )
            content = ""
            if content_div:
                paragraphs = content_div.find_all("p")
                content = " ".join(p.get_text(strip=True) for p in paragraphs)
            if not content:
                # fallback: semua paragraf
                paragraphs = soup.find_all("p")
                content = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20)

            # Filter keyword
            full_text = (link["title"] + " " + content).lower()
            if any(kw in full_text for kw in OJK_KEYWORDS):
                articles.append({
                    "source": f"ojk_{page['label']}",
                    "url": link["url"],
                    "title": link["title"],
                    "content": content[:3000],
                    "scraped_at": time.time(),
                })
            self.polite_sleep()

        log.info("OJK %s: %d artikel relevan", page["label"], len(articles))
        return articles

    def _scrape_media_listing(self, media_name: str, search_url: str, query: str) -> list[dict]:
        """Scrape media search page → extract article links."""
        try:
            params = {"q": query}
            if media_name == "detik":
                params["site"] = "all"
            elif media_name == "cnbc":
                params["query"] = query
            r = requests.get(search_url, params=params, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                log.warning("%s search '%s' status %d", media_name, query, r.status_code)
                return []
        except Exception as e:
            log.warning("Gagal %s search '%s': %s", media_name, query, e)
            return []

        soup = BeautifulSoup(r.text, "lxml")
        article_links = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            title = a.get_text(strip=True)

            if media_name == "kompas" and "kompas.com/read" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "detik" and "detik.com" in href and "/berita/" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "cnbc" and "cnbcindonesia.com" in href and "connect.detik" not in href and "oauth" not in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "antara" and "antaranews.com" in href and "/berita/" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "jawapos" and "jawapos.com" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "tribunnews" and "tribunnews.com" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "republika" and "republika.co.id" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "suara" and "suara.com" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "kontan" and "kontan.co.id" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "tempo" and "tempo.co" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "merdeka" and "merdeka.com" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})
            elif media_name == "jpnn" and "jpnn.com" in href and len(title) > 15:
                article_links.append({"url": href, "title": title})

        # Dedup by URL
        seen = set()
        unique = []
        for link in article_links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique.append(link)

        log.info("%s '%s': %d article links", media_name, query, len(unique))
        return unique

    def _scrape_media_article(self, media_name: str, url: str, title: str) -> dict | None:
        """Visit satu artikel → extract content."""
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                return None
        except Exception:
            return None

        soup = BeautifulSoup(r.text, "lxml")
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract content
        if media_name == "kompas":
            content_div = soup.find("div", class_=re.compile(r"read__content|article__content", re.I))
        elif media_name == "detik":
            content_div = soup.find("div", class_=re.compile(r"detail__body|itp_bodycontent", re.I))
        elif media_name == "cnbc":
            content_div = soup.find("div", class_=re.compile(r"detail__body|article|content", re.I))
        else:
            content_div = (
                soup.find("div", class_=re.compile(r"content|article|post|detail|berita", re.I))
                or soup.find("article")
            )

        if not content_div:
            content_div = soup.find("article") or soup.find("main")

        content = ""
        if content_div:
            paragraphs = content_div.find_all("p")
            content = " ".join(p.get_text(strip=True) for p in paragraphs)

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
        """Jalankan scraping OJK + media besar."""
        # OJK
        ojk_articles = []
        for page in OJK_LISTING_PAGES:
            ojk_articles.extend(self._scrape_ojk_listing(page, max_articles=max_ojk_articles))

        # Media
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

        meta = self.meta("ojk_news", {
            "n_ojk": len(ojk_articles),
            "n_media": len(media_articles),
            "n_total": len(all_articles),
            "ojk_keywords": OJK_KEYWORDS,
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
=======
    def run(self, **kwargs):
        raise NotImplementedError(
            "OJK/news scraper belum diimplementasi. Eksplor: requests+BS4."
        )
>>>>>>> origin/main
