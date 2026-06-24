"""Area C — Indonesian sentiment lexicon extension for VADER.

VADER's bundled lexicon is English-only, so out of the box it scores almost
every Indonesian sentence as neutral. This module supplies the missing
pieces so `processing/sentiment.py` can keep using VADER (NLTK) — required
by the project brief — while actually understanding Indonesian text:

- ID_SENTIMENT_LEXICON: word -> valence (-4..+4, same scale as VADER's own
  lexicon) merged into `SentimentIntensityAnalyzer().lexicon`.
- ID_NEGATIONS: Indonesian negators merged into `vader.NEGATE`, so "tidak
  bagus" actually flips polarity instead of scoring as plain "bagus".
- ID_BOOSTER_INCREMENT / ID_BOOSTER_DECREMENT: Indonesian intensity
  modifiers merged into `vader.BOOSTER_DICT`.

Words are chosen to match the canonical forms that
`processing/preprocess.py::clean_text()` normalizes slang into (e.g. "gak"
-> "tidak", "mantap"/"keren" -> "bagus", "jelek"/"payah"/"rusak" -> "buruk"),
plus galbay/fintech domain terms not covered by general-purpose lexicons.
"""
from __future__ import annotations

ID_SENTIMENT_LEXICON: dict[str, float] = {
    # --- general positive ---
    "bagus": 2.0, "baik": 1.8, "puas": 2.2, "memuaskan": 2.2, "nyaman": 1.8,
    "aman": 1.5, "mudah": 1.5, "gampang": 1.5, "cepat": 1.3, "ramah": 1.8,
    "sopan": 1.5, "membantu": 1.8, "terbantu": 1.8, "suka": 1.9, "senang": 2.0,
    "bahagia": 2.2, "mantap": 2.0, "keren": 1.8, "rekomendasi": 1.8,
    "direkomendasikan": 1.8, "oke": 1.3, "terpercaya": 2.0, "profesional": 1.6,
    "fleksibel": 1.5, "ringan": 1.3, "jujur": 1.6, "transparan": 1.5,
    "responsif": 1.5, "tanggap": 1.3,
    # --- general negative ---
    "buruk": -2.0, "jelek": -1.8, "payah": -1.8, "rusak": -1.8, "parah": -1.6,
    "kecewa": -2.3, "mengecewakan": -2.3, "menyesal": -2.0, "penyesalan": -1.8,
    "lambat": -1.5, "lemot": -1.5, "lelet": -1.5, "error": -1.8, "gagal": -1.8,
    "ribet": -1.5, "susah": -1.5, "sulit": -1.4, "bohong": -2.0, "berbohong": -2.0,
    "tipu": -2.5, "menipu": -2.5, "penipuan": -2.8, "scam": -2.8, "rugi": -2.0,
    "merugikan": -2.2, "takut": -1.8, "khawatir": -1.5, "cemas": -1.8,
    "stres": -2.0, "stress": -2.0, "panik": -1.8, "malu": -1.5, "marah": -1.8,
    "kesal": -1.5, "jengkel": -1.5, "hancur": -2.0, "bangkrut": -2.8,
    "korupsi": -2.5, "korup": -2.5, "lemah": -1.0, "rumit": -1.3,
    # --- fintech/galbay domain ---
    "galbay": -2.2, "gagalbayar": -2.2, "nunggak": -2.0, "menunggak": -2.0,
    "telat": -1.3, "terlambat": -1.3, "macet": -1.8, "denda": -1.5,
    "pinalti": -1.5, "penalti": -1.5, "bunga": -1.0, "tagih": -1.3,
    "menagih": -1.3, "nagih": -1.3, "penagih": -1.5, "dc": -1.8,
    "teror": -2.8, "meneror": -2.8, "ancam": -2.5, "mengancam": -2.5,
    "intimidasi": -2.5, "ilegal": -2.0, "utang": -1.0, "hutang": -1.0,
    "ditolak": -1.5, "ditipu": -2.5, "sebar": -1.0, "blacklist": -1.8,
    "slik": -0.8, "lancar": 2.0, "cair": 1.6, "approve": 1.8, "disetujui": 1.8,
    "acc": 1.5, "restrukturisasi": 1.0,
}

ID_NEGATIONS: set[str] = {"tidak", "bukan", "tanpa", "jangan", "belum", "tak"}

ID_BOOSTER_INCREMENT: set[str] = {"sangat", "amat", "sungguh", "banget"}
ID_BOOSTER_DECREMENT: set[str] = {"agak", "kurang", "sedikit", "cukup"}
