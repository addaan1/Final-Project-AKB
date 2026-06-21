"""Build 7 CSV terpisah dari data review Google Play.

Output ke data/processed/:
1. overview.csv           — ringkasan meta scrape
2. all_reviews.csv        — semua review
3. relevant_only.csv      — review berisi keyword galbay
4. per_app_summary.csv    — statistik per app
5. keyword_frequency.csv  — frekuensi keyword sinyal
6. score_distribution.csv — distribusi rating per app
7. timeline.csv           — review per bulan per app

Penggunaan:
    python -m processing.build_csv
    python -m processing.build_csv --sample-rows 500
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from config import RAW_DIR, PROCESSED_DIR, SAMPLE_DIR
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


def build_overview(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    n_apps = df["query"].nunique() if "query" in df else 0
    n_relevant = int(df["is_relevant"].sum()) if "is_relevant" in df else 0
    date_min = df["at"].min().strftime("%Y-%m-%d") if pd.notna(df["at"].min()) else "-"
    date_max = df["at"].max().strftime("%Y-%m-%d") if pd.notna(df["at"].max()) else "-"

    rows = [
        {"metric": "source", "value": meta.get("source", "google_play_reviews")},
        {"metric": "scraped_at", "value": meta.get("scraped_at", "-")},
        {"metric": "scraper", "value": meta.get("scraper", "-")},
        {"metric": "mode", "value": meta.get("mode", "-")},
        {"metric": "total_apps", "value": str(n_apps)},
        {"metric": "total_reviews", "value": str(len(df))},
        {"metric": "relevant_reviews", "value": str(n_relevant)},
        {"metric": "relevant_rate", "value": f"{n_relevant/len(df)*100:.2f}%" if len(df) else "-"},
        {"metric": "avg_score", "value": str(round(float(df["score"].mean()), 2)) if "score" in df else "-"},
        {"metric": "avg_content_len", "value": str(round(float(df["content_len"].mean()), 1)) if "content_len" in df else "-"},
        {"metric": "date_min", "value": date_min},
        {"metric": "date_max", "value": date_max},
    ]
    return pd.DataFrame(rows)


def build_all_reviews(df: pd.DataFrame) -> pd.DataFrame:
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "is_relevant", "matched_categories_str",
            "n_matched_categories", "replied", "version"]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    return out.sort_values(["query", "date"], ascending=[True, False])


def build_relevant_only(df: pd.DataFrame) -> pd.DataFrame:
    if "is_relevant" not in df.columns:
        return pd.DataFrame()
    rel = df[df["is_relevant"]].copy()
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "matched_categories_str",
            "n_matched_categories"]
    cols = [c for c in cols if c in rel.columns]
    return rel[cols].sort_values(["query", "date"], ascending=[True, False])


def build_per_app_summary(df: pd.DataFrame) -> pd.DataFrame:
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


def build_keyword_frequency(df: pd.DataFrame) -> pd.DataFrame:
    if "content" not in df.columns:
        return pd.DataFrame()
    rows = []
    for cat, kws in GALBAY_KEYWORDS.items():
        for kw in kws:
            n = int(df["content"].fillna("").str.lower().str.contains(kw, regex=False).sum())
            n_relevant = int(df[df["is_relevant"]]["content"].fillna("").str.lower().str.contains(kw, regex=False).sum()) if "is_relevant" in df.columns else 0
            rows.append({"category": cat, "keyword": kw, "total_occurrence": n, "in_relevant": n_relevant})
    freq = pd.DataFrame(rows).sort_values(["category", "total_occurrence"], ascending=[True, False])
    return freq


def build_score_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if "score" not in df.columns or "query" not in df.columns:
        return pd.DataFrame()
    ct = pd.crosstab(df["query"], df["score"], margins=True, margins_name="Total")
    ct.columns = [f"score_{c}" if c != "Total" else c for c in ct.columns]
    ct = ct.reset_index()
    return ct


def build_timeline(df: pd.DataFrame) -> pd.DataFrame:
    if "year_month" not in df.columns or "query" not in df.columns:
        return pd.DataFrame()
    tl = df.groupby(["year_month", "query"]).size().reset_index(name="n_reviews")
    tl = tl.pivot(index="year_month", columns="query", values="n_reviews").fillna(0).astype(int)
    tl["Total"] = tl.sum(axis=1)
    tl = tl.reset_index().sort_values("year_month")
    return tl


def write_csvs(df: pd.DataFrame, meta: dict, out_dir: Path) -> dict[str, Path]:
    """Tulis 7 CSV ke out_dir. Return dict {name: path}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    log.info("Writing CSVs -> %s", out_dir)

    files = {}
    for name, frame in [
        ("overview", build_overview(df, meta)),
        ("all_reviews", build_all_reviews(df)),
        ("relevant_only", build_relevant_only(df)),
        ("per_app_summary", build_per_app_summary(df)),
        ("keyword_frequency", build_keyword_frequency(df)),
        ("score_distribution", build_score_distribution(df)),
        ("timeline", build_timeline(df)),
    ]:
        path = out_dir / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8")
        files[name] = path
        log.info("  %s.csv: %d rows (%.1f KB)", name, len(frame), path.stat().st_size / 1e3)

    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build 7 CSV dari review JSON")
    parser.add_argument("--input", default=str(Path(RAW_DIR) / "play_reviews_all.json"), help="Path JSON raw")
    parser.add_argument("--output", default=str(PROCESSED_DIR), help="Dir output CSV")
    args = parser.parse_args(argv)

    df, meta = load_reviews(Path(args.input))
    files = write_csvs(df, meta, Path(args.output))

    print("\n=== RINGKASAN CSV ===")
    print(f"Total review : {len(df)}")
    print(f"Relevant     : {int(df['is_relevant'].sum())} ({df['is_relevant'].mean()*100:.2f}%)")
    print(f"Apps         : {df['query'].nunique()}")
    print(f"Output dir   : {args.output}")
    for name, path in files.items():
        print(f"  {name:22s} {path.stat().st_size/1e3:8.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
