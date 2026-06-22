# Panduan Mengambil Dataset Besar

Dataset Galbay Predictor terlalu besar untuk disimpan langsung di GitHub. Karena itu, dataset dibagikan melalui **Google Drive tim**, sementara konfigurasi **DVC** tetap dipertahankan di repo untuk struktur proyek dan kemungkinan sinkronisasi otomatis di tahap berikutnya.

## Folder Google Drive tim

Folder utama tim:

`https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_`

## Alur yang dipakai tim saat ini

Untuk kondisi terbaru proyek, jalur yang paling disarankan adalah **manual download dari Google Drive**.

### 1. Clone repository

```powershell
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB
```

### 2. Install dependency

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Download dataset besar dari Google Drive

Setelah repository berhasil di-clone:

1. buka folder Google Drive tim;
2. download dataset versi terbaru yang sudah disinkronkan;
3. pastikan folder `raw/` dan `processed/` ikut terbawa;
4. pindahkan hasil download ke dalam folder `data/`.

Struktur akhirnya minimal seperti ini:

```text
Final-Project-AKB/
  data/
    raw/
    processed/
```

### 4. Cek file yang paling penting

File yang disarankan untuk langsung dipakai:

- `data/processed/all_reviews.csv`
- `data/processed/relevant_only.csv`
- `data/processed/per_app_summary.csv`
- `data/processed/timeline.csv`
- `data/processed/validated_forum.csv`
- `data/processed/validated_news.csv`

### 5. Jalankan aplikasi atau analisis

```powershell
python run.py
```

Atau langsung buka file CSV untuk eksplorasi data.

## Tentang DVC

Repository ini tetap menyimpan:

- `data/raw.dvc`
- `data/processed.dvc`

Artinya struktur proyek masih kompatibel dengan workflow DVC. Namun untuk update dataset terbaru saat ini, tim belum mengandalkan `dvc push` sebagai jalur utama karena akses remote Google Drive masih belum stabil dari sesi kerja ini.

## Jika nanti DVC sudah aktif lagi

Kalau remote DVC sudah aktif penuh, anggota tim bisa memakai alur berikut:

```powershell
copy .env.example .env
python scripts/setup_dvc_gdrive.py
python -m dvc pull
```

Pada alur ini:

- setiap anggota tim tetap harus punya akses ke folder Google Drive;
- `.dvc/config.local` bersifat lokal dan tidak boleh di-commit;
- `python scripts/setup_dvc_gdrive.py` akan menulis konfigurasi OAuth lokal untuk mesin masing-masing.

## Ringkasan singkat untuk teman satu tim

Kalau tujuan temanmu hanya ingin cepat dapat dataset besar:

1. clone repo GitHub;
2. install dependency;
3. download dataset besar dari folder Google Drive tim;
4. taruh ke `data/raw/` dan `data/processed/`;
5. mulai analisis dari `all_reviews.csv` dan `relevant_only.csv`.
