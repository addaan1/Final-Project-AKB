"""Scraper Google Trends via pytrends (PRIORITAS 5).

Untuk narasi tren, bukan volume. Mengukur minat pencarian keyword
galbay/paylater/pinjol dari waktu ke waktu.
"""
from __future__ import annotations

import logging
from typing import Any

from pytrends.request import TrendReq

from scraper.base import BaseScraper

log = logging.getLogger("scraper.google_trends")

KEYWORDS_GROUPS: list[dict] = [
    {"label": "galbay", "kw": ["galbay", "gagal bayar", "gagalbayar"]},
    {"label": "paylater", "kw": ["paylater", "pay later", "limit paylater"]},
    {"label": "pinjol", "kw": ["pinjol", "pinjaman online", "pinjol legal"]},
    {"label": "tagihan", "kw": ["ditagih dc", "cara lunasi hutang", "takut ditagih"]},
    {"label": "konsumtif", "kw": ["self reward", "checkout dulu bayar nanti"]},
    {"label": "kredit", "kw": ["kartu kredit", "kredit online", "KTA"]},
    {"label": "cicilan", "kw": ["cicilan 0", "cicilan mobil", "cicilan rumah"]},
    {"label": "utang", "kw": ["utang", "cara melunasi hutang", "restrukturisasi"]},
    {"label": "debt_collector", "kw": ["debt collector", "penagih utang", "ditagih"]},
    {"label": "konsolidasi", "kw": ["konsolidasi pinjaman", "pelunasan utang"]},
    {"label": "edukasi", "kw": ["literasi keuangan", "tips keuangan", "menabung"]},
    {"label": "kredivo", "kw": ["kredivo", "akulaku", "indodana"]},
    {"label": "julo", "kw": ["julo", "koinworks", "amartha"]},
    {"label": "shopeepaylater", "kw": ["shopeepaylater", "shopee paylater", "gopaylater"]},
    {"label": "dana", "kw": ["dana paylater", "ovo paylater"]},
    {"label": "kredit_pintar", "kw": ["kredit pintar", "rupee cepat", "tunaiku"]},
    {"label": "ada_kami", "kw": ["ada kami", "easy cash", "uangku"]},
    {"label": "cicilan_motor", "kw": ["cicilan motor", "kredit motor", "leasing"]},
    {"label": "kpr", "kw": ["KPR", "kredit rumah", "cicilan KPR"]},
    {"label": "gaji", "kw": ["gaji", "take home pay", "gaji UMR"]},
]


class GoogleTrendsScraper(BaseScraper):
    name = "google_trends"

    def run(self, timeframe: str = "today 5-y", **kwargs) -> dict[str, Any]:
        """Scrape Google Trends time-series.

        Args:
            timeframe: pytrends timeframe string. Default 'today 5-y' (5 tahun).
                Use 'today 12-m' untuk 12 bulan.
        """
        pytrends = TrendReq(hl="id-ID", tz=420)  # tz=420 = WIB UTC+7
        frames = []
        for group in KEYWORDS_GROUPS:
            try:
                # pytrends max 5 keywords per request, kita sudah batasi
                kw = group["kw"][:5]
                pytrends.build_payload(kw, cat=0, geo="ID", timeframe=timeframe)
                df = pytrends.interest_over_time()
                if df.empty:
                    continue
                df = df.reset_index().drop(columns=["isPartial"], errors="ignore")
                df["label"] = group["label"]
                frames.append(df)
                self.polite_sleep()
            except Exception as e:
                log.warning("Gagal ambil tren grup '%s': %s", group["label"], e)

        if not frames:
            return {"status": "empty"}

        import pandas as pd
        merged = pd.concat(frames, ignore_index=True)
        records = merged.to_dict(orient="records")
        meta = self.meta(
            "google_trends",
            {
                "n_records": len(records),
                "groups": [g["label"] for g in KEYWORDS_GROUPS],
                "timeframe": timeframe,
            },
        )
        payload = {"meta": meta, "trends": records}
        # Save with timeframe suffix
        suffix = "5y" if "5-y" in timeframe else "12m"
        self.save_json(payload, f"google_trends_{suffix}.json", subdir="raw")
        self.save_json(payload, f"google_trends_{suffix}_sample.json", subdir="sample")
        return {
            "status": "ok",
            "n_records": len(records),
            "groups": [g["label"] for g in KEYWORDS_GROUPS],
            "timeframe": timeframe,
        }
