"""Scraper Google Play reviews aplikasi fintech Indonesia (PRIORITAS 1).

Menggunakan google-play-scraper. Ini penggerak utama volume big data:
~20 app x ratusan ribu review potensial.

Etika:
- Data publik (review app store).
- Tidak menyimpan PII; reviewId userName kita redact/buang di tahap processed.
- Rate-limit sopan via polite_sleep().
"""
from __future__ import annotations

import logging
from typing import Any

from google_play_scraper import reviews, search, Sort
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.fintech_reviews")

# Curated appId fintech Indonesia (terverifikasi via app() lookup).
# Kategori: paylater/BNPL, e-wallet, e-commerce (dengan paylater), pinjol.
# Catatan: beberapa pinjol kecil (AdaKami, Easycash, Julo, UangMe, TunaiKita,
# Atome, Tunaiku, Pintarnya) TIDAK ditemukan di Play Store — kemungkinan
# delist akibat penegakan OJK. Itu sendiri temuan data regulator.
APP_IDS: dict[str, str] = {
    "Kredivo": "com.finaccel.android",
    "Akulaku": "io.silvrr.installment",
    "Indodana": "com.indodana.app",
    "Shopee": "com.shopee.id",
    "Tokopedia": "com.tokopedia.tkpd",
    "Lazada": "com.lazada.android",
    "Traveloka": "com.traveloka.android",
    "Tiket.com": "com.tiket.gits",
    "Gojek": "com.gojek.app",
    "OVO": "ovo.id",
    "DANA": "id.dana",
    "LinkAja": "com.telkom.mwallet",
    "RupiahCepat": "com.loan.cash.credit.easy.kilat.cepat.pinjam.uang.dana.rupiah",
    "KreditPintar": "com.kreditpintar",
}

# Keyword bahasa sinyal galbay untuk filtering konten relevan
GALBAY_KEYWORDS: tuple[str, ...] = (
    "galbay", "gagal bayar", "ditagih", "tagihan", "tagih", "dendanya",
    "bunga", "menagih", "debt collector", "dc", "dicerewet", "kasbon",
    "paylater", "pay later", "pinjol", "pinjaman online", "cicilan",
    "telat bayar", "nunggak", "macet", "limit", "penagih",
)


class GooglePlayReviewsScraper(BaseScraper):
    name = "fintech_reviews"

    def resolve_apps(self, queries: list[str] | None = None, app_limit: int = 0) -> list[dict]:
        """Resolve app_id untuk setiap nama. Pakai curated APP_IDS (reliable);
        fallback ke search() jika nama tidak ada di dict. Return list
        {query, app_id, title, score}."""
        from google_play_scraper import app as app_info
        names = queries or list(APP_IDS.keys())
        resolved = []
        for name in tqdm(names, desc="Resolve app"):
            app_id = APP_IDS.get(name)
            if app_id:
                try:
                    info = app_info(app_id, lang="id", country="id")
                    resolved.append({
                        "query": name,
                        "app_id": app_id,
                        "title": info.get("title"),
                        "score": info.get("score"),
                        "installs": info.get("installs"),
                    })
                    self.polite_sleep()
                    continue
                except Exception as e:
                    log.warning("Curated appId '%s' gagal verifikasi: %s", app_id, e)
            # fallback: search() dan ambil hasil pertama dengan appId non-None
            try:
                results = search(name, lang="id", country="id", n_hits=8)
                for r in results:
                    aid = r.get("appId")
                    if aid:
                        resolved.append({
                            "query": name,
                            "app_id": aid,
                            "title": r.get("title"),
                            "score": r.get("score"),
                            "installs": None,
                        })
                        break
                else:
                    log.warning("Tidak ketemu appId valid untuk: %s", name)
                self.polite_sleep()
            except Exception as e:
                log.warning("Gagal resolve '%s': %s", name, e)
        if app_limit:
            resolved = resolved[:app_limit]
        log.info("Resolved %d app dari %d nama", len(resolved), len(names))
        return resolved

    def fetch_reviews(self, app: dict, count: int = 400) -> list[dict]:
        """Ambil review untuk satu app. count = jumlah review per app."""
        app_id = app["app_id"]
        try:
            result, _continuation = reviews(
                app_id,
                lang="id",
                country="id",
                sort=Sort.NEWEST,
                count=count,
                filter_score_with=None,
            )
        except Exception as e:
            log.warning("Gagal fetch reviews %s (%s): %s", app.get("title"), app_id, e)
            return []

        rows = []
        for r in result:
            content = (r.get("content") or "").strip()
            rows.append({
                "app_id": app_id,
                "app_name": app.get("title"),
                "query": app.get("query"),
                "review_id": r.get("reviewId"),
                "score": r.get("score"),
                "content": content,
                "thumbs_up": r.get("thumbsUpCount", 0),
                "at": r.get("at").isoformat() if r.get("at") else None,
                "replied": bool(r.get("replyContent")),
                "version": r.get("reviewCreatedVersion"),
            })
        return rows

    def _flag_relevant(self, rows: list[dict]) -> list[dict]:
        """Tandai baris yang mengandung keyword galbay (sinyal perilaku)."""
        for row in rows:
            text = (row.get("content") or "").lower()
            row["is_relevant"] = any(kw in text for kw in GALBAY_KEYWORDS)
        return rows

    def run(self, count: int = 400, app_limit: int = 0) -> dict[str, Any]:
        apps = self.resolve_apps(app_limit=app_limit)
        if not apps:
            return {"status": "no_apps", "resolved": 0}

        all_rows: list[dict] = []
        per_app_summary: list[dict] = []

        for app in tqdm(apps, desc="Fetch reviews"):
            rows = self.fetch_reviews(app, count=count)
            rows = self._flag_relevant(rows)
            all_rows.extend(rows)
            per_app_summary.append({
                "app_id": app["app_id"],
                "app_name": app.get("title"),
                "query": app.get("query"),
                "n_reviews": len(rows),
                "n_relevant": sum(1 for r in rows if r.get("is_relevant")),
            })
            # simpan per-app (raw, gitignored)
            safe = (app.get("query") or "app").replace(" ", "_").lower()
            self.save_json(rows, f"play_reviews_{safe}.json", subdir="raw")
            self.polite_sleep()

        # gabungan raw (gitignored)
        meta = self.meta("google_play_reviews", {
            "n_apps": len(apps),
            "n_reviews_total": len(all_rows),
            "count_per_app": count,
            "per_app": per_app_summary,
        })
        combined = {"meta": meta, "reviews": all_rows}
        self.save_json(combined, "play_reviews_all.json", subdir="raw")

        # sample kecil untuk di-commit (reproducibility)
        sample = all_rows[:1000] if len(all_rows) > 1000 else all_rows
        sample_payload = {"meta": meta, "reviews": sample}
        self.save_json(sample_payload, "play_reviews_sample.json", subdir="sample")

        n_relevant = sum(1 for r in all_rows if r.get("is_relevant"))
        log.info("Total %d review dari %d app (%d relevan galbay)",
                 len(all_rows), len(apps), n_relevant)

        return {
            "status": "ok",
            "n_apps": len(apps),
            "n_reviews_total": len(all_rows),
            "n_relevant": n_relevant,
            "sample_size": len(sample),
            "per_app": per_app_summary,
        }
