"""Scraper diskusi.kompas.com — alternative forum (Kaskus is 403).

Forum komunitas Kompas dengan banyak thread soal galbay/pinjol.
"""
from __future__ import annotations

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import RAW_DIR

log = logging.getLogger("scraper.diskusi_kompas")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9",
}

QUERIES = [
    "galbay paylater", "gagal bayar pinjol", "debt collector", "kredivo macet",
    "cicilan 0 persen", "tips bayar paylater", "pinjol ilegal", "utang online",
    "bunga tinggi", "restrukturisasi", "konsolidasi", "kartu kredit cicilan",
    "tagihan telat", "penagihan", "konsumer", "kredit pintar", "julo",
    "uangme", "koinworks", "amartha", "kta kilat", "negosiasi kredit",
]


def fetch(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def get_thread_links(query, max_pages=3):
    """Search diskusi.kompas for query, return thread links."""
    out = []
    seen = set()
    for page in range(1, max_pages + 1):
        url = f"https://diskusi.kompas.com/search?q={quote(query)}&page={page}"
        html = fetch(url)
        if not html:
            break
        soup = BeautifulSoup(html, "lxml")
        found = 0
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)
            if ("diskusi.kompas.com" in href
                and "/komentar-" not in href
                and len(title) > 20
                and "search" not in href
                and href not in seen):
                seen.add(href)
                out.append({"url": href, "title": title, "query": query})
                found += 1
                if len(out) >= 30:
                    return out
        if found == 0:
            break
    return out


def get_thread_posts(url, query):
    """Get posts (original post + replies) from a thread."""
    html = fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out = []
    # Try common post containers
    for div in soup.find_all("div", class_=re.compile(r"post|message|comment|komentar", re.I)):
        text = div.get_text(" ", strip=True)
        if len(text) > 50:
            out.append({
                "source": "diskusi_kompas",
                "query": query,
                "thread_url": url,
                "text": text[:1500],
                "scraped_at": time.time(),
            })
    if not out:
        # Fallback: get all <p> with substantial text
        for p in soup.find_all("p"):
            t = p.get_text(strip=True)
            if len(t) > 50:
                out.append({
                    "source": "diskusi_kompas",
                    "query": query,
                    "thread_url": url,
                    "text": t[:1500],
                    "scraped_at": time.time(),
                })
    return out


def main():
    logging.basicConfig(level=logging.WARNING)
    t0 = time.time()
    print(f"Queries: {len(QUERIES)}")
    all_links = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(get_thread_links, q): q for q in QUERIES}
        for f in tqdm(as_completed(futs), total=len(futs), desc="search links"):
            try:
                links = f.result(timeout=30)
                all_links.extend(links)
            except Exception:
                pass
    # Dedup
    seen = set()
    unique_links = []
    for l in all_links:
        if l["url"] not in seen:
            seen.add(l["url"])
            unique_links.append(l)
    print(f"Got {len(unique_links)} unique threads")
    all_posts = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(get_thread_posts, l["url"], l["query"]): l for l in unique_links[:200]}
        for f in tqdm(as_completed(futs), total=len(futs), desc="fetch posts"):
            try:
                posts = f.result(timeout=15)
                all_posts.extend(posts)
            except Exception:
                pass
    out = {
        "meta": {
            "source": "diskusi_kompas",
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_threads": len(unique_links),
            "n_posts": len(all_posts),
            "queries": QUERIES,
        },
        "posts": all_posts,
        "threads": unique_links,
    }
    Path(RAW_DIR, "diskusi_kompas.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    # Sample
    sample = all_posts[:500]
    Path("data/sample").mkdir(exist_ok=True)
    Path("data/sample/diskusi_kompas_sample.json").write_text(
        json.dumps({**out, "posts": sample}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nTotal: {len(all_posts)} posts in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
