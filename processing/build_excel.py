"""Build Excel multi-sheet dari data review Google Play.

Menghasilkan galbay_reviews.xlsx dengan 7 sheet:
1. Overview        — ringkasan meta scrape
2. All Reviews     — semua review (kolom utama)
3. Relevant Only   — review berisi keyword galbay (sinyal psikologis)
4. Per-App Summary — statistik per app
5. Keyword Frequency — frekuensi keyword sinyal
6. Score Distribution — distribusi rating per app
7. Timeline        — review per bulan per app

Penggunaan:
    python -m processing.build_excel
    python -m processing.build_excel --sample-rows 500
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
from config import RAW_DIR, PROCESSED_DIR, SAMPLE_DIR
from scraper.fintech_reviews import GALBAY_KEYWORDS, ALL_GALBAY_KEYWORDS

log = logging.getLogger("processing.build_excel")
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
    # Parse tanggal
    if "at" in df.columns:
        df["at"] = pd.to_datetime(df["at"], errors="coerce", utc=True)
        df["date"] = df["at"].dt.strftime("%Y-%m-%d")
        df["year_month"] = df["at"].dt.strftime("%Y-%m")
    # Text length
    df["content_len"] = df["content"].fillna("").str.len()
    # matched categories sebagai string
    df["matched_categories_str"] = df["matched_categories"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else ""
    )
    log.info("Loaded %d rows, %d apps", len(df), df["query"].nunique() if "query" in df else 0)
    return df, meta


def build_overview(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Sheet 1: Overview."""
    n_apps = df["query"].nunique() if "query" in df else 0
    n_relevant = int(df["is_relevant"].sum()) if "is_relevant" in df else 0
    date_min = df["at"].min().strftime("%Y-%m-%d") if pd.notna(df["at"].min()) else "-"
    date_max = df["at"].max().strftime("%Y-%m-%d") if pd.notna(df["at"].max()) else "-"

    rows = [
        ["Galbay Predictor — Dataset Overview", ""],
        ["", ""],
        ["Source", meta.get("source", "google_play_reviews")],
        ["Scraped at", meta.get("scraped_at", "-")],
        ["Scraper", meta.get("scraper", "-")],
        ["Mode", meta.get("mode", "-")],
        ["", ""],
        ["Total apps", n_apps],
        ["Total reviews", len(df)],
        ["Relevant reviews (galbay)", n_relevant],
        ["Relevant rate", f"{n_relevant/len(df)*100:.2f}%" if len(df) else "-"],
        ["Avg score", round(float(df["score"].mean()), 2) if "score" in df else "-"],
        ["Avg content length", round(float(df["content_len"].mean()), 1) if "content_len" in df else "-"],
        ["Date range", f"{date_min} s/d {date_max}"],
        ["", ""],
        ["Keyword groups", ""],
    ]
    for g in meta.get("keyword_groups", list(GALBAY_KEYWORDS.keys())):
        rows.append([f"  - {g}", len(GALBAY_KEYWORDS.get(g, ()))])

    # Kategori app
    if "category" in df.columns:
        rows.append(["", ""])
        rows.append(["App categories", ""])
        for cat, n in df.groupby("category")["query"].nunique().items():
            rows.append([f"  - {cat}", int(n)])

    return pd.DataFrame(rows, columns=["Metric", "Value"])


def build_all_reviews(df: pd.DataFrame, sample_rows: int = 0) -> pd.DataFrame:
    """Sheet 2: All Reviews (kolom utama)."""
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "is_relevant", "matched_categories_str",
            "n_matched_categories", "replied", "version"]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    out = out.sort_values(["query", "date"], ascending=[True, False])
    if sample_rows and len(out) > sample_rows:
        # sample proporsional per app
        out = out.groupby("query", group_keys=False).head(sample_rows // max(out["query"].nunique(), 1))
    return out


def build_relevant_only(df: pd.DataFrame, sample_rows: int = 0) -> pd.DataFrame:
    """Sheet 3: Relevant Only."""
    if "is_relevant" not in df.columns:
        return pd.DataFrame()
    rel = df[df["is_relevant"]].copy()
    cols = ["query", "category", "app_name", "score", "content", "content_len",
            "thumbs_up", "date", "year_month", "matched_categories_str",
            "n_matched_categories"]
    cols = [c for c in cols if c in rel.columns]
    out = rel[cols].sort_values(["query", "date"], ascending=[True, False])
    if sample_rows and len(out) > sample_rows:
        out = out.groupby("query", group_keys=False).head(sample_rows // max(out["query"].nunique(), 1))
    return out


def build_per_app_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Sheet 4: Per-App Summary."""
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
    """Sheet 5: Keyword Frequency per kategori (diagnosa psikologis)."""
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
    """Sheet 6: Score Distribution (cross-tab app x rating)."""
    if "score" not in df.columns or "query" not in df.columns:
        return pd.DataFrame()
    ct = pd.crosstab(df["query"], df["score"], margins=True, margins_name="Total")
    ct.columns = [f"score_{c}" if c != "Total" else c for c in ct.columns]
    ct = ct.reset_index()
    return ct


def build_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Sheet 7: Timeline review per bulan per app."""
    if "year_month" not in df.columns or "query" not in df.columns:
        return pd.DataFrame()
    tl = df.groupby(["year_month", "query"]).size().reset_index(name="n_reviews")
    tl = tl.pivot(index="year_month", columns="query", values="n_reviews").fillna(0).astype(int)
    tl["Total"] = tl.sum(axis=1)
    tl = tl.reset_index().sort_values("year_month")
    return tl


def write_excel(df: pd.DataFrame, meta: dict, out_path: Path, sample_rows: int = 0) -> Path:
    """Tulis semua sheet ke satu file Excel dengan formatting xlsxwriter."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing Excel -> %s", out_path)

    overview = build_overview(df, meta)
    all_rev = build_all_reviews(df, sample_rows=0)  # full di processed
    relevant = build_relevant_only(df, sample_rows=0)
    per_app = build_per_app_summary(df)
    keyword_freq = build_keyword_frequency(df)
    score_dist = build_score_distribution(df)
    timeline = build_timeline(df)

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as xw:
        workbook = xw.book
        # Format
        fmt_header = workbook.add_format({"bold": True, "bg_color": "#e74c3c", "color": "#ffffff", "border": 1, "text_wrap": True, "valign": "top"})
        fmt_cell = workbook.add_format({"text_wrap": True, "valign": "top", "border": 1})
        fmt_title = workbook.add_format({"bold": True, "font_size": 14, "bg_color": "#1a1d24", "font_color": "#e74c3c"})
        fmt_meta = workbook.add_format({"bg_color": "#f5f5f5", "border": 1})
        fmt_pct = workbook.add_format({"num_format": "0.00%", "border": 1})

        def write_sheet(name: str, frame: pd.DataFrame, freeze_row: int = 1):
            if frame.empty:
                ws = workbook.add_worksheet(name)
                ws.write(0, 0, "(no data)", fmt_title)
                ws.set_column(0, 0, 20)
                return
            frame.to_excel(xw, sheet_name=name, index=False, startrow=0)
            ws = xw.sheets[name]
            for col_idx, col_name in enumerate(frame.columns):
                ws.write(0, col_idx, col_name, fmt_header)
            ws.set_row(0, 28)
            ws.freeze_panes(freeze_row, 0)
            # autofilter
            ws.autofilter(0, 0, len(frame), len(frame.columns) - 1)

        # Overview special formatting
        ws = xw.sheets["Overview"] if "Overview" in xw.sheets else None
        write_sheet("Overview", overview)
        ws = xw.sheets["Overview"]
        ws.set_column(0, 0, 30, fmt_meta)
        ws.set_column(1, 1, 50, fmt_cell)
        ws.set_row(0, 24)

        write_sheet("All Reviews", all_rev)
        ws = xw.sheets["All Reviews"]
        ws.set_column("E:E", 60)  # content
        ws.set_column("A:D", 18)
        ws.set_column("F:I", 14)

        write_sheet("Relevant Only", relevant)
        ws = xw.sheets["Relevant Only"]
        ws.set_column("E:E", 60)
        ws.set_column("A:D", 18)

        write_sheet("Per-App Summary", per_app)
        ws = xw.sheets["Per-App Summary"]
        ws.set_column("A:C", 22)
        ws.set_column("D:N", 14)

        write_sheet("Keyword Frequency", keyword_freq)
        ws = xw.sheets["Keyword Frequency"]
        ws.set_column("A:A", 24)
        ws.set_column("B:B", 32)
        ws.set_column("C:D", 16)

        write_sheet("Score Distribution", score_dist)
        ws = xw.sheets["Score Distribution"]
        ws.set_column("A:A", 22)
        ws.set_column("B:G", 14)

        write_sheet("Timeline", timeline)
        ws = xw.sheets["Timeline"]
        ws.set_column("A:A", 12)
        ws.set_column("B:Z", 14)

    log.info("Excel written: %s (%.2f MB)", out_path, out_path.stat().st_size / 1e6)
    return out_path


def write_sample_excel(df: pd.DataFrame, meta: dict, sample_path: Path, sample_rows: int = 500) -> Path:
    """Excel sample kecil untuk di-commit (reproducibility)."""
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing sample Excel -> %s", sample_path)

    overview = build_overview(df, meta)
    all_rev = build_all_reviews(df, sample_rows=sample_rows)
    relevant = build_relevant_only(df, sample_rows=sample_rows)
    per_app = build_per_app_summary(df)
    keyword_freq = build_keyword_frequency(df)
    score_dist = build_score_distribution(df)
    timeline = build_timeline(df)

    with pd.ExcelWriter(sample_path, engine="xlsxwriter") as xw:
        workbook = xw.book
        fmt_header = workbook.add_format({"bold": True, "bg_color": "#e74c3c", "color": "#ffffff", "border": 1, "text_wrap": True, "valign": "top"})

        def write_sheet(name: str, frame: pd.DataFrame):
            if frame.empty:
                ws = workbook.add_worksheet(name)
                ws.write(0, 0, "(no data)")
                return
            frame.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            for col_idx, col_name in enumerate(frame.columns):
                ws.write(0, col_idx, col_name, fmt_header)
            ws.set_row(0, 24)
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, len(frame), len(frame.columns) - 1)
            if name in ("All Reviews", "Relevant Only"):
                ws.set_column("E:E", 60)

        write_sheet("Overview", overview)
        write_sheet("All Reviews", all_rev)
        write_sheet("Relevant Only", relevant)
        write_sheet("Per-App Summary", per_app)
        write_sheet("Keyword Frequency", keyword_freq)
        write_sheet("Score Distribution", score_dist)
        write_sheet("Timeline", timeline)

    log.info("Sample Excel written: %s (%.2f KB)", sample_path, sample_path.stat().st_size / 1e3)
    return sample_path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Excel dari review JSON")
    parser.add_argument("--input", default=str(Path(RAW_DIR) / "play_reviews_all.json"), help="Path JSON raw")
    parser.add_argument("--output", default=str(Path(PROCESSED_DIR) / "galbay_reviews.xlsx"), help="Path Excel output")
    parser.add_argument("--sample-out", default=str(Path(SAMPLE_DIR) / "galbay_reviews_sample.xlsx"), help="Path Excel sample (di-commit)")
    parser.add_argument("--sample-rows", type=int, default=500, help="Baris per app di sample Excel (di-commit)")
    args = parser.parse_args(argv)

    df, meta = load_reviews(Path(args.input))
    write_excel(df, meta, Path(args.output), sample_rows=0)
    write_sample_excel(df, meta, Path(args.sample_out), sample_rows=args.sample_rows)

    # Ringkasan
    print("\n=== RINGKASAN EXCEL ===")
    print(f"Total review : {len(df)}")
    print(f"Relevant     : {int(df['is_relevant'].sum())} ({df['is_relevant'].mean()*100:.2f}%)")
    print(f"Apps         : {df['query'].nunique()}")
    print(f"Full Excel   : {args.output} ({Path(args.output).stat().st_size/1e6:.2f} MB)")
    print(f"Sample Excel : {args.sample_out} ({Path(args.sample_out).stat().st_size/1e3:.1f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
