# Data Documentation

Dokumentasi sumber data, skema, dan etika scraping untuk reproducibility.

## Sumber data

| Source | Status | Lokasi output | Format |
|---|---|---|---|
| Google Play reviews (fintech) | ✅ Aktif | `data/raw/play_reviews_*.json` + `data/processed/galbay_reviews.xlsx` | JSON + Excel 7-sheet |
| Google Trends | ✅ Aktif | `data/raw/google_trends_12m.json` | time-series JSON |
| TikTok komentar | 🔲 Stub | - | - |
| Twitter/X | 🔲 Stub | - | - |
| Instagram | 🔲 Stub | - | - |
| Forum (Kaskus/Reddit) | 🔲 Stub | - | - |
| OJK & berita media | 🔲 Stub | - | - |

## Dataset saat ini (Mei 2025)

- **24 app fintech** Indonesia (paylater, e-wallet, e-commerce, pinjol, P2P, banking, investasi).
- **72.000 review** total (mode all, cap 3.000/app).
- **5.825 review relevan galbay** (8,09%) — mengandung 65+ keyword psikologis.
- **36 MB** JSON raw + **5,25 MB** Excel processed + **106 KB** Excel sample.

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

## Skema Excel: `galbay_reviews.xlsx` (7 sheet)

| Sheet | Kolom utama | Deskripsi |
|---|---|---|
| **Overview** | Metric, Value | Ringkasan meta scrape |
| **All Reviews** | query, category, app_name, score, content, content_len, thumbs_up, date, year_month, is_relevant, matched_categories_str, n_matched_categories, replied, version | Semua review |
| **Relevant Only** | (sama minus is_relevant) | Filter `is_relevant=true` |
| **Per-App Summary** | query, category, app_name, n_reviews, n_relevant, avg_score, median_score, n_score_1, n_score_5, avg_content_len, date_min, date_max, relevant_rate | Statistik per app |
| **Keyword Frequency** | category, keyword, total_occurrence, in_relevant | Frekuensi 65+ keyword |
| **Score Distribution** | query, score_1, score_2, score_3, score_4, score_5, Total | Cross-tab app × rating |
| **Timeline** | year_month, <app1>, <app2>, ..., Total | Review per bulan per app |

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
  - `galbay_reviews_sample.xlsx` (Excel 7-sheet, ~500 baris/app)
