# Data Documentation

Dokumentasi sumber data, skema, dan etika scraping untuk reproducibility.

<<<<<<< HEAD
## ⚠️ Big Data di Google Drive

Dataset terlalu besar untuk GitHub. **Lihat [DOWNLOAD.md](DOWNLOAD.md) untuk cara download dari Google Drive.**

**Link:** https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_

## Sumber data: Google Play Store (single source)

| Source | Status | Lokasi output | Format |
|---|---|---|---|
| **Google Play reviews (44 app)** | ✅ **Sumber utama (349K)** | `data/raw/play_reviews_*.json` | JSON |
| Google Trends | ✅ Pelengkap time-series | `data/raw/google_trends_12m.json` | JSON |
| Kaskus threads | ⚠️ Data tersedia (152) | `data/raw/kaskus_threads.json` | JSON |
| OJK + media | ⚠️ Data tersedia (163) | `data/raw/news_all.json` | JSON |
| Blog posts | ⚠️ Data tersedia (44) | `data/raw/blogs_all.json` | JSON |
| Apple App Store | ❌ 0 review | - | - |
| TikTok, Twitter, Reddit, YouTube | ❌ Blocked | - | - |

> **Catatan:** Dataset utama berasal dari **Google Play Store review** (single source). Data dari Kaskus, OJK, dan blog tersedia di `data/raw/` namun belum diintegrasikan ke CSV utama.

## Dataset saat ini (Juni 2025)

- **44 app fintech** Indonesia (paylater, e-wallet, e-commerce, pinjol, P2P, bank digital, banking, investasi).
- **349.200 review** Google Play (mode all, cap 3K-15K/app).
- **35.968 review relevan galbay** (10,30%) — mengandung 65+ keyword psikologis.
- **~100 MB** JSON raw + **~70 MB** CSV processed + 5 charts PNG + SQLite DB (74 MB).

## CSV Output (4 file di `data/processed/`)

| File | Rows | Size | Fungsi |
|---|---|---|---|
| `reviews_with_sentiment.csv` | 349.200 | 78 MB | **FILE UTAMA** — semua review + sentiment VADER |
| `relevant_only.csv` | 35.968 | 8 MB | **FILE KUNCI** — hanya review galbay relevan |
| `per_app_summary.csv` | 44 | <1 MB | Ringkasan statistik per app |
| `timeline.csv` | 50 | <1 MB | Tren review per bulan |

> **Yang dipakai untuk analisis:**
> - `reviews_with_sentiment.csv` — gunakan ini sebagai dataset utama (semua data + sentiment)
> - `relevant_only.csv` — gunakan ini jika hanya ingin data galbay relevan

## Skema: `reviews_with_sentiment.csv` (FILE UTAMA)

```
app_id, app_name, query, category, review_id, score, content, thumbs_up,
at, replied, version, is_relevant, matched_categories, n_matched_categories,
date, year_month, content_len, sentiment_pos, sentiment_neg, sentiment_neu,
sentiment_compound, sentiment_label
```

## Processing Pipeline

| Step | Modul | Output |
|---|---|---|
| 1. Build CSV | `processing.build_csv` | 3 CSV (relevant_only, per_app_summary, timeline) |
| 2. Sentiment | `processing.sentiment` | `reviews_with_sentiment.csv` ← **file utama** |
| 3. Visualization | `processing.visualize` | `data/processed/charts/*.png` |
| 4. SQLite export | `processing.export_sqlite` | `data/processed/galbay.db` |

## Keyword sinyal psikologis (65+ keyword, 7 kategori)

| Kategori | Keyword contoh |
|---|---|
| `distress_langsung` | galbay, gagal bayar, nunggak, macet, telat bayar |
| `tagihan_dan_penagihan` | ditagih, tagihan, debt collector, dc, dicerewet |
| `bunga_dan_biaya` | bunga, denda, biaya admin, bunga tinggi |
| `produk_fintech` | paylater, pinjol, cicilan, kasbon, limit, tenor |
| `psikologi_impulsif` | self reward, checkout dulu, fomo, flash sale, gpp cicil |
| `psikologi_avoidance` | takut ditagih, kabur, ganti nomor, diblokir |
| `psikologi_regret_stress` | menyesal, insyaf, stress, depresi, susah tidur |

Lihat `scraper/fintech_reviews.py` untuk daftar lengkap (`GALBAY_KEYWORDS` dict).

## Etika & PII

- Hanya data publik (review app store).
- Tidak menyimpan PII (nama asli, no HP, email user).
- Rate-limit sopan via `polite_sleep()`.
- Tanggal scrape & sumber dicatat di field `meta.scraped_at` & `meta.source`.
=======
## Sumber data

| Source | Status | Lokasi output | Skema |
|---|---|---|---|
| Google Play reviews (fintech) | Aktif | `data/raw/play_reviews_*.json` | lihat bawah |
| Google Trends | Aktif | `data/raw/google_trends_12m.json` | time-series |
| TikTok komentar | Stub | - | - |
| Twitter/X | Stub | - | - |
| Instagram | Stub | - | - |
| Forum (Kaskus/Reddit) | Stub | - | - |
| OJK & berita media | Stub | - | - |

## Skema: `play_reviews_*.json`

```json
{
  "meta": {
    "source": "google_play_reviews",
    "scraped_at": "ISO-8601 UTC",
    "scraper": "fintech_reviews",
    "n_apps": 24,
    "n_reviews_total": 9600,
    "count_per_app": 400,
    "per_app": [{"app_id": "...", "app_name": "...", "n_reviews": 400, "n_relevant": 87}]
  },
  "reviews": [
    {
      "app_id": "com.app.id",
      "app_name": "Kredivo",
      "query": "Kredivo",
      "review_id": "...",
      "score": 1,
      "content": "teks review",
      "thumbs_up": 12,
      "at": "ISO-8601",
      "replied": false,
      "version": "x.y.z",
      "is_relevant": true
    }
  ]
}
```

## Keyword sinyal galbay (untuk flag `is_relevant`)

`galbay`, `gagal bayar`, `ditagih`, `tagihan`, `tagih`, `dendanya`, `bunga`,
`menagih`, `debt collector`, `dc`, `dicerewet`, `kasbon`, `paylater`, `pay later`,
`pinjol`, `pinjaman online`, `cicilan`, `telat bayar`, `nunggak`, `macet`,
`limit`, `penagih`

## Etika & PII

- Hanya data publik (review app store, postingan publik).
- Tidak menyimpan PII (nama asli, no HP, email user). Atribut `review_id` &
  `userName` di-redact/buang di tahap `data/processed/`.
- Rate-limit sopan via `polite_sleep()`; hormati ToS platform.
- Tanggal scrape & sumber dicatat di field `meta.scraped_at` & `meta.source`.

## Distribusi dataset besar

- File `data/raw/*` dan `data/processed/*` **di-gitignore** (>50MB).
- Untuk distribusi: **GitHub Releases** atau **Git LFS** (konfigurasi menyusul).
- Sample kecil (`data/sample/`) di-commit untuk reproducibility.
>>>>>>> origin/main
