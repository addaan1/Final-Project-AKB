"""Scraper berita & siaran pers OJK (PRIORITAS 6).

STUB — rencana:
- OJK: scrape siaran pers & regulasi paylater/pinjol dari ojk.go.id.
- Media: crawler berita (kompas, detik, cnbc) keyword "galbay"/"paylater".

Volume rendah-menengah tapi relevansi tinggi sebagai sinyal regulator & market.
"""
from __future__ import annotations

from scraper.base import BaseScraper


class OjkNewsScraper(BaseScraper):
    name = "ojk_news"

    def run(self, **kwargs):
        raise NotImplementedError(
            "OJK/news scraper belum diimplementasi. Eksplor: requests+BS4."
        )
