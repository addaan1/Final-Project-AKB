"""Area B — Behavioral (galbay) signal analysis.

Category breakdown, binary distress flag, severity scoring, and keyword
scan over review text.

Penggunaan (dari scripts/analyze.py):
    from behavior_analysis import count_categories, flag_distress, keyword_scan, score_severity
"""
from __future__ import annotations

import re
from collections import Counter

import pandas as pd

BEH_LABEL = {
    "produk_fintech": "Diskusi Produk Fintech",
    "bunga_dan_biaya": "Keluhan Bunga & Biaya",
    "tagihan_dan_penagihan": "Tagihan & Penagihan (DC)",
    "psikologi_avoidance": "Psikologi: Menghindar",
    "distress_langsung": "Distress Finansial Langsung",
    "psikologi_regret_stress": "Psikologi: Penyesalan/Stres",
    "psikologi_impulsif": "Psikologi: Impulsif",
}

DISTRESS_TAGS = {
    "distress_langsung", "tagihan_dan_penagihan", "psikologi_regret_stress", "psikologi_avoidance",
}

KEYWORD_PATTERNS = {
    "gagal bayar/galbay": r"galbay|gagal bayar",
    "telat/nunggak": r"telat|nunggak|tunggak",
    "denda": r"denda|pinalti|penalti",
    "bunga tinggi": r"bunga",
    "debt collector/DC": r"\bdc\b|debt collector|penagih|nagih",
    "teror/ancam": r"teror|ancam|sebar data|intimidasi",
    "pinjol ilegal": r"\bilegal\b|\blegal\b|\bojk\b",
    "gali lubang tutup lubang": r"gali lubang|tutup lubang|pinjam.*bayar",
}


def _split_categories(mc) -> list[str]:
    return [c.strip() for c in str(mc or "").split(",") if c.strip()]


def count_categories(df: pd.DataFrame, mc_col: str = "matched_categories_str") -> list[dict]:
    """Frequency of each matched behavioral category, most common first."""
    counter = Counter()
    for mc in df[mc_col].fillna(""):
        counter.update(_split_categories(mc))
    return [{"key": k, "label": BEH_LABEL.get(k, k), "count": int(v)} for k, v in counter.most_common()]


def flag_distress(
    df: pd.DataFrame, mc_col: str = "matched_categories_str", distress_tags: set[str] = DISTRESS_TAGS
) -> pd.Series:
    """Binary flag: 1 if any matched category is a distress-signal tag."""
    def _is_distress(mc):
        return int(any(tag in distress_tags for tag in _split_categories(mc)))
    return df[mc_col].fillna("").apply(_is_distress)


def keyword_scan(
    df: pd.DataFrame, content_col: str = "content", patterns: dict[str, str] = KEYWORD_PATTERNS
) -> list[dict]:
    """Count of reviews containing each galbay-related keyword pattern, sorted descending."""
    content_low = df[content_col].fillna("").str.lower()
    counts = [
        {"label": label, "count": int(content_low.str.contains(pattern, regex=True, na=False).sum())}
        for label, pattern in patterns.items()
    ]
    counts.sort(key=lambda x: -x["count"])
    return counts


SEVERITY_BUCKETS = (("rendah", 0, 33), ("sedang", 33, 66), ("tinggi", 66, 101))


def _severity_bucket(score: float) -> str:
    for label, lo, hi in SEVERITY_BUCKETS:
        if lo <= score < hi:
            return label
    return SEVERITY_BUCKETS[-1][0]


def score_severity(
    df: pd.DataFrame,
    mc_col: str = "matched_categories_str",
    content_col: str = "content",
    distress_tags: set[str] = DISTRESS_TAGS,
    patterns: dict[str, str] = KEYWORD_PATTERNS,
    max_categories: int = 3,
    max_keywords: int = 3,
) -> pd.DataFrame:
    """0-100 distress severity per review.

    Half the score comes from how many distinct distress categories matched,
    half from how many galbay keywords matched in the text — richer than the
    binary `distress` flag, which can't distinguish a review hitting one
    signal from one hitting several.
    """
    content_low = df[content_col].fillna("").str.lower()
    compiled = [re.compile(p) for p in patterns.values()]

    cat_hits = df[mc_col].fillna("").apply(
        lambda mc: sum(1 for tag in _split_categories(mc) if tag in distress_tags)
    )
    kw_hits = content_low.apply(lambda text: sum(1 for p in compiled if p.search(text)))

    cat_score = (cat_hits.clip(upper=max_categories) / max_categories) * 50
    kw_score = (kw_hits.clip(upper=max_keywords) / max_keywords) * 50
    severity = (cat_score + kw_score).round(1)

    return pd.DataFrame(
        {"severity": severity, "severity_bucket": severity.apply(_severity_bucket)},
        index=df.index,
    )
