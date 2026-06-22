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

from google_play_scraper import reviews, reviews_all, search, Sort
from tqdm import tqdm

from scraper.base import BaseScraper

log = logging.getLogger("scraper.fintech_reviews")

# Curated appId fintech Indonesia (terverifikasi via app() lookup Mei 2025).
# Kategori: paylater/BNPL, e-wallet, e-commerce (dengan paylater), pinjol,
# P2P lending, mobile banking, investasi (untuk diversifikasi sinyal literasi).
APP_IDS: dict[str, dict] = {
    # Paylater / BNPL
    "Kredivo": {"app_id": "com.finaccel.android", "category": "paylater"},
    "Akulaku": {"app_id": "io.silvrr.installment", "category": "paylater"},
    "Indodana": {"app_id": "com.indodana.app", "category": "paylater"},
    # E-commerce dengan paylater/BNPL
    "Shopee": {"app_id": "com.shopee.id", "category": "ecommerce"},
    "Tokopedia": {"app_id": "com.tokopedia.tkpd", "category": "ecommerce"},
    "Lazada": {"app_id": "com.lazada.android", "category": "ecommerce"},
    "Bukalapak": {"app_id": "com.bukalapak.android", "category": "ecommerce"},
    # Travel & booking (paylater travel)
    "Traveloka": {"app_id": "com.traveloka.android", "category": "travel"},
    "Tiket.com": {"app_id": "com.tiket.gits", "category": "travel"},
    # E-wallet
    "Gojek": {"app_id": "com.gojek.app", "category": "ewallet"},
    "GoPay": {"app_id": "com.gojek.gopay", "category": "ewallet"},
    "OVO": {"app_id": "ovo.id", "category": "ewallet"},
    "DANA": {"app_id": "id.dana", "category": "ewallet"},
    "LinkAja": {"app_id": "com.telkom.mwallet", "category": "ewallet"},
    "Sakuku": {"app_id": "com.bca.sakuku", "category": "ewallet"},
    # Pinjol / pinjaman online
    "RupiahCepat": {"app_id": "com.loan.cash.credit.easy.kilat.cepat.pinjam.uang.dana.rupiah", "category": "pinjol"},
    "KreditPintar": {"app_id": "com.kreditpintar", "category": "pinjol"},
    "Tunaiku": {"app_id": "com.tunaikumobile.app", "category": "pinjol"},
    "AdaKami": {"app_id": "com.yinshan.program.banda", "category": "pinjol"},
    "Easycash": {"app_id": "com.uatas.android", "category": "pinjol"},
    "UangMe": {"app_id": "com.kkii", "category": "pinjol"},
    # P2P lending
    "KoinWorks": {"app_id": "com.koinworks.app", "category": "p2p_lending"},
    # Mobile banking (dengan fitur paylater/kredit)
    "BRImo": {"app_id": "id.co.bri.brimo", "category": "mobile_banking"},
    # Investasi (sinyal literasi finansial, pembanding)
    "Stockbit": {"app_id": "com.stockbit.android", "category": "investasi"},
    # === Tambahan 20 app baru (Juni 2025) ===
    # Bank digital
    "SeaBank": {"app_id": "id.co.bankbkemobile.digitalbank", "category": "bank_digital"},
    "neobank": {"app_id": "com.bnc.finance", "category": "bank_digital"},
    "Bank Jago": {"app_id": "com.jago.digitalBanking", "category": "bank_digital"},
    "blu by BCA": {"app_id": "com.bcadigital.blu", "category": "bank_digital"},
    "Livin by Mandiri": {"app_id": "id.bmri.livin", "category": "mobile_banking"},
    # Pinjol tambahan
    "EasycashNew": {"app_id": "com.fintopia.idnEasycash.google", "category": "pinjol"},
    "BantuSaku": {"app_id": "com.smartec.ft", "category": "pinjol"},
    "AdaKamiNew": {"app_id": "com.adakami.dana.kredit.pinjaman", "category": "pinjol"},
    "Singa": {"app_id": "com.asf.singa", "category": "pinjol"},
    "FinPlus": {"app_id": "com.finplus.android", "category": "pinjol"},
    "KrediOne": {"app_id": "com.id.kredi360", "category": "pinjol"},
    "Home Credit": {"app_id": "id.co.myhomecredit", "category": "pinjol"},
    "JULO": {"app_id": "com.julofinance.juloapp", "category": "pinjol"},
    "KTA Kilat": {"app_id": "com.ktakilat.loan", "category": "pinjol"},
    "Indosaku": {"app_id": "com.indosk.sensid", "category": "pinjol"},
    "Cairin": {"app_id": "com.iss.client.cairin", "category": "pinjol"},
    # E-wallet / transfer tambahan
    "ShopeePay": {"app_id": "com.shopeepay.id", "category": "ewallet"},
    "Flip": {"app_id": "id.flip", "category": "ewallet"},
    # Koperasi
    "Artha Niaga": {"app_id": "com.kpsto.artha.niaga", "category": "koperasi"},
    # Kartu kredit digital
    "Honest": {"app_id": "com.honestbank.android", "category": "kartu_kredit"},
}

# Keyword sinyal galbay & psikologis untuk filtering konten relevan.
# Dikelompokkan untuk diagnosis kategori perilaku di tahap processing.
GALBAY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "distress_langsung": (
        "galbay", "gagal bayar", "gagalbayar", "nunggak", "macet",
        "telat bayar", "tidak bisa bayar", "nggak bisa bayar",
    ),
    "tagihan_dan_penagihan": (
        "ditagih", "tagihan", "tagih", "menagih", "penagih", "debt collector",
        "dc", "dicerewet", "ditagih dc", "ditagih jam 12",
    ),
    "bunga_dan_biaya": (
        "bunga", "dendanya", "denda", "biaya admin", "admin", "bunga tinggi",
        "bunga naik", "markup",
    ),
    "produk_fintech": (
        "paylater", "pay later", "paylateran", "pinjol", "pinjaman online",
        "cicilan", "kasbon", "bon", "limit", "tenor",
    ),
    "psikologi_impulsif": (
        "self reward", "selfreward", "checkout dulu", "checkout dulu bayar nanti",
        "fomo", "flash sale", "gpp cicil", "bayar nanti", "bayar nanti aja",
        "tagihan bulan depan", "impulsif", "kebablasan",
    ),
    "psikologi_avoidance": (
        "takut ditagih", "kabur", "kabur dari dc", "ganti nomor", "ganti hp",
        "blokir", "di blokir", "diblokir", "hide", "sembunyi",
    ),
    "psikologi_regret_stress": (
        "menyesal", "insyaf", "sudah insyaf", "janji gak akan lagi", "stress",
        "stres", "depresi", "tidur", "susah tidur", "nggak bisa tidur",
        "gambar dp", "dp galbay", "dp stress",
    ),
}

# Flat set untuk flagging cepat is_relevant
ALL_GALBAY_KEYWORDS: tuple[str, ...] = tuple(
    kw for group in GALBAY_KEYWORDS.values() for kw in group
)


class GooglePlayReviewsScraper(BaseScraper):
    name = "fintech_reviews"

    def resolve_apps(self, names: list[str] | None = None, app_limit: int = 0) -> list[dict]:
        """Resolve app_id untuk setiap nama. Pakai curated APP_IDS (reliable);
        fallback ke search() jika nama tidak ada di dict. Return list
        {query, app_id, title, score, installs, category}."""
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
                    resolved.append({
                        "query": name,
                        "app_id": app_id,
                        "title": info.get("title"),
                        "score": info.get("score"),
                        "installs": info.get("installs"),
                        "category": category,
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
                            "category": category,
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

    @staticmethod
    def _normalize_row(r: dict, app: dict) -> dict:
        """Normalisasi satu review mentah ke skema konsisten."""
        return {
            "app_id": app["app_id"],
            "app_name": app.get("title"),
            "query": app.get("query"),
            "category": app.get("category"),
            "review_id": r.get("reviewId"),
            "score": r.get("score"),
            "content": (r.get("content") or "").strip(),
            "thumbs_up": r.get("thumbsUpCount", 0),
            "at": r.get("at").isoformat() if r.get("at") else None,
            "replied": bool(r.get("replyContent")),
            "version": r.get("reviewCreatedVersion") or r.get("appVersion"),
        }

    def fetch_reviews(self, app: dict, count: int = 400) -> list[dict]:
        """Ambil sejumlah review terbatas untuk satu app (mode sample)."""
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
        return [self._normalize_row(r, app) for r in result]

    def fetch_all_reviews(self, app: dict, max_per_app: int = 0) -> list[dict]:
        """Ambil SEMUA review untuk satu app via continuation token (mode all).
        max_per_app=0 berarti unlimited. Bisa lama untuk app besar (100M+ installs).
        Resume-friendly: jika file raw per-app sudah ada dan cukup, skip."""
        app_id = app["app_id"]
        safe = (app.get("query") or "app").replace(" ", "_").lower()
        cache_path = self.raw_dir / f"play_reviews_{safe}.json"
        # Cek cache/resume
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    import json
                    cached = json.load(f)
                if isinstance(cached, list) and len(cached) > 0:
                    log.info("Resume: load %d review dari cache %s", len(cached), cache_path.name)
                    return cached
            except Exception as e:
                log.warning("Cache %s corrupt, re-scrape: %s", cache_path.name, e)

        try:
            kwargs = {"lang": "id", "country": "id", "sort": Sort.NEWEST, "filter_score_with": None}
            if max_per_app > 0:
                # pakai reviews() berturut-turut dengan continuation untuk cap
                result = []
                _continuation = None
                while len(result) < max_per_app:
                    batch, _continuation = reviews(
                        app_id, count=min(max_per_app - len(result), 200),
                        continuation_token=_continuation, **kwargs,
                    )
                    if not batch:
                        break
                    result.extend(batch)
                    if not _continuation:
                        break
                    self.polite_sleep()
                rows = [self._normalize_row(r, app) for r in result[:max_per_app]]
            else:
                result = reviews_all(app_id, sleep_milliseconds=int(self.sleep_seconds * 1000), **kwargs)
                rows = [self._normalize_row(r, app) for r in result]
        except Exception as e:
            log.warning("Gagal fetch_all %s (%s): %s", app.get("title"), app_id, e)
            return []
        log.info("Fetched %d review (all) untuk %s", len(rows), app.get("title"))
        return rows

    def _flag_relevant(self, rows: list[dict]) -> list[dict]:
        """Tandai baris yang mengandung keyword galbay (sinyal perilaku).
        Tambah field matched_categories untuk diagnosis psikologis."""
        for row in rows:
            text = (row.get("content") or "").lower()
            matched = []
            for cat, kws in GALBAY_KEYWORDS.items():
                if any(kw in text for kw in kws):
                    matched.append(cat)
            row["is_relevant"] = bool(matched)
            row["matched_categories"] = matched
            row["n_matched_categories"] = len(matched)
        return rows

    def run(self, count: int = 400, app_limit: int = 0, mode: str = "sample",
            max_per_app: int = 0) -> dict[str, Any]:
        """Jalankan scraper.

        mode='sample' : ambil `count` review terbaru per app (cepat, untuk demo).
        mode='all'    : ambil SEMUA review per app via continuation token
                        (big data, bisa lama). max_per_app>0 membatasi per-app.
        """
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
            per_app_summary.append({
                "app_id": app["app_id"],
                "app_name": app.get("title"),
                "query": app.get("query"),
                "category": app.get("category"),
                "installs": app.get("installs"),
                "n_reviews": len(rows),
                "n_relevant": sum(1 for r in rows if r.get("is_relevant")),
                "mode": mode,
            })
            # simpan per-app (raw, gitignored) sebagai checkpoint resume
            safe = (app.get("query") or "app").replace(" ", "_").lower()
            self.save_json(rows, f"play_reviews_{safe}.json", subdir="raw")
            self.polite_sleep()

        # gabungan raw (gitignored)
        meta = self.meta("google_play_reviews", {
            "n_apps": len(apps),
            "n_reviews_total": len(all_rows),
            "mode": mode,
            "count_per_app": count if mode == "sample" else None,
            "max_per_app": max_per_app or None,
            "keyword_groups": list(GALBAY_KEYWORDS.keys()),
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
            "mode": mode,
            "sample_size": len(sample),
            "per_app": per_app_summary,
        }
