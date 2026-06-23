# Data Strategy — Galbay Predictor

Strategi akuisisi, pengolahan, governance, dan etika big data.

---

## 1. Sumber data & prioritas

| # | Source | Volume | Relevansi | Status | Tools |
|---|---|---|---|---|---|
| 1 | Google Play reviews fintech | Sangat tinggi (jutaan baris) | Tinggi | **Aktif** | google-play-scraper |
| 2 | TikTok komentar #galbay | Tinggi | Sangat tinggi (Gen Z) | Stub | TikTokApi/Playwright |
| 3 | Forum Kaskus + Reddit | Menengah-tinggi | Tinggi | Stub | BS4 / PRAW |
| 4 | Twitter/X post | Tinggi | Tinggi | Stub | X API v2 / snscrape |
| 5 | Google Trends | Rendah (time-series) | Tinggi (narasi) | **Aktif** | pytrends |
| 6 | Berita & siaran pers OJK | Rendah-menengah | Tinggi (regulator) | Stub | requests + BS4 |

## 2. Target big data

- **Volume target:** ratusan MB → 1GB+ teks+metadata.
- **Penggerak utama volume:** Google Play reviews (~24 app × ratusan ribu
  review potensial per app).
- **Penyimpanan:** `data/raw/` & `data/processed/` di-gitignore (>50MB).
  Sample kecil di `data/sample/` di-commit untuk reproducibility.
- **Distribusi besar:** GitHub Releases atau Git LFS (menyusul).

## 3. Keyword sinyal perilaku (inti thesis)

Keyword psikologis yang dicari di teks untuk mengubah "termometer" → "dokter":

- **Impulsif:** `self reward`, `checkout dulu bayar nanti`, `FOMO`, `flash sale`
- **Horizon pendek:** `bayar nanti aja`, `gpp cicil`, `tagihan bulan depan`
- **Avoidance/takut:** `takut ditagih`, `kabur dari DC`, `ganti nomor`,
  `dicerewet debt collector`
- **Regret loop:** `menyesal pakai paylater`, `janji gak akan lagi`, `sudah
  insyaf`
- **Sinyal sistem:** `galbay`, `gagal bayar`, `nunggak`, `macet`, `bunga
  tinggi`, `limit`

Filter `is_relevant` di `scraper/fintech_reviews.py` memakai subset keyword ini.

## 4. Pipeline

```
raw (scraping)  →  cleaning/PII redaction  →  labeling (relevant/category)
   →  modeling (risk score, NLP)  →  insight (dashboard, API, nudge)
```

- **Raw:** `data/raw/` (JSON per source per app).
- **Processed:** `data/processed/` (PII dibuang, normalisasi teks, label).
- **Sample:** `data/sample/` (di-commit, ~1000 baris).
- **Model:** `models/` (artefak ML).
- **Notebook:** `notebooks/` (eksplorasi & visualisasi).

## 5. Etika & governance (sangat penting — sorotan dosen)

### 5.1 Prinsip
- Hanya ambil **data publik**.
- **Tidak simpan PII** (nama, no HP, email). Redact sebelum commit.
- **Rate-limit sopan**; hormati `robots.txt` & ToS platform.
- Dokumentasikan sumber & tanggal scrape di `meta`.

### 5.2 Paradoks etika (kasus pemilu sebagai analogi)
> Data memberi kekuatan untuk (a) **memanfaatkan** psikologi pasar atau
> (b) **mengedukasi** ke arah benar. Pilihan ini menentukan karakter bisnis.

**Pilihan Galbay Predictor:** data digunakan untuk **nudge edukasi &
intervensi dini**, BUKAN untuk predatory targeting borrower rapuh.

Contoh kontras:
- ❌ Eksploitasi: target user "takut ditagih" → iklan pinjol baru (memperburuk).
- ✅ Edukasi: deteksi pola "self reward 3x/minggu" → nudge pending checkout
  24 jam + simulasi cicilan.

### 5.3 Compliance
- **UU PDP (Perlindungan Data Pribadi):** anonimisasi sejak scraping, consent
  untuk data user opt-in.
- **OJK regulasi paylater:** ikuti sebagai sumber data, bukan sebagai lender.
- Transparansi: sumber & metodologi terbuka di repo.

## 6. Quality & reproducibility

- Setiap batch scrape mencatat `meta`: source, scraped_at, scraper version,
  count, per-app summary.
- Sample kecil di-commit agar reviewer bisa verifikasi format tanpa download
  dataset besar.
- `tests/` smoke test memastikan app & scraper importable.

## 7. Roadmap scraping (fokus peran Anda)

| Sprint | Target |
|---|---|
| S1 (sekarang) | Google Play reviews jalan, sample data |
| S2 | Google Trends 12-bulan, dashboard narasi |
| S3 | Forum (Kaskus/Reddit) thread utang |
| S4 | TikTok komentar (perlu antisipasi anti-bot) |
| S5 | OJK & berita media (sinyal regulator) |
| S6 | Twitter/X (jika akses terbuka) + Instagram opsional |

## 8. Catatan teknis anti-bot

- TikTok/Instagram: anti-bot kuat → gunakan unofficial API + proxy rotasi +
  delay random. Ekspektasi: break sering, butuh maintenance.
- Twitter: API berbayar → prioritas turun, ambil snapshot bila ada celah
  legal (Nitter/academic).
- Play Store & Google Trends: relatif stabil, jadi backbone dataset.

---

Skema detail: `data/README.md` · Bisnis: `docs/business_plan.md`
