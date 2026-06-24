"""Rebuild play_reviews_all.json from per-app cache files.

This aggregates all per-app JSON files in data/raw/ into the master
play_reviews_all.json. Useful when scraping was done per-app and the
master file is stale.
"""
import json
from pathlib import Path
from datetime import datetime, timezone


RAW = Path("data/raw")
META = {
    "source": "google_play_reviews",
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "scraper": "fintech_reviews",
    "n_apps": 0,
    "n_reviews_total": 0,
    "mode": "aggregated_from_per_app",
    "per_app": [],
}

all_rows = []
per_app_summary = []

for cache in sorted(RAW.glob("play_reviews_*.json")):
    if "all" in cache.name or "sample" in cache.name:
        continue
    with cache.open(encoding="utf-8") as f:
        rows = json.load(f)
    if not rows or not isinstance(rows, list):
        continue
    all_rows.extend(rows)
    app_name = rows[0].get("app_name", cache.stem.replace("play_reviews_", ""))
    n_relevant = sum(1 for r in rows if r.get("is_relevant"))
    per_app_summary.append(
        {
            "cache_file": cache.name,
            "app_name": app_name,
            "n_reviews": len(rows),
            "n_relevant": n_relevant,
        }
    )
    print(f"  {cache.name}: {len(rows)} reviews, app={app_name}, relevant={n_relevant}")

META["n_apps"] = len(per_app_summary)
META["n_reviews_total"] = len(all_rows)
META["per_app"] = per_app_summary

out = RAW / "play_reviews_all.json"
with out.open("w", encoding="utf-8") as f:
    json.dump({"meta": META, "reviews": all_rows}, f, ensure_ascii=False, indent=2, default=str)

print(f"\nWrote {len(all_rows)} reviews from {len(per_app_summary)} apps to {out}")
print(f"File size: {out.stat().st_size / 1024 / 1024:.1f} MB")
