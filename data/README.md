# Data Documentation

Dokumentasi sumber data, skema, dan etika scraping untuk reproducibility.

## Sumber data

| Source | Status | Lokasi output | Format |
|---|---|---|---|
| Google Play reviews (fintech) | ✅ Aktif (72K) | `data/raw/play_reviews_*.json` + `data/processed/*.csv` | JSON + 7 CSV |
| Google Trends | ✅ Aktif (pytrends) | `data/raw/google_trends_12m.json` | time-series JSON |
| Kaskus threads | ✅ Aktif via Playwright (66) | `data/raw/kaskus_threads.json` | JSON |
| OJK + media (kompas/detik/cnbc) | ✅ Aktif (89) | `data/raw/news_all.json` | JSON |
| TikTok komentar | ⚠️ Implementasi siap, headless blocked | `data/raw/tiktok_comments.json` | JSON |
| Reddit | ⚠️ Network timeout dari env ini | `data/raw/reddit_posts.json` | JSON |
| Twitter/X | ⚠️ Login wall (butuh auth) | `data/raw/twitter_tweets.json` | JSON |
| Instagram | 🔲 Stub | - | - |

## Dataset saat ini (Juni 2025)

- **24 app fintech** Indonesia (paylater, e-wallet, e-commerce, pinjol, P2P, banking, investasi).
- **72.000 review** Google Play (mode all, cap 3.000/app).
- **5.823 review relevan galbay** (8,09%) — mengandung 65+ keyword psikologis.
- **66 Kaskus threads** via Playwright render.
- **89 artikel OJK + media** (16 OJK + 73 media besar).
- **36 MB** JSON raw + **7 CSV** processed + 5 charts PNG + SQLite DB (15.8 MB).

## Skema: `play_reviews_*.json` & `play_reviews_all.json`

```json
{
  "meta": {
    "source": "google_play_reviews",
    "scraped_at": "ISO-8601 UTC",
    "scraper": "fintech_reviews",
    "mode": "all",
    "n_apps": 24,
    "n_reviews_total": 72000,
    "max_per_app": 3000,
    "keyword_groups": ["distress_langsung", "tagihan_dan_penagihan", ...],
    "per_app": [{"app_id": "...", "app_name": "...", "category": "...", "n_reviews": 3000, "n_relevant": 185}]
  },
  "reviews": [
    {
      "app_id": "com.finaccel.android",
      "app_name": "Kredivo - Paylater & Pinjaman",
      "query": "Kredivo",
      "category": "paylater",
      "review_id": "...",
      "score": 1,
      "content": "teks review",
      "thumbs_up": 12,
      "at": "ISO-8601",
      "replied": false,
      "version": "x.y.z",
      "is_relevant": true,
      "matched_categories": ["distress_langsung", "tagihan_dan_penagihan"],
      "n_matched_categories": 2
    }
  ]
}
```

## CSV Output (7 file di `data/processed/`)

| File | Kolom utama | Deskripsi |
|---|---|---|
| `overview.csv` | metric, value | Ringkasan meta scrape |
| `all_reviews.csv` | query, category, app_name, score, content, content_len, thumbs_up, date, year_month, is_relevant, matched_categories_str, n_matched_categories, replied, version | Semua review |
| `relevant_only.csv` | (sama minus is_relevant) | Filter `is_relevant=true` |
| `per_app_summary.csv` | query, category, app_name, n_reviews, n_relevant, avg_score, median_score, n_score_1, n_score_5, avg_content_len, date_min, date_max, relevant_rate | Statistik per app |
| `keyword_frequency.csv` | category, keyword, total_occurrence, in_relevant | Frekuensi 65+ keyword |
| `score_distribution.csv` | query, score_1, score_2, score_3, score_4, score_5, Total | Cross-tab app × rating |
| `timeline.csv` | year_month, <app1>, <app2>, ..., Total | Review per bulan per app |

## Processing Pipeline

| Step | Modul | Output |
|---|---|---|
| 1. Build CSV | `processing.build_csv` | 7 CSV di `data/processed/` |
| 2. Validation | `processing.validate` | `validated_*.csv` (dedup, clean) |
| 3. Sentiment | `processing.sentiment` | `*_with_sentiment.csv` (VADER scores) |
| 4. Preprocessing | `processing.preprocess` | `*_preprocessed.csv` (NLP cleaned) |
| 5. Visualization | `processing.visualize` | `data/processed/charts/*.png` |
| 6. SQLite export | `processing.export_sqlite` | `data/processed/galbay.db` |

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

## Aplikasi yang di-scrape (24 app)

| Kategori | App | appId |
|---|---|---|
| paylater | Kredivo, Akulaku, Indodana | com.finaccel.android, io.silvrr.installment, com.indodana.app |
| ecommerce | Shopee, Tokopedia, Lazada, Bukalapak | com.shopee.id, com.tokopedia.tkpd, com.lazada.android, com.bukalapak.android |
| travel | Traveloka, Tiket.com | com.traveloka.android, com.tiket.gits |
| ewallet | Gojek, GoPay, OVO, DANA, LinkAja, Sakuku | com.gojek.app, com.gojek.gopay, ovo.id, id.dana, com.telkom.mwallet, com.bca.sakuku |
| pinjol | RupiahCepat, KreditPintar, Tunaiku, AdaKami, Easycash, UangMe | (lihat APP_IDS di scraper) |
| p2p_lending | KoinWorks | com.koinworks.app |
| mobile_banking | BRImo | id.co.bri.brimo |
| investasi | Stockbit | com.stockbit.android |

## Etika & PII

- Hanya data publik (review app store, postingan publik).
- Tidak menyimpan PII (nama asli, no HP, email user). `review_id` & `userName` di-redact/buang di tahap `data/processed/`.
- Rate-limit sopan via `polite_sleep()`; hormati ToS platform.
- Tanggal scrape & sumber dicatat di field `meta.scraped_at` & `meta.source`.

## Distribusi dataset besar

- File `data/raw/*` dan `data/processed/*` **di-gitignore** (>50MB).
- Untuk distribusi: **GitHub Releases** atau **Git LFS** (konfigurasi menyusul).
- Sample kecil (`data/sample/`) di-commit untuk reproducibility:
  - `play_reviews_sample.json` (1000 baris JSON)
