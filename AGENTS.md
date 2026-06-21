# AGENTS.md

Panduan untuk agent/ kontributor yang bekerja di repo ini.

## Identitas commit

- Git config **lokal repo**:
  - `user.name` = `adi`
  - `user.email` = `adieffendy5@gmail.com`
- Pastikan email ini terverifikasi di https://github.com/settings/emails agar commit terhitung sebagai contribution GitHub.

## Branch policy

- `main` **diproteksi**: tidak boleh direct push. Semua perubahan lewat Pull Request.
- Branch kerja: `fullstack` (aplikasi web) dan `scraping` (akuisisi big data).
- Merge ke `main` wajib **squash merge** + linear history.
- Jangan pernah commit ke `main` secara langsung setelah proteksi aktif.

## Workflow kontribusi

1. Checkout branch kerja (`scraping` atau `fullstack`).
2. Buat perubahan, commit dengan pesan imperatif: `Add Google Play reviews scraper`.
3. Push branch.
4. Buka PR ke `main`: `gh pr create --base main --head scraping --title "..." --body "..."`.
5. Merge via squash: `gh pr merge --squash --delete-branch=false`.

## Perintah verifikasi wajib

Sebelum push, jalankan dan pastikan lolos:

```powershell
# Typecheck / lint (jika sudah ada)
# python -m py_compile $(git ls-files '*.py')   # fallback minimal
python -m py_compile app\ scraper\ run.py config.py
```

Jika ada test:
```powershell
python -m pytest -q
```

## Aturan big data

- File data besar (>50MB) **TIDAK** dikomit. Hanya sample kecil di `data/sample/`.
- `data/raw/` dan `data/processed/` sudah di-gitignore.
- Untuk distribusi dataset besar, gunakan **GitHub Releases** atau **Git LFS** (konfigurasi menyusul).
- Simpan skema & dokumentasi dataset di `data/README.md`.

## Etika scraping

- Hanya ambil data publik.
- Jangan store PII (nama, no HP, email user). Hapus/redact sebelum commit.
- Rate-limit sopan; hormati `robots.txt` & ToS platform.
- Dokumentasikan sumber & tanggal scrape di `data/README.md`.

## Lingkungan

- Python 3.12 (Windows dev).
- Aktifkan venv sebelum install/jalan: `.\.venv\Scripts\Activate.ps1`.
- Freeze dependency: `pip freeze > requirements.txt` (hanya package yang relevan).
