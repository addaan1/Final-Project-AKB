"""Scraper Google Play reviews aplikasi fintech Indonesia (PRIORITAS 1)."""
from __future__ import annotations

import logging
from typing import Any

from google_play_scraper import Sort, reviews, reviews_all, search
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.fintech_reviews")

APP_IDS: dict[str, dict] = {
    "Kredivo": {"app_id": "com.finaccel.android", "category": "paylater"},
    "Akulaku": {"app_id": "io.silvrr.installment", "category": "paylater"},
    "Indodana": {"app_id": "com.indodana.app", "category": "paylater"},
    "Shopee": {"app_id": "com.shopee.id", "category": "ecommerce"},
    "Tokopedia": {"app_id": "com.tokopedia.tkpd", "category": "ecommerce"},
    "Lazada": {"app_id": "com.lazada.android", "category": "ecommerce"},
    "Bukalapak": {"app_id": "com.bukalapak.android", "category": "ecommerce"},
    "Traveloka": {"app_id": "com.traveloka.android", "category": "travel"},
    "Tiket.com": {"app_id": "com.tiket.gits", "category": "travel"},
    "Gojek": {"app_id": "com.gojek.app", "category": "ewallet"},
    "GoPay": {"app_id": "com.gojek.gopay", "category": "ewallet"},
    "OVO": {"app_id": "ovo.id", "category": "ewallet"},
    "DANA": {"app_id": "id.dana", "category": "ewallet"},
    "LinkAja": {"app_id": "com.telkom.mwallet", "category": "ewallet"},
    "Sakuku": {"app_id": "com.bca.sakuku", "category": "ewallet"},
    "RupiahCepat": {"app_id": "com.loan.cash.credit.easy.kilat.cepat.pinjam.uang.dana.rupiah", "category": "pinjol"},
    "KreditPintar": {"app_id": "com.kreditpintar", "category": "pinjol"},
    "Tunaiku": {"app_id": "com.tunaikumobile.app", "category": "pinjol"},
    "AdaKami": {"app_id": "com.yinshan.program.banda", "category": "pinjol"},
    "Easycash": {"app_id": "com.uatas.android", "category": "pinjol"},
    "UangMe": {"app_id": "com.kkii", "category": "pinjol"},
    "KoinWorks": {"app_id": "com.koinworks.app", "category": "p2p_lending"},
    "BRImo": {"app_id": "id.co.bri.brimo", "category": "mobile_banking"},
    "Stockbit": {"app_id": "com.stockbit.android", "category": "investasi"},
    # === Round 7 additions: 20 app baru (investasi, kartu kredit, P2P, mobile_banking) ===
    "Ajaib": {"app_id": "ajaib.co.id.revamp.android", "category": "investasi"},
    "Bibit": {"app_id": "com.bibit.id", "category": "investasi"},
    "Bareksa": {"app_id": "id.bareksa.app", "category": "investasi"},
    "IPOT": {"app_id": "com.indopremier.app.ipot", "category": "investasi"},
    "Pluang": {"app_id": "com.pluang.android", "category": "investasi"},
    "Jenius": {"app_id": "com.btpn.digital", "category": "kartu_kredit"},
    "Digibank": {"app_id": "com.dbs.id.digibank", "category": "mobile_banking"},
    "BCA Mobile": {"app_id": "com.bca.mybca", "category": "mobile_banking"},
    "BNI Mobile": {"app_id": "id.bni.apps", "category": "mobile_banking"},
    "CIMB Niaga": {"app_id": "id.co.cimb.android", "category": "mobile_banking"},
    "PermataMobileX": {"app_id": "com.bii.mobile.android", "category": "mobile_banking"},
    "Danamon": {"app_id": "mobile.com.danamon", "category": "mobile_banking"},
    "Investree": {"app_id": "com.investree.app", "category": "p2p_lending"},
    "Amartha": {"app_id": "com.amartha.app", "category": "p2p_lending"},
    "Akseleran": {"app_id": "id.akseleran.app", "category": "p2p_lending"},
    "Finmas": {"app_id": "id.web.finmas", "category": "pinjol"},
    "PinjamUang": {"app_id": "id.pinjaman.uang.online", "category": "pinjol"},
    "CashKerjo": {"app_id": "com.cashkerjo", "category": "pinjol"},
    "Maupinjam": {"app_id": "id.maupinjaman.app", "category": "pinjol"},
    "PinjamanGo": {"app_id": "com.pinjamango.app", "category": "pinjol"},
}

GALBAY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "distress_langsung": (
        "galbay",
        "gagal bayar",
        "gagalbayar",
        "nunggak",
        "macet",
        "telat bayar",
        "tidak bisa bayar",
        "nggak bisa bayar",
    ),
    "tagihan_dan_penagihan": (
        "ditagih",
        "tagihan",
        "tagih",
        "menagih",
        "penagih",
        "debt collector",
        "dc",
        "dicerewet",
        "ditagih dc",
        "ditagih jam 12",
    ),
    "bunga_dan_biaya": (
        "bunga",
        "dendanya",
        "denda",
        "biaya admin",
        "admin",
        "bunga tinggi",
        "bunga naik",
        "markup",
    ),
    "produk_fintech": (
        "paylater",
        "pay later",
        "paylateran",
        "pinjol",
        "pinjaman online",
        "cicilan",
        "kasbon",
        "bon",
        "limit",
        "tenor",
    ),
    "psikologi_impulsif": (
        "self reward",
        "selfreward",
        "checkout dulu",
        "checkout dulu bayar nanti",
        "fomo",
        "flash sale",
        "gpp cicil",
        "bayar nanti",
        "bayar nanti aja",
        "tagihan bulan depan",
        "impulsif",
        "kebablasan",
    ),
    "psikologi_avoidance": (
        "takut ditagih",
        "kabur",
        "kabur dari dc",
        "ganti nomor",
        "ganti hp",
        "blokir",
        "di blokir",
        "diblokir",
        "hide",
        "sembunyi",
    ),
    "psikologi_regret_stress": (
        "menyesal",
        "insyaf",
        "sudah insyaf",
        "janji gak akan lagi",
        "stress",
        "stres",
        "depresi",
        "tidur",
        "susah tidur",
        "nggak bisa tidur",
        "gambar dp",
        "dp galbay",
        "dp stress",
    ),
}

ALL_GALBAY_KEYWORDS: tuple[str, ...] = tuple(keyword for group in GALBAY_KEYWORDS.values() for keyword in group)


class GooglePlayReviewsScraper(BaseScraper):
    name = "fintech_reviews"

    def resolve_apps(self, names: list[str] | None = None, app_limit: int = 0) -> list[dict]:
        from google_play_scraper import app as app_info

        names = names or list(APP_IDS.keys())
        resolved = []
        for name in tqdm(names, desc="Resolve app"):
            entry = APP_IDS.get(name)
            app_id = entry.get("app_id") if entry else None
            category = entry.get("category") if entry else None
            if app_id:
                try:
                    info = app_info(app_id, lang="id", country="id")
                    resolved.append(
                        {
                            "query": name,
                            "app_id": app_id,
                            "title": info.get("title"),
                            "score": info.get("score"),
                            "installs": info.get("installs"),
                            "category": category,
                        }
                    )
                    self.polite_sleep()
                    continue
                except Exception as exc:
                    log.warning("Curated appId '%s' gagal verifikasi: %s", app_id, exc)
            try:
                results = search(name, lang="id", country="id", n_hits=8)
                for result in results:
                    aid = result.get("appId")
                    if aid:
                        resolved.append(
                            {
                                "query": name,
                                "app_id": aid,
                                "title": result.get("title"),
                                "score": result.get("score"),
                                "installs": None,
                                "category": category,
                            }
                        )
                        break
                else:
                    log.warning("Tidak ketemu appId valid untuk: %s", name)
                self.polite_sleep()
            except Exception as exc:
                log.warning("Gagal resolve '%s': %s", name, exc)
        if app_limit:
            resolved = resolved[:app_limit]
        log.info("Resolved %d app dari %d nama", len(resolved), len(names))
        return resolved

    @staticmethod
    def _normalize_row(review: dict, app: dict) -> dict:
        return {
            "app_id": app["app_id"],
            "app_name": app.get("title"),
            "query": app.get("query"),
            "category": app.get("category"),
            "review_id": review.get("reviewId"),
            "score": review.get("score"),
            "content": (review.get("content") or "").strip(),
            "thumbs_up": review.get("thumbsUpCount", 0),
            "at": review.get("at").isoformat() if review.get("at") else None,
            "replied": bool(review.get("replyContent")),
            "version": review.get("reviewCreatedVersion") or review.get("appVersion"),
        }

    def fetch_reviews(self, app: dict, count: int = 400) -> list[dict]:
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
        except Exception as exc:
            log.warning("Gagal fetch reviews %s (%s): %s", app.get("title"), app_id, exc)
            return []
        return [self._normalize_row(row, app) for row in result]

    def fetch_all_reviews(self, app: dict, max_per_app: int = 0) -> list[dict]:
        app_id = app["app_id"]
        safe = (app.get("query") or "app").replace(" ", "_").lower()
        cache_path = self.raw_dir / f"play_reviews_{safe}.json"
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as handle:
                    import json

                    cached = json.load(handle)
                if isinstance(cached, list) and cached:
                    log.info("Resume: load %d review dari cache %s", len(cached), cache_path.name)
                    return cached
            except Exception as exc:
                log.warning("Cache %s corrupt, re-scrape: %s", cache_path.name, exc)

        try:
            kwargs = {"lang": "id", "country": "id", "sort": Sort.NEWEST, "filter_score_with": None}
            if max_per_app > 0:
                result = []
                continuation = None
                while len(result) < max_per_app:
                    batch, continuation = reviews(
                        app_id,
                        count=min(max_per_app - len(result), 200),
                        continuation_token=continuation,
                        **kwargs,
                    )
                    if not batch:
                        break
                    result.extend(batch)
                    if not continuation:
                        break
                    self.polite_sleep()
                rows = [self._normalize_row(row, app) for row in result[:max_per_app]]
            else:
                result = reviews_all(app_id, sleep_milliseconds=int(self.sleep_seconds * 1000), **kwargs)
                rows = [self._normalize_row(row, app) for row in result]
        except Exception as exc:
            log.warning("Gagal fetch_all %s (%s): %s", app.get("title"), app_id, exc)
            return []
        log.info("Fetched %d review (all) untuk %s", len(rows), app.get("title"))
        return rows

    def _flag_relevant(self, rows: list[dict]) -> list[dict]:
        for row in rows:
            text = (row.get("content") or "").lower()
            matched = []
            for category, keywords in GALBAY_KEYWORDS.items():
                if any(keyword in text for keyword in keywords):
                    matched.append(category)
            row["is_relevant"] = bool(matched)
            row["matched_categories"] = matched
            row["n_matched_categories"] = len(matched)
        return rows

    def run(self, count: int = 400, app_limit: int = 0, mode: str = "sample", max_per_app: int = 0) -> dict[str, Any]:
        apps = self.resolve_apps(app_limit=app_limit)
        if not apps:
            return {"status": "no_apps", "resolved": 0}

        all_rows: list[dict] = []
        per_app_summary: list[dict] = []

        fetch_desc = "Fetch reviews (ALL)" if mode == "all" else "Fetch reviews (sample)"
        for app in tqdm(apps, desc=fetch_desc):
            if mode == "all":
                rows = self.fetch_all_reviews(app, max_per_app=max_per_app)
            else:
                rows = self.fetch_reviews(app, count=count)
            rows = self._flag_relevant(rows)
            all_rows.extend(rows)
            per_app_summary.append(
                {
                    "app_id": app["app_id"],
                    "app_name": app.get("title"),
                    "query": app.get("query"),
                    "category": app.get("category"),
                    "installs": app.get("installs"),
                    "n_reviews": len(rows),
                    "n_relevant": sum(1 for row in rows if row.get("is_relevant")),
                    "mode": mode,
                }
            )
            safe = (app.get("query") or "app").replace(" ", "_").lower()
            self.save_json(rows, f"play_reviews_{safe}.json", subdir="raw")
            self.polite_sleep()

        meta = self.meta(
            "google_play_reviews",
            {
                "n_apps": len(apps),
                "n_reviews_total": len(all_rows),
                "mode": mode,
                "count_per_app": count if mode == "sample" else None,
                "max_per_app": max_per_app or None,
                "keyword_groups": list(GALBAY_KEYWORDS.keys()),
                "per_app": per_app_summary,
            },
        )
        combined = {"meta": meta, "reviews": all_rows}
        self.save_json(combined, "play_reviews_all.json", subdir="raw")

        sample = all_rows[:1000] if len(all_rows) > 1000 else all_rows
        sample_payload = {"meta": meta, "reviews": sample}
        self.save_json(sample_payload, "play_reviews_sample.json", subdir="sample")

        n_relevant = sum(1 for row in all_rows if row.get("is_relevant"))
        log.info("Total %d review dari %d app (%d relevan galbay)", len(all_rows), len(apps), n_relevant)
        return {
            "status": "ok",
            "n_apps": len(apps),
            "n_reviews_total": len(all_rows),
            "n_relevant": n_relevant,
            "mode": mode,
            "sample_size": len(sample),
            "per_app": per_app_summary,
        }
