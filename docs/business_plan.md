# Business Plan — Galbay Predictor

> Membaca psikologi gagal bayar anak muda dari jejak digital.

**Status:** Kerangka berbasis data (diisi bertahap sesuai hasil scraping).
**Tim:** Scraping / Fullstack / Modeling.
**Repo:** https://github.com/addaan1/Final-Project-AKB

---

## 1. Executive Summary

**Galbay Predictor** adalah *financial behavior coach* berbasis big data yang
mendiagnosis **psikologi** gagal bayar Gen Z dari pola bahasa dan perilaku
digital — bukan sekadar mengukur tren.

**Analogi inti (termometer vs dokter):**
- **Termometer** = Google Trends/sentimen → mendeteksi tren "galbay" naik.
  Data tidak menjelaskan *kenapa*.
- **Dokter** = NLP pada review/komentar → membaca gejala perilaku: impulsif,
  "self reward", "checkout dulu bayar nanti", "takut ditagih DC", horizon
  berpikir pendek → diagnosa akar psikologis.
- **Obat** = produk: peringatan pre-checkout, simulasi cicilan, edukasi
  keuangan yang tidak menggurui.

**Thesis:** *"Anak muda gagal bayar bukan karena tidak punya uang, tapi karena
perilaku, gaya hidup, dan horizon berpikir pendek."* Mereka relatif stabil
(tanpa tanggungan keluarga), namun kebiasaan konsumtif & jangka pendek
(gaming, self-reward, FOMO) mendorong default.

## 2. Problem Statement

| Stakeholder | Nyeri | Bukti data (diisi) |
|---|---|---|
| Gen Z / mahasiswa | Stres tagihan, iuran paylater jam 12 malam, gossip "galbay" | _% review 1-bintang berisi keyword "ditagih"_ |
| Kampus | Mahasiswa drop out/alpa karena diganggu DC | _survei internal (placeholder)_ |
| Fintech legal | NPL tinggi, onboarding risky borrower | _rata-rara score review fintech_ |
| HR perusahaan | Karyawan stres finansial → produktivitas turun | _placeholder_ |
| OJK | Sistemik risk paylater | _siaran pers OJK (di-scrape)_ |

## 3. Insight dari Big Data (akan diisi dari scraping)

### 3.1 Lapisan Termometer — Tren (Google Trends)
- Keyword watch: `galbay`, `paylater`, `limit paylater`, `pinjol legal`,
  `cara lunasi hutang`, `self reward`, `checkout dulu bayar nanti`,
  `takut ditagih`.
- Output: time-series minat 12 bulan, geo Indonesia.
- _[Diisi: puncak tren, korelasi event, regional hotspot]_

### 3.2 Lapisan Dokter — Diagnosa psikologi (Play reviews + TikTok + Forum)
- Klasifikasi pola bahasa:
  - **Impulsif:** "self reward", "checkout dulu", "FOMO sale".
  - **Horizon pendek:** "bayar nanti aja", "gpp cicil".
  - **Takut/avoidance:** "takut ditagih", "kabur dari DC", "ganti nomor".
  - **Regret loop:** "menyesal pakai paylater", "janji gak akan lagi".
- Sinyal tejebak: kata `dicerewet`, `debt collector`, `ditagih jam 12`,
  `kasbon`, `nunggak`.
- _[Diisi: distribusi kategori, app terburuk, narasi dominan]_

### 3.3 Lapisan Obat — Intervensi (produk)
- Peringatan pre-checkout saat deteksi pola impulsif.
- Simulasi efek cicilan (visualisasi bunga & tenor).
- Nudge edukasi mikro (bukan menggurui): "Kamu tadi pakai kata self-reward
  3x minggu ini — itu sinyal FOMO. Mau coba pending 24 jam?"

## 4. Product

### 4.1 MVP
- **Web app (Flask)**: dashboard risiko perilaku + simulasi cicilan + edukasi.
- **Browser extension (next)**: peringatan pre-checkout di Shopee/Tokopedia.

### 4.2 Fitur prioritas
1. Risk score perilaku (0–100) dari analisis bahasa user (opt-in).
2. Simulasi cicilan multi-platform.
3. Dashboard tren personal & komunitas.
4. Edukasi adaptif (mikro-lesson sesuai pola).

## 5. Target Market & Segmentasi

| Segmen | Channel | Nyeri utama |
|---|---|---|
| B2C Gen Z 18–27 | TikTok, kampus, komunitas | Stres tagihan, malu |
| B2B Kampus | kerjasama Kemahasiswaan | Retensi mahasiswa |
| B2B Fintech legal | BD ke risk team | Reduksi NPL |
| B2B HR korporat | benefit karyawan | Produktivitas |
| B2B Koperasi | edukasi anggota | Gagal bayar internal |

**Persona utama:** "Dika, 21, mahasiswa, 3 paylater aktif, review TikTok
setiap malam jam 12 nunggu gajian, pernah ketagihan gacha game."

## 6. Business Model & Monetisasi (ekstrim)

| Stream | Model | Skala awal |
|---|---|---|
| B2B Kampus | lisensi tahunan + workshop | Rp 15–30jt/kampus/thn |
| B2B Fintech | API risk-score per user | rev-share / per-call |
| B2B HR | SaaS benefit karyawan | per-employee/thn |
| B2C freemium | basic gratis, pro simulasi | Rp 29rb/bln |
| Data report | lisensi laporan tren psikologis | Rp 5–20jt/laporan |
| Koperasi/komunitas | workshop + lisensi mini | Rp 3–10jt |

**Target "ekstrim menghasilkan":** kombinasi B2B anchor (kampus+fintech) untuk
revenue stabil + B2C volume + data licensing margin tinggi.

## 7. Competitive Advantage

- **Berbasis perilaku (psikologi), bukan credit score klasik.** SLIK OJK hanya
  lihat historis; kami lihat *intensi* dari bahasa.
- **Big data native:** jutaan review + komentar = dataset perilaku Gen Z
  terbesar di kategori ini (moat data).
- **Edukasi non-menggurui** (tone Gen Z), bukan literasi keuangan kaku.

## 8. Go-to-Market

1. **Pilot kampus** (1–2 kampus early adopter, free 3 bulan → case study).
2. **Content engine TikTok/IG** dengan insight data (viral hook "katanya
   self-reward, eh galbay").
3. **BD fintech legal** pakai data report sebagai door-opener.
4. **Partnership komunitas edukasi finansial** (co-branding).

## 9. Roadmap

| Fase | Waktu | Output |
|---|---|---|
| F1 — Data foundation | Minggu 1–3 | Pipeline scraping jalan, ~1GB data |
| F2 — Insight & model | Minggu 3–6 | Risk score, dashboard |
| F3 — MVP web | Minggu 4–8 | Flask dashboard + simulasi |
| F4 — Pilot B2B | Minggu 8–12 | 1–2 kampus, 1 fintech |
| F5 — Monetisasi | Bulan 4+ | Kontrak B2B pertama |

## 10. Tim & RACI

| Peran | PIC | Tanggung jawab |
|---|---|---|
| Scraping | (Anda) | Akuisisi big data multi-platform |
| Fullstack | (Teman) | Web app, dashboard, API |
| Modeling | (Teman) | NLP, risk score |

## 11. Risiko & mitigasi

| Risiko | Mitigasi |
|---|---|
| Scraping diblokir platform | Multi-source, rate-limit sopan, snapshot legal |
| Etika data (eksploitasi vs edukasi) | Governance: data untuk nudge edukasi, bukan predatory targeting |
| Regulasi OJK/PDP | Anonimisasi PII, compliance UU PDP |
| Adopsi B2C lambat | Anchor B2B dulu, B2C sebagai flywheel |

## 12. Tautan

- **Business Model Canvas (9 blok, data-driven):** [`docs/bmc.md`](bmc.md)
- Detail keuangan: `docs/financial_plan.md`
- Strategi data & etika: `docs/data_strategy.md`
- Metodologi modelling: `docs/analysis_methodology.md`
- Skema dataset: `data/README.md`
- Output dashboard: `data/site/data.js` (auto-generated, 10,5KB)
