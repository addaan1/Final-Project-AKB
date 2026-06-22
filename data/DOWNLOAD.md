# Download Big Data (Google Drive)

Dataset Galbay Predictor terlalu besar untuk GitHub (>100MB). Kami menggunakan
**DVC (Data Version Control) + Google Drive** untuk distribusi big data.

## Link Google Drive

**Folder:** https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_

## Struktur folder Drive

```
galbay-predictor-data/
├── raw/                          # Data mentah dari scraping
│   ├── play_reviews_all.json     # 349.200 review Google Play (gabungan)
│   ├── play_reviews_<app>.json   # Per-app JSON (45 file)
│   ├── kaskus_threads.json
│   ├── forum_all.json
│   ├── news_all.json
│   ├── ojk_articles.json
│   ├── media_articles.json
│   └── blogs_all.json
└── processed/                    # Data hasil processing
    ├── all_reviews.csv           # 349K review (CSV utama)
    ├── relevant_only.csv         # 35.968 review galbay relevan
    ├── per_app_summary.csv
    ├── timeline.csv
    ├── reviews_with_sentiment.csv
    ├── reviews_preprocessed.csv
    ├── validated_reviews.csv
    ├── galbay.db                 # SQLite database
    └── charts/                   # 5 PNG charts
```

## Cara download

### Opsi 1: Manual download (paling simple)
1. Buka link Google Drive di atas
2. Pilih folder yang mau didownload (`raw/` atau `processed/`)
3. Klik "Download" atau drag ke local

### Opsi 2: DVC pull (rekomendasi)
```bash
# Clone repo
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB

# Install DVC
pip install dvc dvc-gdrive

# Authenticate Google Drive (browser akan terbuka)
# Ikuti instruksi di layar untuk login dengan akun Google yang punya akses ke folder

# Pull data dari Google Drive
dvc pull
```

## Ringkasan dataset

| Source | Jumlah | Kategori |
|---|---|---|
| **Google Play Reviews** | 349.200 review | Multi-fintech (44 app) |
| Kaskus threads | 152 thread | Forum diskusi |
| OJK + Media | 163 artikel | Berita & regulasi |
| Blog posts | 44 post | Edukasi finansial |
| **Total** | **349.559+ items** | |

**Review relevan galbay:** 35.968 (10,30%)

**Sentiment:**
- Positive: 40.668
- Negative: 6.481
- Neutral: 302.051

## Update dataset

Jika dataset di-update (re-scrape), jalankan:
```bash
dvc add data/raw data/processed
dvc push
```

Ini akan upload file baru ke Google Drive dengan versioning DVC.

## Catatan

- File di Google Drive hanya untuk distribusi, bukan versi terbaru
- Versi terbaru selalu di repo ini (lihat `data/raw/` dan `data/processed/`)
- Untuk kontribusi: clone repo → edit → `dvc push` → commit `.dvc` files
- Google Drive folder di-share read-only untuk publik
