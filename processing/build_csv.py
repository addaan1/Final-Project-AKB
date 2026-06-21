"""Build CSV dari data review Google Play.

Output 4 CSV utama di data/processed/:
1. all_reviews.csv    — semua review (data utama, ~11 MB)
2. relevant_only.csv  — review berisi keyword galbay (sinyal psikologis)
3. per_app_summary.csv — statistik per app (agregat untuk analisis)
4. timeline.csv       — review per bulan per app (tren waktu)

CSV lain (overview, keyword_frequency, score_distribution) dihapus karena:
- overview: info sudah ada di meta JSON & README
- keyword_frequency: bisa di-generate on-demand dari all_reviews
- score_distribution: mirip per_app_summary, bisa di-generate

Penggunaan:
    python -m processing.build_csv
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from config import RAW_DIR, PROCESSED_DIR
from scraper.fintech_reviews import GALBAY_KEYWORDS

log = logging.getLogger("processing.build_csv")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def load_reviews(raw_path: Path) -> tuple[pd.DataFrame, dict]:
    """Load JSON raw dan return (DataFrame, meta)."""
    log.info("Loading %s", raw_path)
    with raw_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    meta = data.get("meta", {})
    rows = data.get("reviews", [])
    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("Dataset kosong.")
    if "at" in df.columns:
        df["at"] = pd.to_datetime(df["at"], errors="coerce", utc=True)
        df["date"] = df["at"].dt.strftime("%Y-%m-%d")
        df["year_month"] = df["at"].dt.strftime("%Y-%m")
    df["content_len"] = df["content"].fillna("").str.len()
    df["matched_categories_str"] = df["matched_categories"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else ""
    )
    log.info("Loaded %d rows, %d apps", len(df), df["query"].nunique() if "query" in df else 0)
    return df, meta


def build_all_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """Semua review (data utama)."""
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "is_relevant", "matched_categories_str",
            "n_matched_categories", "replied", "version"]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    return out.sort_values(["query", "date"], ascending=[True, False])


def build_relevant_only(df: pd.DataFrame) -> pd.DataFrame:
    """Hanya review berisi keyword galbay (sinyal psikologis)."""
    if "is_relevant" not in df.columns:
        return pd.DataFrame()
    rel = df[df["is_relevant"]].copy()
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "matched_categories_str",
            "n_matched_categories"]
    cols = [c for c in cols if c in rel.columns]
    return rel[cols].sort_values(["query", "date"], ascending=[True, False])


def build_per_app_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Statistik per app (agregat untuk analisis)."""
    g = df.groupby(["query", "category", "app_name"]).agg(
        n_reviews=("content", "count"),
        n_relevant=("is_relevant", "sum"),
        avg_score=("score", "mean"),
        median_score=("score", "median"),
        n_score_1=("score", lambda s: int((s == 1).sum())),
        n_score_5=("score", lambda s: int((s == 5).sum())),
        avg_content_len=("content_len", "mean"),
        date_min=("at", "min"),
        date_max=("at", "max"),
    ).reset_index()
    g["relevant_rate"] = (g["n_relevant"] / g["n_reviews"] * 100).round(2)
    g["avg_score"] = g["avg_score"].round(2)
    g["median_score"] = g["median_score"].round(2)
    g["avg_content_len"] = g["avg_content_len"].round(1)
    g["date_min"] = g["date_min"].dt.strftime("%Y-%m-%d")
    g["date_max"] = g["date_max"].dt.strftime("%Y-%m-%d")
    return g.sort_values("relevant_rate", ascending=False)


def build_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Review per bulan per app (tren waktu)."""
    if "year_month" not in df.columns or "query" not in df.columns:
        return pd.DataFrame()
    tl = df.groupby(["year_month", "query"]).size().reset_index(name="n_reviews")
    tl = tl.pivot(index="year_month", columns="query", values="n_reviews").fillna(0).astype(int)
    tl["Total"] = tl.sum(axis=1)
    tl = tl.reset_index().sort_values("year_month")
    return tl


def write_csvs(df: pd.DataFrame, out_dir: Path) -> dict[str, Path]:
    """Tulis 4 CSV utama ke out_dir. Return dict {name: path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("Writing 4 CSV utama -> %s", out_dir)

    files = {}
    for name, frame in [
        ("all_reviews", build_all_reviews(df)),
        ("relevant_only", build_relevant_only(df)),
        ("per_app_summary", build_per_app_summary(df)),
        ("timeline", build_timeline(df)),
    ]:
        path = out_dir / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        files[name] = path
        log.info("  %s.csv: %d rows (%.1f KB)", name, len(frame), path.stat().st_size / 1e3)

    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build 4 CSV utama dari review JSON")
    parser.add_argument("--input", default=str(Path(RAW_DIR) / "play_reviews_all.json"), help="Path JSON raw")
    parser.add_argument("--output", default=str(PROCESSED_DIR), help="Dir output CSV")
    args = parser.parse_args(argv)

    df, meta = load_reviews(Path(args.input))
    files = write_csvs(df, Path(args.output))

    print("\n=== RINGKASAN CSV (4 file utama) ===")
    print(f"Total review : {len(df)}")
    print(f"Relevant     : {int(df['is_relevant'].sum())} ({df['is_relevant'].mean()*100:.2f}%)")
    print(f"Apps         : {df['query'].nunique()}")
    print(f"Output dir   : {args.output}")
    for name, path in files.items():
        print(f"  {name:22s} {path.stat().st_size/1e3:8.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
