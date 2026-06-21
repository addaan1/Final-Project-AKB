# Galbay Predictor

> Membaca psikologi gagal bayar anak muda dari jejak digital.

**Galbay Predictor** bukan sistem pinjaman, melainkan sebuah *financial behavior coach* berbasis big data yang membaca pola bahasa dan perilaku digital Gen Z terkait gagal bayar ("galbay"), paylater, pinjol, dan konsumsi impulsif.

## Thesis Proyek

> *"Anak muda gagal bayar bukan karena tidak punya uang, tapi karena perilaku, gaya hidup, dan horizon berpikir pendek."*

Data tren hanya bertindak sebagai **termometer** (menunjukkan gejala). Galbay Predictor naik ke level **dokter**: mendiagnosis akar psikologis dari pola bahasa digital, lalu memberikan **obat** berupa peringatan pre-checkout, simulasi cicilan, dan edukasi keuangan yang tidak menggurui.

## Arsitektur Branch

| Branch | Fungsi | Proteksi |
|---|---|---|
| `main` | Production-ready | Direct push diblokir; wajib PR + linear history |
| `fullstack` | Pengembangan aplikasi web (Flask) | - |
| `scraping` | Pipeline scraping big data | - |

Alur kontribusi: branch kerja → Pull Request → review/merge ke `main`.

## Struktur Proyek

```
.
├── app/                  # Flask web app
├── scraper/              # Modul scraping big data
│   ├── google_trends.py
│   ├── fintech_reviews.py
│   ├── tiktok.py
│   ├── twitter.py
│   ├── instagram.py
│   ├── forum.py
│   ├── ojk_news.py
│   └── runner.py
├── data/
│   ├── raw/              # Data mentah (gitignored, big data)
│   ├── processed/        # Data bersih (gitignored)
│   └── sample/           # Sample kecil untuk reproducibility
├── docs/
│   ├── business_plan.md
│   ├── financial_plan.md
│   └── data_strategy.md
├── models/               # Model ML
├── notebooks/            # Eksplorasi
├── tests/
├── run.py
├── config.py
└── requirements.txt
```

## Tim

| Peran | Tanggung jawab | Branch |
|---|---|---|
| Scraping | Akuisisi big data multi-platform | `scraping` |
| Fullstack | Aplikasi web & dashboard | `fullstack` |
| Modeling | Klasifikasi risiko & NLP | `fullstack` |

## Quickstart

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

## Quickstart Scraping

```powershell
.\.venv\Scripts\Activate.ps1
python -m scraper.runner --source play_reviews
python -m scraper.runner --source google_trends
```

## Lisensi & Etika

Scraping dilakukan untuk keperluan akademik/analisis agregat. Data pribadi tidak disimpan; hanya teks, metadata agregat, dan timestamp. Lihat `docs/data_strategy.md`.
