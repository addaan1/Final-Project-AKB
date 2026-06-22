# Download Big Data (DVC + Google Drive)

Dataset Galbay Predictor terlalu besar untuk GitHub (>100MB). Distribusi utama
dataset dilakukan lewat **DVC** dengan remote **Google Drive**.

## Link folder Drive

**Folder share tim:** https://drive.google.com/drive/folders/1Rgs0cgz70h0gMXjMTHjNjhFwjMHdI4T_

Catatan:

- Folder share di atas adalah pintu masuk manusia untuk tim.
- Cache object DVC disimpan di subfolder khusus `dvc-cache` di dalam folder tersebut.
- DVC **tidak** mengandalkan akses "anyone with the link". Setiap teammate harus
  dishare langsung ke akun Google masing-masing.

## Cara utama: `dvc pull`

### 1. Clone repo dan install dependency

```powershell
git clone https://github.com/addaan1/Final-Project-AKB.git
cd Final-Project-AKB
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Siapkan OAuth client Google Drive

1. Buka `https://console.cloud.google.com`.
2. Buat atau pilih project Google Cloud.
3. Enable **Google Drive API**.
4. Buat **OAuth 2.0 Client ID** dengan tipe **Desktop app**.
5. Copy `client_id` dan `client_secret` ke `.env`.

```powershell
copy .env.example .env
```

Isi minimal dua field ini di `.env`:

```env
GDRIVE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=your-client-secret
```

### 3. Tulis config lokal DVC

```powershell
python scripts/setup_dvc_gdrive.py
```

Script ini akan:

- membaca `GDRIVE_CLIENT_ID` dan `GDRIVE_CLIENT_SECRET` dari `.env`,
- menyimpan nilainya ke `.dvc/config.local`,
- menjaga secret tetap lokal dan tidak ikut ke Git.

### 4. Pull dataset

```powershell
dvc pull
```

Saat `dvc pull` pertama:

- browser akan membuka Google consent screen,
- login pakai akun Google yang **sudah di-share** ke folder Drive project,
- approve akses, lalu kembali ke terminal.

Jika consent ditutup atau ditolak, DVC akan gagal dengan error auth rejected.
Jalankan `dvc pull` lagi dan selesaikan login.

## Output yang akan dipulihkan

- `data/raw/`
- `data/processed/`

Tracked output tetap memakai:

- `data/raw.dvc`
- `data/processed.dvc`

## Fallback manual

Gunakan ini hanya kalau setup OAuth benar-benar belum siap.

1. Buka folder Drive di atas.
2. Download isi `raw/` dan `processed/`.
3. Letakkan hasil download ke:

```text
Final-Project-AKB/
└── data/
    ├── raw/
    └── processed/
```

Fallback manual tidak menggantikan workflow DVC dan tidak memverifikasi versi
cache object yang dipakai repo.

## Troubleshooting singkat

- `dvc` tidak dikenali:
  aktifkan virtualenv lalu jalankan `pip install -r requirements.txt`.
- Browser terbuka tapi gagal login:
  pastikan akun Google yang dipakai sudah dishare ke folder Drive project.
- Muncul `Authentication request was rejected`:
  consent screen ditutup/ditolak; jalankan `dvc pull` lagi.
- `.dvc/config.local` tidak ada:
  jalankan `python scripts/setup_dvc_gdrive.py` setelah `.env` diisi.
