"""Scraper komentar TikTok #galbay #paylater #pinjol (PRIORITAS 2).

STUB — implementasi menyusul. Catatan teknis:
- TikTok anti-bot kuat; opsi: TikTokApi (unofficial) atau Playwright headless.
- Target: komentar video dengan hashtag relevan, fokus Gen Z.
- Etika: tidak simpan username asli (redact); simpan teks komentar + timestamp.
"""
from __future__ import annotations

from scraper.base import BaseScraper


class TikTokScraper(BaseScraper):
    name = "tiktok"

    def run(self, **kwargs):
        raise NotImplementedError(
            "TikTok scraper belum diimplementasi. Gunakan TikTokApi/Playwright. "
            "Lihat docstring modul untuk rencana implementasi."
        )
