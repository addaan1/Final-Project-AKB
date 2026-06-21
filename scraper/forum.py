"""Scraper forum: Kaskus & Reddit thread utang/paylater (PRIORITAS 3).

STUB — rencana:
- Kaskus: BeautifulSoup + requests pada forum "The Lounge"/"Finansial".
- Reddit: PRAW (r/indonesia, r/finansial) keyword "utang"/"paylater"/"pinjol".

Volume menengah-tinggi, relevansi tinggi (diskusi panjang = konteks psikologi).
"""
from __future__ import annotations

from scraper.base import BaseScraper


class ForumScraper(BaseScraper):
    name = "forum"

    def run(self, **kwargs):
        raise NotImplementedError(
            "Forum scraper (Kaskus/Reddit) belum diimplementasi. "
            "Eksplor: requests+BS4 (Kaskus), PRAW (Reddit)."
        )
