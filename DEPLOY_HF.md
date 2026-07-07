# Deploy ke Hugging Face Spaces

Dokumen ini menjelaskan jalur deploy gratis untuk **Galbay Predictor** sebagai **Hugging Face Docker Space**.

## Tujuan deploy

- aplikasi publik tetap bisa dipakai untuk demo;
- dataset besar tidak di-pull via DVC saat runtime;
- login memakai akun demo bawaan;
- register, waitlist, OAuth, dan penyimpanan lokal dimatikan.

## File yang dipakai

- `Dockerfile`
- `.dockerignore`
- `requirements-runtime.txt`
- `HF_SPACE_README.md`

## Environment yang dipakai

Set default deploy ini:

```text
APP_CONFIG=production
DEMO_ONLY=1
ALLOW_REGISTRATION=0
ALLOW_WAITLIST=0
ALLOW_OAUTH=0
PERSIST_LOCAL_WRITES=0
```

Yang wajib kamu isi di Hugging Face:

```text
SECRET_KEY=<isi-random-yang-aman>
```

## Langkah deploy

1. Buat repo baru di [Hugging Face Spaces](https://huggingface.co/new-space) dan pilih **Docker**.
2. Copy isi `HF_SPACE_README.md` menjadi `README.md` di repo Space.
3. Copy source project ini ke repo Space.
4. Tambahkan `SECRET_KEY` pada menu **Settings > Variables and secrets**.
5. Push semua file ke repo Space.
6. Tunggu build selesai, lalu buka URL Space.

## Login demo

- `demo@galbay.id` / `demo123`
- `premium@galbay.id` / `demo123`

## Verifikasi cepat

Setelah Space hidup, cek:

1. `GET /`
2. `GET /login`
3. login dengan `demo@galbay.id`
4. `GET /dashboard/ringkasan`
5. `POST /api/chat`
6. `POST /api/score`
7. `GET /tools/dc-simulator`

## Catatan penting

- Free tier Hugging Face bisa sleep saat idle, dan itu normal.
- Waitlist/premium form di public demo hanya preview, tidak menyimpan data.
- Kalau nanti mau aktifkan Google OAuth, itu iterasi berikutnya karena butuh callback URL Space dan `authlib` di runtime.
