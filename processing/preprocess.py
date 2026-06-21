"""NLP preprocessing: text cleaning, normalization, tokenization.

- Lowercase
- Remove URL, mention (@user), hashtag (#)
- Normalize slang Indonesia
- Remove emoji, special chars
- Tokenize

Penggunaan:
    python -m processing.preprocess
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from config import RAW_DIR, PROCESSED_DIR

log = logging.getLogger("processing.preprocess")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

SLANG_MAP: dict[str, str] = {
    "yg": "yang", "gk": "gak", "gak": "tidak", "ga": "tidak", "g": "tidak",
    "bgt": "banget", "bnget": "banget", "dgn": "dengan", "dlm": "dalam",
    "dr": "dari", "krn": "karena", "karna": "karena", "utk": "untuk",
    "thd": "terhadap", "sdh": "sudah", "sudah": "sudah", "blm": "belum",
    "jgn": "jangan", "klo": "kalau", "klw": "kalau", "klu": "kalau",
    "bkn": "bukan", "bs": "bisa", "bsk": "besok", "hr": "hari",
    "mgkn": "mungkin", "pake": "pakai", "pke": "pakai", "aja": "saja",
    "ajah": "saja", "aj": "saja", "dah": "sudah", "deh": "sudah",
    "nih": "ini", "sih": "ini", "itu": "itu", "gue": "saya", "gw": "saya",
    "gua": "saya", "lu": "kamu", "lw": "kamu", "loe": "kamu",
    "banget": "sangat", "banged": "sangat", "parah": "sangat",
    "nggak": "tidak", "enggak": "tidak", "gak": "tidak",
    "cuman": "cuma", "cm": "cuma", "doang": "saja",
    "udah": "sudah", "belom": "belum", "blom": "belum",
    "kayak": "seperti", "kyk": "seperti", "kek": "seperti",
    "bgt": "banget", "bngett": "banget",
    "gimana": "bagaimana", "gmna": "bagaimana",
    "kenapa": "mengapa", "knp": "mengapa",
    "parah": "sangat", "mantap": "bagus", "keren": "bagus",
    "jelek": "buruk", "payah": "buruk", "rusak": "buruk",
}


def clean_text(text: str) -> str:
    """Clean satu teks."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()
    words = [SLANG_MAP.get(w, w) for w in words]
    return " ".join(words)


def preprocess_texts(texts: list[str]) -> list[str]:
    """Preprocess list teks."""
    return [clean_text(t) for t in tqdm(texts, desc="Preprocessing")]


def main(argv=None):
    out = Path(PROCESSED_DIR)
    out.mkdir(parents=True, exist_ok=True)
    results = {}

    reviews_path = Path(RAW_DIR) / "play_reviews_all.json"
    if reviews_path.exists():
        with reviews_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        reviews = data.get("reviews", [])
        if reviews:
            df = pd.DataFrame(reviews)
            df["content_clean"] = preprocess_texts(df["content"].fillna("").tolist())
            df.to_csv(out / "reviews_preprocessed.csv", index=False, encoding="utf-8")
            results["reviews"] = len(df)

    tiktok_path = Path(RAW_DIR) / "tiktok_comments.json"
    if tiktok_path.exists():
        with tiktok_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        comments = data.get("comments", [])
        if comments:
            df = pd.DataFrame(comments)
            df["text_clean"] = preprocess_texts(df["text"].fillna("").tolist())
            df.to_csv(out / "tiktok_preprocessed.csv", index=False, encoding="utf-8")
            results["tiktok"] = len(df)

    twitter_path = Path(RAW_DIR) / "twitter_tweets.json"
    if twitter_path.exists():
        with twitter_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        tweets = data.get("tweets", [])
        if tweets:
            df = pd.DataFrame(tweets)
            df["text_clean"] = preprocess_texts(df["text"].fillna("").tolist())
            df.to_csv(out / "twitter_preprocessed.csv", index=False, encoding="utf-8")
            results["twitter"] = len(df)

    print("\n=== PREPROCESSING RESULTS ===")
    for k, v in results.items():
        print(f"  {k:15s}: {v} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
