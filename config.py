"""Konfigurasi aplikasi."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"


def env_flag(name: str, default: bool) -> bool:
    """Parse boolean-like environment flags."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-galbay")
    DEBUG = env_flag("FLASK_DEBUG", True)
    JSON_SORT_KEYS = False
    DATA_DIR = str(DATA_DIR)
    RAW_DIR = str(RAW_DIR)
    PROCESSED_DIR = str(PROCESSED_DIR)
    SESSION_COOKIE_SECURE = False  # True kalau HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60  # 7 hari dalam detik

    # Google OAuth (opsional — kalau tidak di-set, demo login only)
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.environ.get(
        "GOOGLE_REDIRECT_URI",
        "http://127.0.0.1:5000/auth/google/callback",
    )

    APP_CONFIG = os.environ.get("APP_CONFIG", "development")
    DEMO_ONLY = env_flag("DEMO_ONLY", False)
    ALLOW_REGISTRATION = env_flag("ALLOW_REGISTRATION", True)
    ALLOW_WAITLIST = env_flag("ALLOW_WAITLIST", True)
    ALLOW_OAUTH = env_flag("ALLOW_OAUTH", True)
    PERSIST_LOCAL_WRITES = env_flag("PERSIST_LOCAL_WRITES", True)


class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-prod")
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


config_map = {
    "development": Config,
    "production": ProductionConfig,
}
