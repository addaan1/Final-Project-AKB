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
]


class GoogleTrendsScraper(BaseScraper):
    name = "google_trends"

    def run(self, **kwargs) -> dict[str, Any]:
        pytrends = TrendReq(hl="id-ID", tz=420)  # tz=420 = WIB UTC+7
        frames = []
        for group in KEYWORDS_GROUPS:
            try:
                pytrends.build_payload(group["kw"], cat=0, geo="ID", timeframe="today 12-m")
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
        meta = self.meta("google_trends", {"n_records": len(records), "groups": [g["label"] for g in KEYWORDS_GROUPS]})
        payload = {"meta": meta, "trends": records}
        self.save_json(payload, "google_trends_12m.json", subdir="raw")
        self.save_json(payload, "google_trends_sample.json", subdir="sample")
        return {"status": "ok", "n_records": len(records), "groups": [g["label"] for g in KEYWORDS_GROUPS]}
