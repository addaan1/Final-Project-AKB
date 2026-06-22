# Download Big Data (Google Drive)

Dataset Galbay Predictor terlalu besar untuk GitHub (>100MB). Data disimpan di
**Google Drive** untuk distribusi.

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

### Download manual (satu-satunya cara)

1. Buka link Google Drive di atas
2. Klik folder `raw/` → Download semua file (atau pilih yang dibutuhkan)
3. Klik folder `processed/` → Download semua file
4. Extract/letakkan di folder project:
   ```
   Final-Project-AKB/
   ── data/
       ├── raw/          ← letakkan file raw di sini
       └── processed/    ← letakkan file processed di sini
   ```

### Setelah download

```bash
# Clone repo
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB

# Install dependencies
pip install -r requirements.txt

# Download data dari Google Drive (lihat link di atas)
# Letakkan di folder data/raw/ dan data/processed/

# Jalankan processing (opsional, jika ingin rebuild CSV)
python processing/build_csv.py
python processing/sentiment.py
python processing/visualize.py
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

## Catatan

- File di Google Drive adalah snapshot dataset
- Versi terbaru selalu di repo ini (lihat `data/raw/` dan `data/processed/`)
- Google Drive folder di-share untuk akses tim
