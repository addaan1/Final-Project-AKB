# Perencanaan Keuangan — Galbay Predictor

**Status:** Kerangka berbasis data. Angka placeholder akan diisi & divalidasi
dari hasil scraping (volume review, demografi TikTok) + riset pasar.

> Catatan dosen: bisnis harus **benar-benar menghasilkan income**. Angka di
> bawah disusun agar realistis dan margin-sehat, bukan vanity metric.

---

## 1. Asumsi utama (akan diperbarui dari data)

| Variabel | Asumsi awal | Sumber validasi |
|---|---|---|
| Total addressable Gen Z 18–27 ID | ~25 juta | BPS |
| Penetrasi paylater Gen Z | ~35% | survey/riset OJK |
| % Gen Z stres tagihan | ~20% dari user paylater | data review (proxy) |
| Conversion B2C free→pro | 3% | benchmark fintech app |
| Churn B2C bulanan | 8% | benchmark SaaS consumer |
| CAC B2C (organic TikTok-led) | Rp 5rb | content engine low cost |
| ARPU B2C pro | Rp 29rb/bln | pricing pilot |
| CAC B2B kampus | Rp 2jt | sales effort |
| ACV kampus | Rp 20jt/thn | lisensi + workshop |
| Gross margin | 78% | SaaS digital |

## 2. Unit economics

### 2.1 B2C (consumer)
- CAC = Rp 5.000 (organic-led, content TikTok dengan insight data).
- ARPU = Rp 29.000/bln → Rp 348.000/thn.
- LTV (gross margin 78%, retention 12 bln avg) = 348.000 × 0,78 × 12 = **Rp 3,25jt**.
- **LTV/CAC ≈ 65** → sangat sehat (benchmark SaaS >3 sehat).

### 2.2 B2B kampus
- CAC = Rp 2jt (sales + demo).
- ACV = Rp 20jt/thn; net retention 90%.
- LTV (5 thn × 0,9 churn) = 20jt × 5 × 0,78 = **Rp 78jt** per kampus.
- **LTV/CAC ≈ 39** → sehat.

### 2.3 B2B fintech (API risk-score)
- Model: per-call Rp 500 atau rev-share 1% dari loan yang berhasil di-hindari
  default (backend lebih besar tapi butuh model akurat).
- Asumsi awal: 10 fintech × Rp 30jt/thn = Rp 300jt/thn.

## 3. Proyeksi 3 tahun ( Konservatif )

| Metrik | Thn 1 | Thn 2 | Thn 3 |
|---|---|---|---|
| B2C user berbayar | 1.500 | 12.000 | 50.000 |
| Revenue B2C | Rp 52jt | Rp 417jt | Rp 1,74M |
| Kampus B2B | 5 | 25 | 80 |
| Revenue kampus | Rp 100jt | Rp 500jt | Rp 1,6M |
| Fintech B2B | 2 | 8 | 20 |
| Revenue fintech | Rp 60jt | Rp 240jt | Rp 600jt |
| Data report lisensi | Rp 30jt | Rp 120jt | Rp 300jt |
| **Total revenue** | **Rp 242jt** | **Rp 1,28M** | **Rp 4,24M** |
| COGS (server, data, API) | Rp 60jt | Rp 280jt | Rp 930jt |
| **Gross profit** | Rp 182jt | Rp 1,0M | Rp 3,31M |
| OPEX (tim, marketing, sales) | Rp 350jt | Rp 700jt | Rp 1,5M |
| **EBITDA** | (Rp 168jt) | Rp 300jt | Rp 1,81M |

> Semua angka dalam Rupiah. M = miliar.

## 4. Break-even

- **B2C unit** break-even per user: langsung (CAC jauh di bawah ARPU pertama
  bulan).
- **Perusahaan** break-even: akhir Tahun 2 (~Rp 1,0M gross profit vs Rp 700jt
  OPEX → EBITDA positif Rp 300jt).

## 5. Cost structure

| Komponen | Proporsi | Catatan |
|---|---|---|
| Tim (3 founder + kontrak) | 55% | Dev, ML, sales |
| Infra (cloud, DB, scraping proxy) | 12% | Naik dengan volume data |
| Marketing/content | 18% | TikTok-led, low CAC |
| Sales B2B | 10% | Komisi + travel |
| Data acquisition & compliance | 5% | Proxy, legal PDP |

## 6. Funding & milestone

- **Bootstrap Tahun 1**: modal founder kecil + revenue pilot kampus.
- **Seed (opsional Tahun 2)**: Rp 1–2M untuk scale sales & infra data.
- Milestone trigger funding: 5 kampus + 2 fintech + 5rb B2C berbayar.

## 7. Sensitivitas (apa yang harus dijaga)

| Lever | Dampak | Aksi |
|---|---|---|
| Churn B2C naik 2x | LTV turun ~50% | Retensi: nudge edukasi, streak |
| CAC B2B naik 2x | LTV/CAC turun ~20x | Product-led sales, case study |
| Regulasi PDP ketat | COGS compliance naik | Anonimisasi sejak scraping |
| Scraping diblokir | Dataset mengecil | Multi-source, snapshot legal |

## 8. Validasi data yang dibutuhkan (push ke tim scraping)

- [ ] Volume & distribusi skor review fintech (proxy stres borrower).
- [ ] Demografi/tonal TikTok #galbay (proxy Gen Z penetration).
- [ ] Tren Google Trends 12 bln (proxy market timing).
- [ ] Frekuensi keyword psikologis (impulsif/avoidance/regret).

## 9. KPI operasional (dashboard)

- MRR B2C, logos B2B, churn, CAC payback, NPS, data volume scraped,
  % relevant review, model precision.

---

Detail bisnis: `docs/business_plan.md` · Strategi data: `docs/data_strategy.md`
