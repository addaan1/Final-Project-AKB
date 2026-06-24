"""Parallel OJK scraper — get more articles by paginating listing pages deeply."""
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

from scraper.base import RAW_DIR

log = logging.getLogger("scraper.ojk_fast")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "id-ID,id;q=0.9",
}

OJK_KEYWORDS = [
    "paylater", "pinjol", "pinjaman online", "fintech lending", "galbay",
    "gagal bayar", "kredit", "konsumen", "nasabah", "utang", "tagihan",
    "kartu kredit", "financial", "pinjaman", "ecommerce", "transaksi",
    "debt", "suku bunga", "bunga", "kredit digital", "konsumer",
]


def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return None


def is_relevant(text):
    t = text.lower()
    hits = sum(1 for kw in OJK_KEYWORDS if kw in t)
    return hits >= 1


def get_ojk_links(label, page_num):
    """Get article links from OJK listing page."""
    base = f"https://www.ojk.go.id/id/berita-dan-kegiatan/{label}/Default.aspx"
    # Try with paging variations
    urls = [f"{base}?page={page_num}", f"{base}"]
    seen = set()
    out = []
    for url in urls:
        html = fetch(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            title = a.get_text(strip=True)
            if f"/{label}/Pages/" in href and len(title) > 10 and href not in seen:
                if not href.startswith("http"):
                    href = "https://www.ojk.go.id" + href
                seen.add(href)
                out.append({"url": href, "title": title})
    return out


def get_ojk_article(link):
    """Fetch and parse one OJK article."""
    html = fetch(link["url"])
    if not html:
        return None
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    # Find content
    div = (soup.find("div", class_=re.compile(r"content|article|post", re.I))
           or soup.find("article")
           or soup.find("main"))
    if not div:
        return None
    paras = div.find_all("p")
    content = " ".join(p.get_text(strip=True) for p in paras)
    if not content or not is_relevant(link["title"] + " " + content):
        return None
    return {
        "source": f"ojk",
        "url": link["url"],
        "title": link["title"],
        "content": content[:3000],
        "scraped_at": time.time(),
    }


def task_for_page(label, page_num):
    links = get_ojk_links(label, page_num)
    out = []
    for link in links[:20]:
        art = get_ojk_article(link)
        if art:
            out.append(art)
    return out


def main():
    logging.basicConfig(level=logging.WARNING)
    t0 = time.time()
    tasks = []
    for label in ["siaran-pers", "info-terkini"]:
        for page in range(1, 8):  # 7 pages per category = 14 listing pages
            tasks.append((label, page))
    print(f"Tasks: {len(tasks)}")
    new_articles = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(task_for_page, l, p): (l, p) for l, p in tasks}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="OJK pages"):
            try:
                arts = fut.result(timeout=30)
                new_articles.extend(arts)
            except Exception:
                pass
    # Load existing
    existing = []
    p = Path(RAW_DIR, "ojk_articles.json")
    if p.exists():
        try:
            d = json.load(open(p, encoding="utf-8"))
            if "ojk" in d and isinstance(d["ojk"], list):
                existing.extend(d["ojk"])
            elif "articles" in d and isinstance(d["articles"], list):
                existing.extend(d["articles"])
        except Exception:
            pass
    # Merge + dedup
    seen = set()
    unique = []
    for a in existing + new_articles:
        if a.get("url") and a["url"] not in seen:
            seen.add(a["url"])
            unique.append(a)
    out = {
        "meta": {
            "source": "ojk",
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "n_total": len(unique),
            "n_existing": len(existing),
            "n_new": len(new_articles),
        },
        "ojk": unique,
    }
    Path(RAW_DIR, "ojk_articles.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nMerged: {len(existing)} existing + {len(new_articles)} new = {len(unique)} total in {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
