"""Scraper Instagram caption/komentar terkait paylater (PRIORITAS 3b).

STUB — Instagram Graph API terbatas untuk bisnis. Alternatif:
- instaloader (unofficial; risiko rate-limit/block).
- Fokus: caption post akun edukasi finansial & iklan paylater.

Etika: PII wajib di-redact sebelum commit.
"""
from __future__ import annotations

from scraper.base import BaseScraper


class InstagramScraper(BaseScraper):
    name = "instagram"

    def run(self, **kwargs):
        raise NotImplementedError(
            "Instagram scraper belum diimplementasi. Eksplor: instaloader."
        )
