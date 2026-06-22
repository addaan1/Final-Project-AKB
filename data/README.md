# Panduan Paket Data

Folder ini berisi data mentah, output olahan, dan file tracking DVC yang dipakai proyek.

## Struktur folder

```text
data/
  raw/             output JSON mentah dari pipeline scraping
  processed/       tabel analisis, chart, dan paket SQLite
  sample/          sample kecil yang ikut tersimpan di repo
  raw.dvc          file tracking DVC untuk data mentah
  processed.dvc    file tracking DVC untuk data olahan
```

## Data mentah

Sumber mentah utama:

- `data/raw/play_reviews_all.json`

File mentah pendukung bisa mencakup:

- `forum_all.json`
- `news_all.json`
- `blogs_all.json`
- file JSON per aplikasi dari Google Play

## Data olahan

### File inti

| File | Keterangan |
|---|---|
| `all_reviews.csv` | dataset utama semua ulasan |
| `relevant_only.csv` | subset ulasan yang relevan dengan galbay |
| `per_app_summary.csv` | ringkasan statistik per aplikasi |
| `timeline.csv` | tren ulasan per bulan |

### File pendukung

| File | Keterangan |
|---|---|
| `validated_forum.csv` | referensi forum yang sudah divalidasi |
| `validated_news.csv` | referensi berita yang sudah divalidasi |
| `galbay.db` | versi SQLite dari paket analisis |
| `charts/` | grafik siap pakai |

### File lanjutan

Tabel turunan yang lebih berat disimpan di `data/processed/advanced/` supaya folder utama tetap ringkas dan mudah dibaca tim.

## Cakupan aplikasi

Data review utama dikumpulkan dari `44` aplikasi fintech Indonesia dalam kategori:

- `paylater`
- `ecommerce`
- `ewallet`
- `pinjol`
- `bank_digital`
- `mobile_banking`
- `p2p_lending`
- `investasi`
- `kartu_kredit`
- `koperasi`
- `travel`

Daftar aplikasinya diringkas di [README.md](../README.md).

## Cara mengambil dataset

Jalur utama pengambilan dataset adalah melalui DVC:

1. clone repository;
2. buat dan aktifkan virtual environment;
3. install dependency dengan `pip install -r requirements.txt`;
4. copy `.env.example` menjadi `.env`;
5. isi `GDRIVE_CLIENT_ID` dan `GDRIVE_CLIENT_SECRET`;
6. jalankan `python scripts/setup_dvc_gdrive.py`;
7. jalankan `python -m dvc pull`.

Detail langkahnya tersedia di [DOWNLOAD.md](DOWNLOAD.md).

## Rekomendasi cepat untuk anggota tim

Kalau hanya ingin langsung analisis, fokuskan dulu ke file berikut:

- `data/processed/all_reviews.csv`
- `data/processed/relevant_only.csv`
- `data/processed/per_app_summary.csv`
- `data/processed/timeline.csv`
