"""Scraper Apple App Store reviews (PRIORITAS 7 - baru, no login).

Menggunakan app_store_scraper untuk mengambil review iOS dari app fintech.
Tidak perlu login/API key. Volume menengah, demografi user iOS (berbeda dari Android).
"""
from __future__ import annotations

import logging
from typing import Any

from app_store_scraper import AppStore
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.appstore_reviews")

APPSTORE_IDS: dict[str, dict] = {
    "Kredivo": {"app_id": "1474527998", "category": "paylater"},
    "Akulaku": {"app_id": "1485443341", "category": "paylater"},
    "Shopee": {"app_id": "959841443", "category": "ecommerce"},
    "Tokopedia": {"app_id": "1001394201", "category": "ecommerce"},
    "Lazada": {"app_id": "785385147", "category": "ecommerce"},
    "Traveloka": {"app_id": "898244530", "category": "travel"},
    "Gojek": {"app_id": "944875099", "category": "ewallet"},
    "OVO": {"app_id": "1276197286", "category": "ewallet"},
    "DANA": {"app_id": "1436496446", "category": "ewallet"},
    "JULO": {"app_id": "1404980061", "category": "pinjol"},
    "Kredit Pintar": {"app_id": "1398423853", "category": "pinjol"},
    "RupiahCepat": {"app_id": "1451294871", "category": "pinjol"},
    "Bukalapak": {"app_id": "1003169137", "category": "ecommerce"},
    "SeaBank": {"app_id": "1599575853", "category": "bank_digital"},
    "Bank Jago": {"app_id": "1546211820", "category": "bank_digital"},
}

MAX_REVIEWS_PER_APP = 5000


class AppStoreReviewsScraper(BaseScraper):
    name = "appstore_reviews"

    @staticmethod
    def _normalize_row(r: dict, app: dict) -> dict:
        return {
            "app_id": app["app_id"],
            "app_name": app.get("query"),
            "query": app.get("query"),
            "category": app.get("category"),
            "review_id": str(r.get("reviewId", r.get("id", ""))),
            "score": r.get("rating"),
            "title": r.get("title", ""),
            "content": (r.get("review") or "").strip(),
            "thumbs_up": r.get("helpfulCount", 0),
            "at": r.get("date").isoformat() if r.get("date") else None,
            "user_name": "[anonymized]",
        }

    def fetch_reviews(self, app: dict, count: int = MAX_REVIEWS_PER_APP) -> list[dict]:
        app_id = app["app_id"]
        rows = []
        try:
            store = AppStore(country="id", app_name=app.get("query", ""), app_id=app_id)
            store.review(how_many=count)
            for r in store.reviews:
                rows.append(self._normalize_row(r, app))
        except Exception as e:
            log.warning("Gagal fetch %s (%s): %s", app.get("query"), app_id, e)
        return rows

    def _flag_relevant(self, rows: list[dict]) -> list[dict]:
        for row in rows:
            text = (row.get("content") or "").lower()
            row["is_relevant"] = any(kw in text for kw in [
                "galbay", "gagal bayar", "paylater", "pinjol",
                "cicilan", "tagihan", "bunga", "telat bayar", "nunggak",
            ])
        return rows

    def run(self, count: int = MAX_REVIEWS_PER_APP, app_limit: int = 0) -> dict[str, Any]:
        all_rows = []
        per_app_summary = []
        apps = list(APPSTORE_IDS.items())
        if app_limit:
            apps = apps[:app_limit]
        for name, info in tqdm(apps, desc="App Store reviews"):
            app_meta = {"query": name, "app_id": info["app_id"], "category": info["category"]}
            rows = self.fetch_reviews(app_meta, count=count)
            rows = self._flag_relevant(rows)
            all_rows.extend(rows)
            per_app_summary.append({
                "app_name": name, "app_id": info["app_id"],
                "category": info["category"], "n_reviews": len(rows),
                "n_relevant": sum(1 for r in rows if r.get("is_relevant")),
            })
            self.polite_sleep()
        meta = self.meta("apple_app_store", {
            "n_apps": len(apps), "n_reviews_total": len(all_rows),
            "country": "id", "count_per_app": count if count != MAX_REVIEWS_PER_APP else None,
            "per_app": per_app_summary,
        })
        self.save_json({"meta": meta, "reviews": all_rows}, "appstore_reviews_all.json", subdir="raw")
        sample = all_rows[:1000] if len(all_rows) > 1000 else all_rows
        self.save_json({"meta": meta, "reviews": sample}, "appstore_reviews_sample.json", subdir="sample")
        return {
            "status": "ok", "n_apps": len(apps), "n_reviews_total": len(all_rows),
            "n_relevant": sum(1 for r in all_rows if r.get("is_relevant")),
            "per_app": per_app_summary,
        }
