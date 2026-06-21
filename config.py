"""Konfigurasi aplikasi."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-galbay")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    JSON_SORT_KEYS = False
    DATA_DIR = str(DATA_DIR)
    RAW_DIR = str(RAW_DIR)
    PROCESSED_DIR = str(PROCESSED_DIR)


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod")


config_map = {
    "development": Config,
    "production": ProductionConfig,
}
