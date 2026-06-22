# Panduan Mengambil Dataset Besar

Dataset Galbay Predictor terlalu besar untuk disimpan langsung di GitHub. Karena itu, dataset dibagikan melalui **DVC** dengan remote **Google Drive tim**.

## Folder Google Drive tim

Folder utama tim:

`https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_`

## Alur utama yang dipakai tim

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

### 4. Siapkan `.env`

```powershell
copy .env.example .env
```

Isi minimal:

```env
GDRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your-client-secret
```

### 5. Tulis konfigurasi lokal DVC

```powershell
python scripts/setup_dvc_gdrive.py
```

### 6. Pull dataset besar

```powershell
python -m dvc pull
```

Atau:

```powershell
dvc pull
```

Pada pull pertama:

- browser biasanya akan membuka login atau consent Google;
- login dengan akun yang sudah diberi akses ke folder Drive tim;
- setelah berhasil, `data/raw/` dan `data/processed/` akan dipulihkan otomatis.

## Output yang akan didapat

- `data/raw/`
- `data/processed/`

### File yang paling penting untuk analisis

- `data/processed/all_reviews.csv`
- `data/processed/relevant_only.csv`
- `data/processed/per_app_summary.csv`
- `data/processed/timeline.csv`
- `data/processed/validated_forum.csv`
- `data/processed/validated_news.csv`

## Tentang file DVC

Repository ini menyimpan:

- `data/raw.dvc`
- `data/processed.dvc`

Itu artinya dataset besar diambil lewat DVC, bukan disimpan langsung di GitHub.

## Catatan penting

- setiap anggota tim harus punya akses ke folder Google Drive tim;
- `.dvc/config.local` bersifat lokal dan tidak boleh di-commit;
- `python scripts/setup_dvc_gdrive.py` akan menulis konfigurasi OAuth lokal untuk mesin masing-masing;
- kalau `dvc pull` tidak meminta login, biasanya token login sudah tersimpan di mesin itu.

## Ringkasan singkat untuk teman satu tim

Kalau tujuan temanmu hanya ingin cepat dapat dataset besar, urutannya adalah:

1. clone repo GitHub;
2. aktifkan venv;
3. install dependency;
4. isi `.env`;
5. jalankan `python scripts/setup_dvc_gdrive.py`;
6. jalankan `python -m dvc pull`;
7. mulai analisis dari `all_reviews.csv` dan `relevant_only.csv`.

## Fallback manual

Kalau DVC sedang bermasalah karena auth atau remote, folder Google Drive tim bisa dipakai sebagai fallback manual. Namun ini hanya cadangan, bukan alur utama.
