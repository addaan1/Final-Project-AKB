"""Scraper post X/Twitter keyword galbay/pinjol (PRIORITAS 4).

STUB — akses X API kini berbayar/terbatas. Alternatif yang akan dieksplor:
- X API v2 tier free (limit 1500 read post/bulan, terbatas).
- Nitter instance snapshot (tidak stabil).
- Snscrape (mendukung Twitter, tapi break sering pas Twitter rate-limit).
"""
from __future__ import annotations

from scraper.base import BaseScraper


class TwitterScraper(BaseScraper):
    name = "twitter"

    def run(self, **kwargs):
        raise NotImplementedError(
            "Twitter/X scraper belum diimplementasi (akses berbayar/terbatas). "
            "Eksplor: X API v2 free tier atau snscrape."
        )
