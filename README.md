<div align="center">

![Galbay Predictor Banner](docs/assets/galbay-readme-hero.svg)

# Galbay Predictor

### Membaca sinyal financial distress dari ulasan fintech Indonesia

Repositori ini berisi pipeline scraping, paket dataset terkurasi, ringkasan visual, dan aplikasi web ringan untuk final project mata kuliah Analisis Keputusan Bisnis.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-111111?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Distribusi Data](https://img.shields.io/badge/Data-DVC%20%2B%20Google%20Drive-C9A227)](data/DOWNLOAD.md)
[![Ulasan](https://img.shields.io/badge/Google%20Play%20reviews-349K-1F5EFF)]()
[![Aplikasi](https://img.shields.io/badge/Fintech%20apps-44-0A7C66)]()
[![Lisensi](https://img.shields.io/badge/License-MIT-2E8B57)](LICENSE)

</div>

## Ringkasan

Galbay Predictor mempelajari bagaimana tanda-tanda gagal bayar, penyesalan finansial, impulsive spending, dan kecemasan penagihan muncul di ulasan publik aplikasi fintech. Sumber utama proyek ini adalah ulasan Google Play Store dalam skala besar, lalu diproses menjadi tabel analisis yang lebih rapi dan mudah dipakai tim.

Repositori ini disusun untuk dua kebutuhan:

- anggota tim yang perlu mengambil dataset besar dengan alur yang jelas;
- reviewer yang ingin cepat memahami ruang lingkup, hasil data, dan nilai analisis proyek.

## Gambaran Dataset

| Komponen | Nilai |
|---|---|
| Sumber utama | Ulasan Google Play Store |
| Cakupan | 44 aplikasi fintech Indonesia |
| Total ulasan | 349.200 |
| Ulasan relevan galbay | 35.968 |
| Konteks pendukung | tabel validasi forum dan berita |
| Distribusi data | DVC + Google Drive |

## Rincian Sumber Data

### Sumber utama

Dataset utama berasal dari review Google Play Store untuk `44` aplikasi fintech Indonesia.

### Kategori aplikasi yang dicakup

| Kategori | Aplikasi |
|---|---|
| `paylater` | Kredivo, Indodana, Akulaku |
| `ecommerce` | Shopee, Tokopedia, Lazada, Bukalapak |
| `ewallet` | DANA, Flip, GoPay, Gojek, LinkAja, OVO, Sakuku, ShopeePay |
| `pinjol` | AdaKami, Adapundi, BantuSaku, Cairin, Easycash, FinPlus, Home Credit, Indosaku, JULO, KTA Kilat, KrediOne, Kredit Pintar, Pinjam Yuk, RupiahCepat, Singa Fintech, Tunaiku, UATAS |
| `bank_digital` | Bank Jago, SeaBank, blu by BCA Digital, neobank dari BNC Digital |
| `mobile_banking` | BRImo, Livin' by Mandiri |
| `p2p_lending` | KoinWorks |
| `investasi` | Stockbit |
| `kartu_kredit` | Honest |
| `koperasi` | Artha Niaga |
| `travel` | Traveloka, tiket.com |

### Sumber pendukung

Selain review aplikasi, proyek ini juga memakai konteks tambahan yang sudah divalidasi:

- `validated_forum.csv` untuk referensi diskusi forum;
- `validated_news.csv` untuk referensi berita dan konteks regulator.

## Lokasi dan File Data

### Folder utama data

| Lokasi | Isi |
|---|---|
| `data/raw/` | data mentah hasil scraping |
| `data/processed/` | data olahan utama untuk analisis |
| `data/processed/advanced/` | file turunan yang lebih berat |
| `data/sample/` | sample kecil yang ikut tersimpan di repo |

### File utama untuk analisis

Folder `data/processed/` sengaja dirapikan agar anggota tim langsung tahu file mana yang paling penting.

| File | Fungsi |
|---|---|
| `all_reviews.csv` | tabel utama semua ulasan |
| `relevant_only.csv` | subset ulasan yang terindikasi berkaitan dengan galbay |
| `per_app_summary.csv` | ringkasan per aplikasi untuk perbandingan |
| `timeline.csv` | tren ulasan per bulan |
| `validated_forum.csv` | konteks diskusi forum yang sudah divalidasi |
| `validated_news.csv` | konteks berita dan regulator yang sudah divalidasi |
| `galbay.db` | paket SQLite untuk query atau dashboard |
| `charts/` | grafik siap pakai untuk laporan dan presentasi |

## Preview

| Tren Ulasan | Distribusi Kata Kunci |
|---|---|
| ![Timeline](data/processed/charts/timeline_monthly.png) | ![Keywords](data/processed/charts/top_keywords.png) |

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
python -m dvc pull
```

Atau kalau command `dvc` sudah ada di `PATH`:

```powershell
dvc pull
```

Yang akan dipulihkan otomatis:

- `data/raw/`
- `data/processed/`

### 6. Jalankan aplikasi

```powershell
python run.py
```

Lalu buka `http://localhost:5000`.

## Alur Dataset untuk Teman Satu Tim

Kalau temanmu ingin mulai dari nol sampai bisa ikut analisis, alurnya seperti ini:

1. clone repo dari GitHub;
2. buat lalu aktifkan virtual environment;
3. jalankan `pip install -r requirements.txt`;
4. isi `.env` dengan `GDRIVE_CLIENT_ID` dan `GDRIVE_CLIENT_SECRET`;
5. jalankan `python scripts/setup_dvc_gdrive.py`;
6. jalankan `python -m dvc pull`;
7. cek file utama di `data/processed/` lalu mulai analisis.

File yang paling direkomendasikan untuk langsung dipakai:

- `data/processed/all_reviews.csv`
- `data/processed/relevant_only.csv`
- `data/processed/per_app_summary.csv`
- `data/processed/timeline.csv`
- `data/processed/validated_forum.csv`
- `data/processed/validated_news.csv`

## Catatan tentang DVC

Konfigurasi DVC adalah jalur utama untuk mengambil dataset besar tim. Folder Google Drive tetap dipakai sebagai remote storage di belakang DVC, tetapi anggota tim seharusnya tidak perlu mengunduh dataset secara manual bila setup DVC sudah benar.

Urutan yang dipakai tim adalah:

```powershell
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python scripts/setup_dvc_gdrive.py
python -m dvc pull
```

Pada alur ini:

- setiap anggota tim tetap harus punya akses ke folder Google Drive;
- `.dvc/config.local` bersifat lokal dan tidak boleh di-commit;
- `python scripts/setup_dvc_gdrive.py` akan menulis konfigurasi OAuth lokal untuk mesin masing-masing;
- `dvc pull` pertama biasanya akan membuka login atau consent Google di browser.

## Fallback Manual

Kalau suatu saat `dvc pull` sedang bermasalah karena auth atau remote, barulah Google Drive bisa dipakai sebagai fallback manual. Detail fallback tetap disimpan di [data/DOWNLOAD.md](data/DOWNLOAD.md), tetapi itu bukan jalur utama yang direkomendasikan.

## Struktur Project

```text
app/             aplikasi Flask
scraper/         pipeline pengumpulan data
processing/      pembentukan CSV, sentiment, chart, dan SQLite
data/raw/        data mentah
data/processed/  output analisis terkurasi
docs/            dokumen pendukung bisnis dan presentasi
tests/           smoke test dan unit test
```

## Alur Kolaborasi

| Branch | Fungsi |
|---|---|
| `main` | branch utama yang stabil dan siap dipresentasikan |
| `scraping` | branch untuk pengolahan data, scraping, dan dataset |
| `fullstack` | branch untuk pengembangan aplikasi web |

Alur kerja yang disarankan:

1. kerjakan perubahan di branch yang sesuai;
2. sinkronkan branch dengan `main` sebelum lanjut kerja besar;
3. validasi hasil secara lokal;
4. push branch ke GitHub;
5. buka pull request ke `main`;
6. merge setelah perubahan siap.

## Tim

| Nama | NIM | Peran |
|---|---|---|
| Sahrul Adicandra Effendy | 164231013 | Big Data Engineer |
| Raihan Naufal Sauqi | 164231107 | Fullstack Engineer |
| Aflah Zein Japamel | 164231085 | Modeling Engineer |
| Muhammad Ilham Gustami | 164231089 | Fullstack Engineer |
| Mohammad Faizal Aprilianto | 164231095 | Big Data Engineer |

## Referensi Tambahan

- [data/README.md](data/README.md) untuk struktur dan isi paket data
- [data/DOWNLOAD.md](data/DOWNLOAD.md) untuk panduan mengambil dataset besar
- [docs/business_plan.md](docs/business_plan.md) untuk konteks bisnis proyek

## Lisensi

MIT License. Lihat [LICENSE](LICENSE).
