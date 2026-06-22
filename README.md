<div align="center">

# 🩺 Galbay Predictor

### Membaca psikologi gagal bayar anak muda dari jejak digital

*Financial behavior coach berbasis big data — bukan sistem pinjaman, melainkan dokter yang mendiagnosis akar perilaku gagal bayar Gen Z dari pola bahasa digital.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![pandas](https://img.shields.io/badge/pandas-2.2.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![google-play-scraper](https://img.shields.io/badge/google--play--scraper-1.2.7-34A853?logo=googleplay&logoColor=white)](https://github.com/JoMingyu/google-play-scraper)
[![pytrends](https://img.shields.io/badge/pytrends-4.9.2-4285F4?logo=google&logoColor=white)](https://github.com/GeneralMills/pytrends)
[![TikTokApi](https://img.shields.io/badge/TikTokApi-7.3.3-000000?logo=tiktok&logoColor=white)](https://github.com/davidteather/TikTok-Api)
[![NLTK](https://img.shields.io/badge/NLTK-3.9.4-004D8C?logo=python&logoColor=white)](https://www.nltk.org/)
[![matplotlib](https://img.shields.io/badge/matplotlib-3.11.0-11557C?logo=python&logoColor=white)](https://matplotlib.org/)
[![seaborn](https://img.shields.io/badge/seaborn-0.13.2-3B7BBF?logo=python&logoColor=white)](https://seaborn.pydata.org/)

[![Status](https://img.shields.io/badge/status-active--development-success)]()
[![Dataset](https://img.shields.io/badge/dataset-349K%20reviews-blueviolet)]()
[![Apps](https://img.shields.io/badge/fintech%20apps-44-orange)]()
[![DVC](https://img.shields.io/badge/data-DVC%2BGoogle%20Drive-yellow)](https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/addaan1/Final-Project-AKB)](https://github.com/addaan1/Final-Project-AKB)
[![Stars](https://img.shields.io/github/stars/addaan1/Final-Project-AKB?style=social)](https://github.com/addaan1/Final-Project-AKB)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](https://github.com/addaan1/Final-Project-AKB/pulls)

</div>

---

## 📖 Thesis

> *"Anak muda gagal bayar bukan karena tidak punya uang, tapi karena perilaku, gaya hidup, dan horizon berpikir pendek."*

Data tren hanya bertindak sebagai **termometer** (menunjukkan gejala). Galbay Predictor naik ke level **dokter**: mendiagnosis akar psikologis dari pola bahasa digital, lalu memberikan **obat** berupa peringatan pre-checkout, simulasi cicilan, dan edukasi keuangan yang tidak menggurui.

| Lapisan | Analogi | Output |
|---|---|---|
| 🌡️ **Termometer** | Google Trends, sentimen | Deteksi tren "galbay" naik |
| 🩺 **Dokter** | NLP pada review/komentar | Diagnosa pola: impulsif, avoidance, regret |
| 💊 **Obat** | Financial behavior coach | Peringatan pre-checkout, simulasi cicilan, edukasi |

---

## 📊 Dataset Saat Ini

| Metrik | Nilai |
|---|---|
| **Sumber data** | **Google Play Store** (single source) |
| **Total review** | 349.200 |
| **App fintech** | 44 (paylater, e-wallet, e-commerce, pinjol, P2P, bank digital, banking, investasi) |
| **Review relevan galbay** | 35.968 (10,30%) |
| **Keyword psikologis** | 65+ terkelompok dalam 7 kategori |
| **Format** | JSON raw → 4 CSV + SQLite DB (74 MB) |
| **Distribusi** | Google Drive (lihat `data/DOWNLOAD.md`) |

### Aplikasi yang di-scrape (44 app)

<details>
<summary><b>Semua kategori fintech (klik untuk detail)</b></summary>

| Kategori | App | Jumlah |
|---|---|---|
| **Paylater/BNPL** | Kredivo, Akulaku, Indodana | 3 |
| **E-commerce** | Shopee, Tokopedia, Lazada, Bukalapak | 4 |
| **Travel** | Traveloka, Tiket.com | 2 |
| **E-wallet** | Gojek, GoPay, OVO, DANA, LinkAja, Sakuku, ShopeePay, Flip | 8 |
| **Pinjol** | RupiahCepat, KreditPintar, Tunaiku, AdaKami (2), Easycash (2), BantuSaku, Singa, FinPlus, KrediOne, Home Credit, JULO, KTA Kilat, Indosaku, Cairin, UangMe | 16 |
| **P2P Lending** | KoinWorks | 1 |
| **Bank Digital** | SeaBank, neobank BNC, Bank Jago, blu by BCA | 4 |
| **Mobile Banking** | BRImo, Livin by Mandiri | 2 |
| **Koperasi** | Artha Niaga | 1 |
| **Kartu Kredit** | Honest | 1 |
| **Investasi** | Stockbit | 1 |

**Total: 44 app fintech Indonesia**

</details>

## 📦 Big Data di Google Drive

Dataset >100MB tidak bisa di GitHub. Kami pakai **DVC + Google Drive** untuk distribusi.

**Link Google Drive:** https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_

Lihat [`data/DOWNLOAD.md`](data/DOWNLOAD.md) untuk cara download via `dvc pull` atau manual.

### Keyword sinyal psikologis (65+ keyword)

| Kategori | Contoh keyword |
|---|---|
| `distress_langsung` | galbay, gagal bayar, nunggak, macet, telat bayar |
| `tagihan_dan_penagihan` | ditagih, tagihan, debt collector, dc, dicerewet, ditagih jam 12 |
| `bunga_dan_biaya` | bunga, denda, biaya admin, bunga tinggi |
| `produk_fintech` | paylater, pinjol, cicilan, kasbon, limit, tenor |
| `psikologi_impulsif` | self reward, checkout dulu, fomo, flash sale, gpp cicil |
| `psikologi_avoidance` | takut ditagih, kabur, ganti nomor, diblokir |
| `psikologi_regret_stress` | menyesal, insyaf, stress, depresi, susah tidur |

---

## 🗂️ Struktur Proyek

```
galbay-predictor/
├── app/                          # Flask web app
│   ├── __init__.py               # Application factory
│   ├── main.py                   # Blueprint utama (landing + dashboard)
│   ├── templates/                # base, index, dashboard
│   └── static/                   # CSS dark theme + JS
│
├── scraper/                      # Pipeline scraping big data
│   ├── __init__.py
│   ├── base.py                   # BaseScraper (rate-limit, save_json, metadata, .env)
│   ├── runner.py                 # CLI orchestrator
│   ├── fintech_reviews.py        # ⭐ Google Play reviews (44 app, 349K review)
│   ├── appstore_reviews.py       # ⭐ Apple App Store reviews iOS
│   ├── google_trends.py          # Tren keyword 12-bulan (pytrends)
│   ├── tiktok.py                 # Komentar TikTok #galbay (Playwright)
│   ├── twitter.py                # Post X/Twitter (Playwright, login-wall)
│   ├── instagram.py              # Caption/komentar IG (stub)
│   ├── forum.py                  # ⭐ Kaskus threads + Reddit (Playwright)
│   ├── ojk_news.py               # ⭐ OJK + 12 media besar
│   ├── blogs.py                  # ⭐ Blog posts (Medium + Dailysia)
│   └── youtube.py                # ⭐ YouTube comments (butuh API key)
│
├── processing/                   # Pre-processing & analisis data mentah
│   ├── __init__.py
│   ├── build_csv.py              # JSON → 3 CSV (relevant_only, per_app_summary, timeline)
│   ├── validate.py               # Deduplication & validation (in-memory)
│   ├── sentiment.py              # ⭐ VADER sentiment → reviews_with_sentiment.csv
│   ├── preprocess.py             # NLP preprocessing (in-memory)
│   ├── visualize.py              # matplotlib/seaborn charts
│   └── export_sqlite.py          # Export ke SQLite database
│
├── data/
│   ├── raw/                      # Data mentah (DVC + Google Drive, ~100 MB)
│   ├── processed/                # CSV, charts, SQLite (DVC + Google Drive, ~70 MB)
│   │   └── charts/               # Visualisasi PNG
│   ├── sample/                   # Sample kecil untuk reproducibility (di-commit)
│   │   └── play_reviews_sample.json
│   ├── raw.dvc                   # DVC tracking untuk raw/
│   ├── processed.dvc             # DVC tracking untuk processed/
│   ├── README.md                 # Skema & dokumentasi dataset
│   └── DOWNLOAD.md               # Panduan download dari Google Drive
│
├── docs/                         # Dokumen bisnis
│   ├── business_plan.md          # Business plan berbasis data
│   ├── financial_plan.md         # Perencanaan keuangan 3 tahun
│   └── data_strategy.md          # Strategi data & etika scraping
│
├── models/                       # Model ML (tim modeling)
├── notebooks/                    # Eksplorasi & visualisasi
├── tests/                        # Smoke test
├── run.py                        # Entry point Flask
├── config.py                     # Konfigurasi aplikasi
└── requirements.txt              # Dependency (Flask, pandas, scraper, Excel)
```

---

## 🚀 Quickstart

### Prasyarat
- Python 3.12
- Windows / Linux / macOS

### Instalasi

```powershell
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

### Jalankan Web App

```powershell
python run.py
# Buka http://localhost:5000
```

### Jalankan Scraping

```powershell
# Lihat semua source tersedia
python -m scraper.runner --list

# === Google Play Reviews ===
# Sample cepat (400 review/app, 24 app = ~9.600 review)
python -m scraper.runner --source play_reviews --mode sample --count 400

# Big data mode (semua review per app, cap 3000/app = 72.000 review)
python -m scraper.runner --source play_reviews --mode all --max-per-app 3000

# === Sumber lain ===
python -m scraper.runner --source google_trends        # Tren 12-bulan
python -m scraper.runner --source tiktok                # Komentar TikTok #galbay
python -m scraper.runner --source forum                 # Kaskus + Reddit
python -m scraper.runner --source twitter               # X/Twitter via Nitter
python -m scraper.runner --source ojk_news              # OJK + kompas/detik/cnbc

# Jalankan semua source
python -m scraper.runner --all
```

### Build CSV + Analisis

```powershell
# 1. Build 3 CSV (relevant_only, per_app_summary, timeline)
python -m processing.build_csv

# 2. Sentiment analysis (VADER) → reviews_with_sentiment.csv
python -m processing.sentiment

# 3. Visualisasi (charts PNG)
python -m processing.visualize

# 4. Export ke SQLite
python -m processing.export_sqlite
```

**Output CSV (4 file — sudah disederhanakan):**

| File | Rows | Size | Fungsi |
|---|---|---|---|
| `reviews_with_sentiment.csv` | 349.200 | 78 MB | **FILE UTAMA** — semua review + sentiment score |
| `relevant_only.csv` | 35.968 | 8 MB | **FILE KUNCI** — hanya review galbay relevan |
| `per_app_summary.csv` | 44 | <1 MB | Ringkasan statistik per app |
| `timeline.csv` | 50 | <1 MB | Tren review per bulan |

> **Yang dipakai untuk analisis:** `reviews_with_sentiment.csv` (semua data) atau `relevant_only.csv` (hanya yang relevan galbay).

---

## 👥 Tim — Kelompok 1 Analisis Keputusan Bisnis

| Nama | NIM | Role | Branch |
|---|---|---|---|
| Sahrul Adicandra Effendy | 164231013 | Big Data Engineer | `scraping` |
| Raihan Naufal Sauqi | 164231107 | Fullstack Engineer | `fullstack` |
| Aflah Zein Japamel | 164231085 | Modeling Engineer | `fullstack` |
| Muhammad Ilham Gustami | 164231089 | Fullstack Engineer | `fullstack` |
| Mohammad Faizal Aprilianto | 164231095 | Big Data Engineer | `scraping` |

---

## 🔀 Branch Policy

| Branch | Fungsi | Proteksi |
|---|---|---|
| `main` | Production-ready | ✅ Direct push diblokir, wajib PR, linear history, enforce admins |
| `fullstack` | Pengembangan aplikasi web (Flask) | - |
| `scraping` | Pipeline scraping & pre-processing big data | - |

**Alur kontribusi:** branch kerja → Pull Request → review → squash merge ke `main`.

```powershell
git checkout scraping
# buat perubahan, commit
git push origin scraping
gh pr create --base main --head scraping --title "..." --body "..."
gh pr merge --squash --delete-branch=false
```

---

## 🌐 Sumber Data

**Sumber utama: Google Play Store** — 349.200 review dari 44 aplikasi fintech Indonesia.

| # | Source | Volume | Status | Tools |
|---|---|---|---|---|
| 1 | **Google Play reviews** (44 app) | **349.200 review** | ✅ **Aktif (sumber utama)** | google-play-scraper |
| 2 | Google Trends | Time-series 12 bulan | ✅ Aktif (pelengkap) | pytrends |
| 3 | Forum Kaskus | 152 threads | ⚠️ Data tersedia, belum masuk CSV | Playwright |
| 4 | OJK + media | 163 artikel | ⚠️ Data tersedia, belum masuk CSV | BS4 + requests |
| 5 | Blog posts | 44 post | ⚠️ Data tersedia, belum masuk CSV | BS4 + requests |
| 6 | TikTok, Twitter, Reddit, YouTube | 0 | ❌ Blocked/login-wall/API key | - |
| 7 | Apple App Store | 0 | ❌ API return 0 review | app_store_scraper |

> **Catatan:** Dataset utama berasal dari **Google Play Store review** (single source). Data dari Kaskus, OJK, dan blog tersedia di `data/raw/` namun belum diintegrasikan ke CSV utama.

---

## 🔍 Insight Awal dari Data

- **Konsentrasi sinyal distress di pinjol/paylater:** KreditPintar, Akulaku, RupiahCepat, KoinWorks memiliki relevant_rate 10-17% vs e-commerce (Shopee/Tokopedia/Lazada) ~1%.
- **Beberapa pinjol kecil (AdaKami rebrand Adapundi, Easycash rebrand UATAS, UangMe rebrand Pinjam Yuk)** — indikasi penegakan OJK atau pivot bisnis.
- **Kategori `psikologi_regret_stress`** muncul konsisten: kata "stress", "susah tidur", "menyesal" — sinyal kesehatan mental akibat galbay.
- **Timeline** menunjukkan lonjakan review negatif seiring event regulasi OJK & viralitas TikTok "galbay".

---

## ⚖️ Etika & Governance

### Prinsip scraping
- ✅ Hanya ambil **data publik** (review app store, postingan publik).
- ✅ **Tidak simpan PII** (nama, no HP, email). `reviewId` & `userName` di-redact di tahap processed.
- ✅ **Rate-limit sopan** via `polite_sleep()`; hormati `robots.txt` & ToS platform.
- ✅ Dokumentasikan sumber & tanggal scrape di field `meta.scraped_at`.

### Paradoks etika (sorotan dosen)
> Data memberi kekuatan untuk (a) **memanfaatkan** psikologi pasar atau (b) **mengedukasi** ke arah benar.

**Pilihan Galbay Predictor:** data digunakan untuk **nudge edukasi & intervensi dini**, BUKAN untuk predatory targeting borrower rapuh.

- ❌ Eksploitasi: target user "takut ditagih" → iklan pinjol baru (memperburuk).
- ✅ Edukasi: deteksi pola "self reward 3x/minggu" → nudge pending checkout 24 jam + simulasi cicilan.

### Compliance
- **UU PDP (Perlindungan Data Pribadi):** anonimisasi sejak scraping.
- **OJK regulasi paylater:** ikuti sebagai sumber data, bukan sebagai lender.

---

## 📚 Dokumen Bisnis

- [`docs/business_plan.md`](docs/business_plan.md) — Business plan: thesis termometer-dokter-obat, model monetisasi B2B+B2C, roadmap.
- [`docs/financial_plan.md`](docs/financial_plan.md) — Unit economics (LTV/CAC), proyeksi 3 tahun, break-even.
- [`docs/data_strategy.md`](docs/data_strategy.md) — Sumber data, etika & governance, roadmap scraping.
- [`data/README.md`](data/README.md) — Skema dataset & dokumentasi teknis.

---

## 🗺️ Roadmap

| Fase | Waktu | Output |
|---|---|---|
| ✅ F1 — Data foundation | Minggu 1-3 | Pipeline scraping Google Play, 349K review, 4 CSV |
| ✅ F2 — Pre-processing | Minggu 3-4 | Validation, sentiment (VADER), charts, SQLite |
| ✅ F3 — Big data pipeline | Minggu 4-5 | DVC + Google Drive, 44 app fintech |
| 🔄 F4 — Insight & model | Minggu 5-6 | Risk score, NLP kategori psikologis |
| 🔲 F5 — MVP web | Minggu 6-8 | Flask dashboard + simulasi cicilan |
| 🔲 F6 — Pilot B2B | Minggu 8-12 | 1-2 kampus, 1 fintech |
| 🔲 F7 — Monetisasi | Bulan 4+ | Kontrak B2B pertama |

---

## 📝 Lisensi

MIT License — lihat [LICENSE](LICENSE).

Scraping dilakukan untuk keperluan akademik/analisis agregat. Data pribadi tidak disimpan; hanya teks, metadata agregat, dan timestamp.


