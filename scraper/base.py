"""Kelas dasar untuk semua scraper.

Menyediakan:
- path output (raw/processed)
- helper simpan JSON
- logging sederhana
- rate-limit sopan (sleep) untuk etika scraping
- load kredensial dari .env (opsional, untuk login ke platform)
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from dotenv import load_dotenv
    load_dotenv()  # load .env kalau ada
except ImportError:
    pass  # python-dotenv belum terinstall, skip

from config import RAW_DIR, PROCESSED_DIR, SAMPLE_DIR


class BaseScraper:
    """Base class untuk scraper big data."""

    name: str = "base"

    def __init__(self, sleep_seconds: float = 0.0):
        self.sleep_seconds = sleep_seconds or float(os.environ.get("SCRAPER_SLEEP_SECONDS", "1.0"))
        self.raw_dir = Path(RAW_DIR)
        self.processed_dir = Path(PROCESSED_DIR)
        self.sample_dir = Path(SAMPLE_DIR)
        for d in (self.raw_dir, self.processed_dir, self.sample_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(f"scraper.{self.name}")

    def polite_sleep(self) -> None:
        """Rate-limit sopan; hormati sumber data."""
        if self.sleep_seconds > 0:
            time.sleep(self.sleep_seconds)

    def save_json(self, data, filename: str, subdir: str = "raw") -> Path:
        """Simpan data ke JSON. subdir: 'raw' | 'processed' | 'sample'."""
        target_dir = {
            "raw": self.raw_dir,
            "processed": self.processed_dir,
            "sample": self.sample_dir,
        }[subdir]
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        self.logger.info("Saved %d items -> %s", len(data) if isinstance(data, list) else 1, path)
        return path

    def meta(self, source: str, extra: dict | None = None) -> dict:
        """Metadata standar untuk reproducibility & etika."""
        m = {
            "source": source,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scraper": self.name,
        }
        if extra:
            m.update(extra)
        return m

    def run(self, **kwargs) -> dict:
        """Override di subclass. Return ringkasan hasil."""
        raise NotImplementedError

    def get_env(self, key: str, default: str | None = None) -> str | None:
        """Ambil env var dengan fallback. Return None kalau tidak ada."""
        return os.environ.get(key, default)
