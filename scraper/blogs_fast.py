"""Parallel blog scraper — run multiple (blog, query) combinations concurrently.

Goal: 5-10K posts from 4-5 fast blogs × 50 queries × ~5 results per query.
Speed: ThreadPoolExecutor with 8 workers.
"""
from __future__ import annotations

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from scraper.base import RAW_DIR
from scraper.blogs_id import BLOG_QUERIES, BLOGS, HEADERS

log = logging.getLogger("scraper.blogs_fast")

# Curated list of blogs that historically return fast + many results
FAST_BLOGS = [
    "detik", "cnbc", "kompas", "idntimes", "tempo", "okezone", "merdeka",
]
BLOGS_BY_NAME = {b["name"]: b for b in BLOGS}

# We use ALL queries for max coverage
QUERIES = BLOG_QUERIES


def fetch(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception as e:
        pass
    return None


def extract_posts(html, blog_name, query, max_posts=20):
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        if (
            blog_name in href.lower()
            and len(title) > 25
            and "/search" not in href
            and "/tag/" not in href
        ):
            if not href.startswith("http"):
                href = "https:" + href if href.startswith("//") else f"https://{blog_name}.com{href}"
            out.append({
                "source": "blog_id",
                "blog": blog_name,
                "query": query,
                "title": title[:200],
                "url": href,
                "snippet": "",
                "scraped_at": time.time(),
            })
            if len(out) >= max_posts:
                break
    return out


def run_one(blog_name, query, max_posts=50, max_pages=4):
    """Scrape with pagination."""
    blog = BLOGS_BY_NAME.get(blog_name)
    if not blog:
        return []
    paged = blog.get("paged_url")
    all_posts = []
    for page in range(1, max_pages + 1):
        if page == 1 or not paged:
            url = blog["search_url"].format(q=quote(query))
        else:
            url = paged.format(q=quote(query), p=page)
        html = fetch(url)
        if not html:
            break
        page_posts = extract_posts(html, blog_name, query, max_posts)
        all_posts.extend(page_posts)
        if len(page_posts) < 3:
            break
    return all_posts[:max_posts]


def main():
    logging.basicConfig(level=logging.WARNING)
    t0 = time.time()
    tasks = []
    for blog_name in FAST_BLOGS:
        for q in QUERIES:
            tasks.append((blog_name, q))
    print(f"Tasks: {len(tasks)}")
    all_posts = []
    seen = set()
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(run_one, b, q): (b, q) for b, q in tasks}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="parallel"):
            posts = fut.result()
            for p in posts:
                if p["url"] not in seen:
                    seen.add(p["url"])
                    all_posts.append(p)
    # Save
    out = {
        "meta": {
            "source": "blogs_id",
            "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scraper": "blogs_fast",
            "n_total": len(all_posts),
            "queries": QUERIES,
            "blogs": FAST_BLOGS,
        },
        "posts": all_posts,
    }
    Path(RAW_DIR, "blogs_id.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    # Sample
    sample = all_posts[:500]
    sample_out = {**out, "posts": sample}
    Path(RAW_DIR.parent / "sample", "blogs_id_sample.json").parent.mkdir(exist_ok=True)
    Path(RAW_DIR, "..", "sample").resolve().mkdir(exist_ok=True)
    Path("data/sample/blogs_id_sample.json").write_text(
        json.dumps(sample_out, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nTotal: {len(all_posts)} posts in {time.time()-t0:.1f}s")
    from collections import Counter
    c = Counter(p["blog"] for p in all_posts)
    for k, v in c.most_common():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
