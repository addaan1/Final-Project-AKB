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
[![Dataset](https://img.shields.io/badge/dataset-72K%20reviews-blueviolet)]()
[![Apps](https://img.shields.io/badge/fintech%20apps-24-orange)]()
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
| **Total review** | 72.000 |
| **App fintech** | 24 (paylater, e-wallet, e-commerce, pinjol, P2P, banking, investasi) |
| **Review relevan galbay** | 5.825 (8,09%) |
| **Keyword psikologis** | 65+ terkelompok dalam 7 kategori |
| **Format** | JSON raw (36 MB) → 7 CSV terpisah |
| **Periode** | review historis per app |

### Aplikasi yang di-scrape

<details>
<summary><b>24 app fintech (klik untuk detail)</b></summary>

| Kategori | App |
|---|---|
| **Paylater/BNPL** | Kredivo, Akulaku, Indodana |
| **E-commerce** | Shopee, Tokopedia, Lazada, Bukalapak |
| **Travel** | Traveloka, Tiket.com |
| **E-wallet** | Gojek, GoPay, OVO, DANA, LinkAja, Sakuku |
| **Pinjol** | RupiahCepat, KreditPintar, Tunaiku, AdaKami, Easycash, UangMe |
| **P2P Lending** | KoinWorks |
| **Mobile Banking** | BRImo |
| **Investasi** | Stockbit |

</details>

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
│   ├── base.py                   # BaseScraper (rate-limit, save_json, metadata)
│   ├── runner.py                 # CLI orchestrator
│   ├── fintech_reviews.py        # ⭐ Google Play reviews (PRIORITAS 1)
│   ├── google_trends.py          # Tren keyword 12-bulan (pytrends)
│   ├── tiktok.py                 # ⭐ Komentar TikTok #galbay (TikTokApi)
│   ├── twitter.py                # ⭐ Post X/Twitter (Nitter instances)
│   ├── instagram.py              # Caption/komentar IG (stub)
│   ├── forum.py                  # ⭐ Kaskus threads + Reddit posts (BS4 + JSON)
│   └── ojk_news.py               # ⭐ OJK + kompas/detik/cnbc (BS4)
│
├── processing/                   # Pre-processing & analisis data mentah
│   ├── __init__.py
│   ├── build_csv.py              # ⭐ JSON → 7 CSV terpisah
│   ├── validate.py               # Deduplication & validation
│   ├── sentiment.py              # VADER sentiment analysis (NLTK)
│   ├── preprocess.py             # NLP preprocessing (slang, cleaning)
│   ├── visualize.py              # matplotlib/seaborn charts
│   └── export_sqlite.py          # Export ke SQLite database
│
├── data/
│   ├── raw/                      # Data mentah (gitignored, big data)
│   ├── processed/                # CSV, charts, SQLite (gitignored)
│   │   └── charts/               # Visualisasi PNG
│   ├── sample/                   # Sample kecil untuk reproducibility (di-commit)
│   │   └── play_reviews_sample.json
│   └── README.md                 # Skema & dokumentasi dataset
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
# Generate 7 CSV dari review JSON
python -m processing.build_csv

# Data validation & deduplication
python -m processing.validate

# Sentiment analysis (VADER)
python -m processing.sentiment

# NLP preprocessing (slang normalization, cleaning)
python -m processing.preprocess

# Visualisasi (charts PNG)
python -m processing.visualize

# Export ke SQLite
python -m processing.export_sqlite
```

**Output CSV (7 file):**

| File | Isi |
|---|---|
| `overview.csv` | Meta scrape: total, relevan, periode, kategori |
| `all_reviews.csv` | Semua review (app, score, content, tanggal, is_relevant) |
| `relevant_only.csv` | Review berisi keyword galbay (sinyal psikologis) |
| `per_app_summary.csv` | Statistik per app: n_reviews, relevant_rate, avg_score |
| `keyword_frequency.csv` | Frekuensi 65+ keyword per kategori (diagnosa psikologis) |
| `score_distribution.csv` | Cross-tab app × rating 1-5 |
| `timeline.csv` | Review per bulan per app (sinyal tren waktu) |

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

## 🌐 Sumber Data & Prioritas

| # | Source | Volume | Relevansi | Status | Tools |
|---|---|---|---|---|---|
| 1 | Google Play reviews fintech | Sangat tinggi | Tinggi | ✅ **Aktif** | google-play-scraper |
| 2 | TikTok komentar #galbay | Tinggi | Sangat tinggi (Gen Z) | ✅ **Aktif** | TikTokApi |
| 3 | Forum Kaskus + Reddit | Menengah-tinggi | Tinggi | ✅ **Aktif** | BS4 + public JSON |
| 4 | Twitter/X post | Tinggi | Tinggi | ✅ **Aktif** | Nitter instances |
| 5 | Google Trends | Rendah (time-series) | Tinggi (narasi) | ✅ **Aktif** | pytrends |
| 6 | OJK + media (kompas/detik/cnbc) | Rendah-menengah | Tinggi (regulator) | ✅ **Aktif** | BS4 + requests |

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
| ✅ F1 — Data foundation | Minggu 1-3 | Pipeline scraping jalan, 72K review, 7 CSV |
| ✅ F2 — Multi-source scraping | Minggu 3-4 | TikTok, Kaskus, Reddit, Twitter, OJK + media |
| ✅ F3 — Pre-processing | Minggu 4-5 | Validation, sentiment (VADER), NLP, charts, SQLite |
| 🔄 F4 — Insight & model | Minggu 5-6 | Risk score, NLP kategori psikologis |
| 🔲 F5 — MVP web | Minggu 6-8 | Flask dashboard + simulasi cicilan |
| 🔲 F6 — Pilot B2B | Minggu 8-12 | 1-2 kampus, 1 fintech |
| 🔲 F7 — Monetisasi | Bulan 4+ | Kontrak B2B pertama |

---

## 📝 Lisensi

MIT License — lihat [LICENSE](LICENSE).

Scraping dilakukan untuk keperluan akademik/analisis agregat. Data pribadi tidak disimpan; hanya teks, metadata agregat, dan timestamp.


