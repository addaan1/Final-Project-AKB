# Data Documentation

Dokumentasi sumber data, skema, dan etika scraping untuk reproducibility.

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
