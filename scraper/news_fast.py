"""Parallel OJK + media scraper — fast expansion of regulator + media articles.

Goal: 5K+ articles from OJK listing + 3 media (detik, kompas, cnbc) × 30 queries.
Speed: ThreadPoolExecutor with 8 workers.
"""
from __future__ import annotations

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import RAW_DIR, SAMPLE_DIR

log = logging.getLogger("scraper.news_fast")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
}

OJK_KEYWORDS = [
    "paylater", "pinjol", "pinjaman online", "fintech", "galbay", "gagal bayar",
    "kredit", "konsumen", "nasabah", "utang", "debt", "tagihan", "kredit digital",
    "financial", "pinjaman", "kartu kredit", "ecommerce", "transaksi",
]

MEDIA_QUERIES = [
    "paylater indonesia", "pinjol indonesia", "gagal bayar paylater", "galbay pinjol",
    "cicilan 0 persen", "tips bayar paylater", "kredivo review", "akulaku review",
    "indodana review", "julo review", "kredit pintar review", "uangme review",
    "koinworks review", "amartha review", "modalku review", "investree review",
    "konsolidasi utang", "restrukturisasi kredit", "tips keluar dari galbay",
    "debt collector indonesia", "bunga pinjol tinggi", "pinjol ilegal ojk",
    "fintech lending", "literasi keuangan gen z", "menabung gen z",
    "tagihan paylater telat", "denda paylater", "negosiasi debt collector",
    "bayar cicilan minimum", "kartu kredit digital", "bank digital indonesia",
    "shopee paylater", "tokopedia paylater", "goPaylater", "dana paylater",
    "kredito review", "easycash review", "tunaiku review", "maupinjam review",
    "bunga majemuk", "utang konsumtif", "rasio utang", "skor kredit",
    "self reward belanja", "FOMO belanja online", "checkout bayar nanti",
    "tagihan shopee", "tagihan tokopedia", "tagihan kredivo", "tagihan akulaku",
    "kartu kredit cicilan", "promo cicilan 0", "cashback paylater",
    "cicilan online shopee", "cicilan online tokopedia", "kredit tanpa agunan",
    "pinjaman kilat", "pinjaman dana", "pinjaman modal usaha",
]

MEDIA_SEARCH = {
    "kompas": "https://search.kompas.com/search",
    "detik": "https://www.detik.com/search/searchall",
    "cnbc": "https://www.cnbcindonesia.com/search",
}


def fetch(url, params=None, timeout=10):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def is_relevant(text):
    t = text.lower()
    return any(kw in t for kw in OJK_KEYWORDS)


def get_media_links(media_name, search_url, query, max_links=15):
    """Get article links from media search page."""
    params = {"q": query}
    if media_name == "detik":
        params["site"] = "all"
    elif media_name == "cnbc":
        params["query"] = query
    html = fetch(search_url, params)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)
        match = False
        if media_name == "kompas" and "kompas.com/read" in href and len(title) > 15:
            match = True
        elif media_name == "detik" and "detik.com" in href and "/berita/" in href and len(title) > 15:
            match = True
        elif media_name == "cnbc" and "cnbcindonesia.com" in href and "connect.detik" not in href and len(title) > 15:
            match = True
        if match and href not in seen:
            seen.add(href)
            out.append({"url": href, "title": title})
            if len(out) >= max_links:
                break
    return out


def get_article_content(media_name, url, title):
    """Fetch article body text."""
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    if media_name == "kompas":
        div = soup.find("div", class_=re.compile(r"read__content|article__content", re.I))
    elif media_name == "detik":
        div = soup.find("div", class_=re.compile(r"detail__body|itp_bodycontent", re.I))
    elif media_name == "cnbc":
        div = soup.find("div", class_=re.compile(r"detail__body|article|content", re.I))
    else:
        div = None
    if not div:
        div = soup.find("article") or soup.find("main")
    if not div:
        return None
    paras = div.find_all("p")
    content = " ".join(p.get_text(strip=True) for p in paras)
    if not content or not is_relevant(title + " " + content):
        return None
    return {
        "source": media_name,
        "url": url,
        "title": title,
        "content": content[:3000],
        "scraped_at": time.time(),
    }


def media_task(media_name, query):
    search_url = MEDIA_SEARCH[media_name]
    links = get_media_links(media_name, search_url, query, max_links=10)
    out = []
    for link in links:
        art = get_article_content(media_name, link["url"], link["title"])
        if art:
            out.append(art)
    return out


def main():
    logging.basicConfig(level=logging.WARNING)
    t0 = time.time()
    tasks = []
    for media_name in MEDIA_SEARCH.keys():
        for q in MEDIA_QUERIES:
            tasks.append((media_name, q))
    print(f"Tasks: {len(tasks)}")
    new_articles = []
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = {ex.submit(media_task, m, q): (m, q) for m, q in tasks}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="media parallel"):
            try:
                articles = fut.result(timeout=30)
                new_articles.extend(articles)
            except Exception:
                pass
    # Load existing
    existing = []
    for fname in ("media_articles.json", "news_all.json"):
        p = Path(RAW_DIR, fname)
        if p.exists():
            try:
                d = json.load(open(p, encoding="utf-8"))
                for k in ("media", "all", "articles"):
                    if k in d and isinstance(d[k], list):
                        existing.extend(d[k])
                        break
            except Exception:
                pass
    # Merge + dedup by url
    seen = set()
    unique = []
    for a in existing + new_articles:
        if a.get("url") and a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    all_articles = unique
    # Save merged
    out = {
        "meta": {
            "source": "ojk_news",
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_total": len(all_articles),
            "n_new": len(new_articles),
            "queries": MEDIA_QUERIES,
            "media": list(MEDIA_SEARCH.keys()),
        },
        "media": all_articles,
        "all": all_articles,
    }
    Path(RAW_DIR, "media_articles.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    Path(RAW_DIR, "news_all.json").write_text(
        json.dumps({"meta": out["meta"], "all": all_articles}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    # Sample
    sample = all_articles[:500]
    Path(SAMPLE_DIR, "news_sample.json").parent.mkdir(exist_ok=True)
    Path(SAMPLE_DIR, "news_sample.json").write_text(
        json.dumps({"meta": out["meta"], "sample": sample}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nMerged: {len(existing)} existing + {len(new_articles)} new = {len(all_articles)} total in {time.time()-t0:.1f}s")
    from collections import Counter
    c = Counter(a.get("source", "?") for a in all_articles)
    for k, v in c.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
