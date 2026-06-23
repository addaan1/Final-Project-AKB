<div align="center">

![Galbay Predictor Banner](docs/assets/galbay-readme-hero.svg)

# Galbay Predictor

### Financial Behavior Coach berbasis Big Data untuk Gen Z Indonesia

Repositori ini berisi pipeline scraping, paket dataset terkurasi, ringkasan visual, dan aplikasi web Flask interaktif untuk final project mata kuliah Analisis Keputusan Bisnis.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-111111?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Tests](https://img.shields.io/badge/Tests-310%20passed-2E8B57)](tests/)
[![Ulasan](https://img.shields.io/badge/Google%20Play%20reviews-349K-1F5EFF)]()
[![Aplikasi](https://img.shields.io/badge/Fintech%20apps-44-0A7C66)]()
[![Chatbot](https://img.shields.io/badge/Chatbot%20v2-38%20intents-9b5de5)]()
[![Distribusi Data](https://img.shields.io/badge/Data-DVC%20%2B%20Google%20Drive-C9A227)](data/DOWNLOAD.md)

</div>

## Ringkasan

**Galbay Predictor** adalah *financial behavior coach* pertama di Indonesia yang dibangun dari data nyata — **349.200 ulasan** Google Play Store dari **44 aplikasi fintech** yang dipakai Gen Z. Tujuannya: membaca sinyal financial distress (gagal bayar, impulsive spending, debt collector) dari pola bahasa dan emosi di review publik, lalu menerjemahkannya menjadi tools bantu keputusan yang bisa dipakai siapa saja.

Repositori ini disusun untuk dua kebutuhan:

- anggota tim yang perlu mengambil dataset besar dengan alur yang jelas;
- reviewer yang ingin cepat memahami ruang lingkup, hasil data, dan nilai analisis proyek.

## Highlights

- **349.200 review Google Play** dari 44 aplikasi fintech Indonesia (paylater, pinjol, e-wallet, bank digital, dll)
- **35.968 review relevan** (10.3% dari total) — teridentifikasi mengandung sinyal galbay
- **11 kategori distress**: gagal bayar, DC agresif, bunga tinggi, dc sebar data, dll
- **Confusion matrix** untuk validasi pipeline NLP (precision, recall, F1)
- **3 game-changer tools** interaktif di dashboard:
  - **Pinjol Blacklist Checker** — cek legal/ilegal dari 50+ app database OJK
  - **Debt Snowball/Avalanche Planner** — simulasi multi-utang dengan timeline lunas
  - **Recovery Roadmap 30/60/90** — personal keluar dari galbay berdasarkan severity
- **Galbay AI Coach** — chatbot NLP-like dengan 38 intents, 8 modul, sinonim, typo tolerance, multi-bahasa (Indonesia), sentiment detection, crisis helpline
- **Auth + Premium tier** — Google OAuth + demo login, premium unlock AI Coach unlimited
- **Dual theme** — vibrant purple (dark default) + warm light, premium gold atmosphere

## Demo

```powershell
# 1. Install
pip install -r requirements.txt

# 2. Set up environment
copy .env.example .env
# Fill in GDRIVE_CLIENT_ID + GDRIVE_CLIENT_SECRET

# 3. Pull dataset (~180MB)
python scripts/setup_dvc_gdrive.py
dvc pull

# 4. Run
python run.py
# → http://localhost:5000
```

**Demo login** (no setup needed):
- `demo@galbay.id` / `demo123` — Free tier
- `premium@galbay.id` / `demo123` — Premium tier (all features unlocked)

## Tech Stack

| Layer | Tools |
|---|---|
| **Backend** | Flask 3.0, Python 3.12, Blueprint multi-page |
| **Frontend** | Vanilla JS, Chart.js, dual-theme CSS variables (vibrant purple) |
| **Auth** | Hybrid Google OAuth (authlib) + demo login + JSON storage |
| **Data** | Pandas, NumPy, scikit-learn, DVC + Google Drive |
| **Scraping** | BeautifulSoup, Playwright (Kaskus SPA), requests |
| **NLP** | Rule-based FAQ matcher (38 intents, 8 modul), synonym resolution, difflib typo tolerance |
| **Testing** | pytest, 310 tests passing |

## Gambaran Dataset

| Komponen | Nilai |
|---|---|
| Sumber utama | Ulasan Google Play Store |
| Cakupan | 44 aplikasi fintech Indonesia |
| Total ulasan | 349.200 |
| Ulasan relevan galbay | 35.968 (10.3%) |
| Kategori distress | 11 (gagal bayar, DC, bunga, dll) |
| Periode | 2022-05 s/d 2026-06 |
| Distribusi | DVC + Google Drive (~180MB) |

## Rincian Sumber Data

### Sumber utama
Dataset utama berasal dari review Google Play Store untuk `44` aplikasi fintech Indonesia.

### Kategori aplikasi yang dicakup

| Kategori | Aplikasi |
|---|---|
| `paylater` | Kredivo, Indodana, Akulaku, Atome, Kredito |
| `ecommerce` | Shopee, Tokopedia, Lazada, Bukalapak |
| `ewallet` | DANA, Flip, GoPay, Gojek, LinkAja, OVO, Sakuku, ShopeePay |
| `pinjol` | AdaKami, Adapundi, BantuSaku, Cairin, Easycash, FinPlus, Home Credit, Indosaku, JULO, KTA Kilat, KrediOne, Kredit Pintar, Pinjam Yuk, RupiahCepat, Singa Fintech, Tunaiku, UATAS, DanaCepat |
| `bank_digital` | Bank Jago, SeaBank, blu by BCA Digital, Jenius, Allo Bank, LINE Bank |
| `mobile_banking` | BRImo, Livin' by Mandiri, BCA Mobile |
| `p2p_lending` | KoinWorks, Amartha, Investree, Modalku, TaniFund |
| `investasi` | Bibit, Ajaib, Stockbit, Pluang |
| `aggregator` | Cermati, Lifepal, Roojai |
| `kartu_kredit` | Honest |
| `koperasi` | Artha Niaga |

### Sumber pendukung
- `validated_forum.csv` — referensi diskusi forum
- `validated_news.csv` — referensi berita dan konteks regulator

## Lokasi dan File Data

| Lokasi | Isi |
|---|---|
| `data/raw/` | data mentah hasil scraping (45 file JSON per app) |
| `data/processed/` | data olahan utama untuk analisis |
| `data/sample/` | sample kecil yang ikut tersimpan di repo |
| `data/pinjol_database.json` | database 50+ app pinjol legal + ilegal |

### File utama untuk analisis

| File | Fungsi |
|---|---|
| `all_reviews.csv` | tabel utama semua ulasan (349K baris) |
| `relevant_only.csv` | subset ulasan terindikasi galbay (36K baris) |
| `per_app_summary.csv` | ringkasan per aplikasi untuk perbandingan |
| `timeline.csv` | tren ulasan per bulan |
| `validated_forum.csv` | konteks diskusi forum yang sudah divalidasi |
| `validated_news.csv` | konteks berita dan regulator |
| `galbay.db` | paket SQLite untuk query atau dashboard |
| `charts/` | grafik siap pakai (timeline, keywords, confusion matrix) |

## Arsitektur Aplikasi Web

```
app/
├── __init__.py        # Flask app factory
├── main.py            # 5 dashboard routes + 9 API endpoints
├── api.py             # Skor Risiko, Simulasi Cicilan, Pinjol Checker,
│                      # Debt Planner, Recovery Roadmap, Chatbot v2
├── auth.py            # User model + Google OAuth + demo login + decorators
├── templates/
│   ├── index.html              # Landing page
│   ├── login.html              # 2-column login (Masuk/Daftar tabs)
│   ├── dashboard/
│   │   ├── base.html           # Topbar + chatbot widget
│   │   ├── ringkasan.html      # Executive summary + KPI
│   │   ├── analisis.html       # Confusion matrix + sentiment
│   │   ├── solusi.html         # 4 modul coaching
│   │   ├── kesimpulan.html     # Key findings
│   │   └── produk.html         # 3 game-changers + pricing
│   ├── privacy.html
│   └── terms.html
└── static/
    ├── css/style.css           # Dual theme (purple light/dark, gold premium)
    ├── js/
    │   ├── main.js             # Chart init + data fill
    │   ├── produk.js           # Skor Risiko + Pinjol + Planner + Roadmap
    │   ├── chatbot.js          # Intercom-style AI Coach widget
    │   ├── data.js             # 349K review data
    │   └── theme.js            # Dark/light toggle
    └── img/                    # Logo + favicon
```

## API Endpoints

| Endpoint | Method | Fungsi |
|---|---|---|
| `/api/health` | GET | health check |
| `/api/score` | POST | hitung Skor Risiko Galbay (rule-based) |
| `/api/simulate` | POST | simulasi cicilan dengan bunga flat |
| `/api/check-pinjol` | POST | cek status legal/ilegal pinjol |
| `/api/debt-planner` | POST | snowball vs avalanche + timeline |
| `/api/recovery-roadmap` | POST | generate 30/60/90 hari plan |
| `/api/chat` | POST | Galbay AI Coach (FAQ NLP v2) |
| `/api/waitlist` | POST | daftar waitlist premium |

Lihat [docs/API.md](docs/API.md) untuk dokumentasi lengkap.

## Galbay AI Coach v2 (Chatbot)

**Phase 2 NLP-like** dengan 38 intents across 8 modul:

| Module | Topik | Intents |
|---|---|---|
| M1 Galbay Basics | Pengertian galbay, skor, simulasi | 3 |
| M2 Pinjol | Legal/ilegal, OJK, bunga wajar | 4 |
| M3 Debt Strategy | Snowball, Avalanche, negosiasi | 4 |
| M4 DC Negotiation | DC agresif, template, lapor | 4 |
| M5 Recovery | 30/60/90 hari, telat 7/30 hari | 4 |
| M6 Legal Rights | UU PDP, ITE, OJK, SLIK | 4 |
| M7 App Recommendation | Galbay aman, premium, data | 6 |
| M8 Mental Health | Stress, krisis, konseling | 3 |
| + default | fallback | 1 |

**Smart features**:
- 🔤 **Synonym resolution** — "pinjol" matches "pinjaman online", "online", "p2p"
- 🔍 **Typo tolerance** — "snowbol" → snowball via difflib
- 🎯 **Multi-intent** — returns top 3 secondary intents for follow-up
- 💚 **Sentiment detection** — curious/stressed/crisis/grateful/positive
- ⏰ **Time-based greeting** — pagi/siang/sore/malam
- 📍 **Context-aware** — page-specific tips (ringkasan/produk/solusi)
- 🆘 **Crisis helpline** — auto-suggest Sejiwa 119 ext 8 untuk self-harm

## Premium Tier

| Fitur | Free | Premium |
|---|---|---|
| Skor Risiko, Simulasi, Pinjol Checker | ✅ | ✅ + alerts |
| Recovery Roadmap | Preview | Full + save |
| Debt Planner | ❌ | ✅ unlimited |
| Galbay AI Coach | 5 pesan | ✅ unlimited |
| Save history | 3 | ✅ unlimited |
| Export PDF | ❌ | ✅ |
| Laporan Bulanan | ❌ | ✅ |

**Pricing**: Rp 49rb/bln atau Rp 399rb/tahun (diskon 50% tahun pertama).

## Cara Mengambil Project dan Dataset

### 1. Clone repository
```powershell
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB
```

### 2. Buat dan aktifkan virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependency
```powershell
pip install -r requirements.txt
```

### 4. Siapkan konfigurasi DVC Google Drive
```powershell
copy .env.example .env
```

Isi minimal field berikut di `.env`:
```env
GDRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your-client-secret
```

Lalu jalankan:
```powershell
python scripts/setup_dvc_gdrive.py
```

### 5. Ambil dataset besar dengan DVC
```powershell
dvc pull
```

Yang akan dipulihkan otomatis: `data/raw/`, `data/processed/`.

### 6. Jalankan aplikasi
```powershell
python run.py
```

Buka `http://localhost:5000`.

## Testing

```powershell
# Run all tests
pytest tests/

# Run specific file
pytest tests/test_chatbot.py -v
```

**310 tests** passing:
- `test_api.py` — API logic (scoring, simulasi, pinjol, debt planner, recovery)
- `test_auth.py` — User model, OAuth, login, upgrade
- `test_chatbot.py` — FAQ NLP v2 (synonyms, typos, multi-intent, sentiment, crisis)
- `test_game_changers.py` — Pinjol Checker, Debt Planner, Recovery Roadmap
- `test_routes.py` — Dashboard routes + auth integration
- `test_produk.py`, `test_simulasi.py`, `test_smoke.py` — integration tests

## Struktur Project

```text
app/             aplikasi Flask (main.py, api.py, auth.py)
scraper/         pipeline pengumpulan data
processing/      pembentukan CSV, sentiment, chart, dan SQLite
data/raw/        data mentah (45 file JSON per app)
data/processed/  output analisis terkurasi (4 CSV utama)
docs/            dokumen pendukung + API docs
tests/           310 unit & integration tests
assets/          chart PNGs untuk laporan
```

## Alur Kolaborasi

| Branch | Fungsi |
|---|---|
| `main` | branch utama yang stabil dan siap dipresentasikan |
| `scraping` | branch untuk pengolahan data, scraping, dan dataset |
| `fullstack` | branch untuk pengembangan aplikasi web + UI/UX |

Alur kerja yang disarankan:
1. kerjakan perubahan di branch yang sesuai;
2. sinkronkan branch dengan `main` sebelum lanjut kerja besar;
3. validasi hasil secara lokal (`pytest tests/`);
4. push branch ke GitHub;
5. buka pull request ke `main`;
6. merge setelah perubahan siap.

## Catatan tentang DVC

Konfigurasi DVC adalah jalur utama untuk mengambil dataset besar tim. Folder Google Drive tetap dipakai sebagai remote storage di belakang DVC, tetapi anggota tim seharusnya tidak perlu mengunduh dataset secara manual bila setup DVC sudah benar.

Pada alur ini:
- setiap anggota tim tetap harus punya akses ke folder Google Drive;
- `.dvc/config.local` bersifat lokal dan tidak boleh di-commit;
- `python scripts/setup_dvc_gdrive.py` akan menulis konfigurasi OAuth lokal untuk mesin masing-masing;
- `dvc pull` pertama biasanya akan membuka login atau consent Google di browser.

## Demo Login (Tanpa Setup)

Untuk coba aplikasi **tanpa setup DVC/OAuth**, pakai akun demo:
- `demo@galbay.id` / `demo123` — Free tier
- `premium@galbay.id` / `demo123` — Premium tier (semua fitur terbuka)

## Tim

| Nama | NIM | Peran |
|---|---|---|
| Sahrul Adicandra Effendy | 164231013 | Big Data Engineer |
| Raihan Naufal Sauqi | 164231107 | Fullstack Engineer |
| Aflah Zein Japamel | 164231085 | Modeling Engineer |
| Muhammad Ilham Gustami | 164231089 | Fullstack Engineer |
| Mohammad Faizal Aprilianto | 164231095 | Big Data Engineer |

## Referensi Tambahan

- [data/README.md](data/README.md) — struktur dan isi paket data
- [data/DOWNLOAD.md](data/DOWNLOAD.md) — panduan mengambil dataset besar
- [docs/API.md](docs/API.md) — dokumentasi API endpoints
- [docs/business_plan.md](docs/business_plan.md) — konteks bisnis proyek

## Lisensi

MIT License. Lihat [LICENSE](LICENSE).

---

<div align="center">

**Galbay Predictor** — *Membaca sinyal financial distress dari 349.200 ulasan fintech Indonesia.*

🟣 **Vibrant Purple Theme** · 🤖 **AI Coach v2** · 📊 **3 Game-Changer Tools** · 🔐 **Auth + Premium**

</div>
