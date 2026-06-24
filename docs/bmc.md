# Business Model Canvas — Galbay Predictor

> Setiap blok di bawah ini disusun berdasarkan data aktual dari 5 sumber (Play Store, OJK/media, Forum, Blog, Google Trends) yang totalnya **350.123 item** (`data/site/data.js`). Angka-angka yang dikutip dapat diverifikasi ulang lewat `data/site/data.js` atau `python -m scripts.analyze`.

**Ringkasan eksekutif (1 paragraf):**
Galbay Predictor adalah *financial behavior coach* untuk Gen Z Indonesia yang membaca **psikologi gagal bayar** dari jejak digital. Berbeda dengan termometer tren (Google Trends/sentimen rata-rata), Galbay membaca **dokter**: NLP pada review/komentar untuk mendeteksi pola impulsif, horizon pendek, takut/avoidance, dan regret loop — lalu memberikan intervensi dini (peringatan pre-checkout, simulasi cicilan, edukasi non-menggurui). **Dataset**: 349.201 review Play Store (44 app, 11 kategori) + 35.968 review relevan (10,30%) + 8.340 sinyal distress (23,2% dari relevan). **Model**: Multinomial Naive Bayes from-scratch, F1=0,841, **5-fold CV=0,848±0,002** (sangat stabil).

---

## 1. Customer Segments (CS)

| Segmen | Profil | Ukuran pasar (estimasi) | Bukti data |
|---|---|---|---|
| **B2C Gen Z 18–27** | Mahasiswa/early worker, pengguna aktif paylater, galbay-prone | ~25 juta Gen Z (BPS); ~35% pakai paylater (~8,75jt); 23,2% dari review relevan menunjukkan distress → ~2 juta potensial B2C | 8.340 review distress dari 35.968 relevan = **23,2% distress rate** |
| **B2B Kampus** | Kemahasiswaan yang peduli retensi & wellbeing mahasiswa | ~4.500 PTN/PTS di Indonesia, ~50 punya kemahasiswaan aktif = ~2.250 target | Korelasi: `distress_pct=23,2%` di 44 app → mahasiswa dengan pinjol aktif = risiko drop-out |
| **B2B Fintech Legal** | Risk team fintech yang butuh filter borrower rapuh | 100+ fintech terdaftar OJK; ~50 fintech lending aktif | NPL rate proxy: 5 dari 10 top-neg-apps adalah pinjol (neg_pct >50%) |
| **B2B HR Korporat** | Benefit division, employee wellness | ~5.000 perusahaan multinasional/besar di Indonesia | "Stress finansial → produktivitas turun" (well-established literature) |
| **B2C Koperasi/Komunitas** | Edukasi anggota, modul keuangan keluarga | ~120.000 koperasi aktif di Indonesia | Skala kecil, mission-aligned |

**Persona utama:** "Dika, 21, mahasiswa, 3 paylater aktif, sering checkout jam 12 malam, pernah gagal bayar".

**Persona sekunder:** "Rina, 25, karyawan baru, 1 paylater + 1 KTA, skor SLIK bersih, tapi bahasa chat dengan teman menunjukkan avoidance ('takut ditagih')."

---

## 2. Value Propositions (VP)

| Value | Bukti data | Diferensiasi |
|---|---|---|
| **Diagnosis perilaku (bukan tren)** | 7 kategori behavioral ter-ekstrak dari 35.968 review relevan (Diskusi Produk 20.246, Bunga & Biaya 12.445, Tagihan/DC 4.809, dst) | Kredit skor (SLIK OJK) hanya lihat historis; kami lihat **intensi** dari bahasa |
| **Moat data 350K+ review** | 349.201 review dari 44 app + 582 OJK/media + 244 forum + 53 time-series = 350.123 total dari 5 source aktif | Kompetitor (Flip, Bibit) tidak punya dataset perilaku Gen Z sebesar ini |
| **AI Coach NLP (38 intents)** | `app/api.py::CHATBOT_MODULES` punya 8 modul × 38 intents, sinonim, multi-intent, sentiment detection | Chatbot finansial generik (KoinWorks, etc.) tidak punya module M3 Debt Strategy / M4 DC Negotiation |
| **3 game-changer** | Pinjol Blacklist (50+ DB), Debt Snowball/Avalanche Planner, Recovery Roadmap 30/60/90 hari | Fitur generik di financial app; galbay-specific tidak ada |
| **Edukasi non-menggurui** | Top negative words: `lintah`, `berkedok`, `tolol`, `sampah`, `bodoh` — borrower butuh dilayani, bukan divonis | OJK SIPEDAS / AFPI formal, tone kaku; Gen Z butuh pendekatan kasual |

**Tagline:** *"Termometer bilang tren naik; dokter Galbay bilang kenapa — dan apa yang harus dilakukan."*

---

## 3. Channels (CH)

| Channel | Fungsi | Bukti data |
|---|---|---|
| **Web app (Flask)** | Onboarding, dashboard, simulasi, chatbot, game-changer | `app/` Flask scaffold, 5 dashboard routes, 308 tests pass |
| **TikTok content engine** | Akuisisi B2C organik Gen Z | Anti-bot scrape gagal (TikTok 0 items), tapi justru jadi peluang content |
| **B2B direct sales** | Kampus + Fintech + HR | CAC B2B diasumsikan Rp 2jt (lihat financial_plan §2.2) |
| **Community (Discord/Telegram)** | Edukasi + retention | 23,2% distress rate = komunitas yang butuh ruang aman |
| **Workshop/seminar** | Activation B2B & brand awareness | Topik: "Baca bahasa Gen Z dari review fintech" — pakai data 350K sebagai hook |
| **Marketplace listing** (planned) | Lead magnet untuk Shopee/Tokopedia seller yang target audiens cicilan | Marketplace scraper built (`scraper/marketplace.py`), blocked by anti-bot → pivot ke API atau partner |

---

## 4. Customer Relationships (CR)

| Tipe | Implementasi | Bukti data |
|---|---|---|
| **Self-serve (B2C)** | Free tier: dashboard + simulasi cicilan. Premium Rp 29rb/bln: AI Coach unlimited + save unlimited | `app/auth.py::seed_demo_users` → `demo@galbay.id` (free) + `premium@galbay.id` (premium) |
| **Account manager (B2B)** | Dedicated PIC untuk kontrak kampus & fintech | ACV B2B Rp 20jt/thn/kampus (lihat financial_plan §2.2) |
| **Community-led (B2C retention)** | Telegram/Discord peer support | 8.340 distress signal = basis komunitas yang jelas |
| **Crisis hotline fallback** | Self-harm detection di chatbot → arahkan ke Sejiwa 119 ext 8 | `app/api.py` punya `self_harm` intent + Sejiwa referral (lihat `analysis_methodology.md` bagian chatbot) |
| **Data-driven nudges** | Push notification 7 hari sebelum tagihan; soft-warning di Pre-checkout | Recovery Roadmap 30/60/90 hari (game-changer #3) |

---

## 5. Revenue Streams (RS)

| Stream | Model | Proyeksi Thn-1 | Justifikasi data |
|---|---|---|---|
| **B2C freemium (premium)** | Rp 29rb/bln × 12 bln = Rp 348rb/thn/user; target 1.500 user = **Rp 52jt** | 8.340 distress × 3% conversion × 1.500 user (lihat financial_plan §3) |
| **B2B Kampus (lisensi)** | Rp 20jt/thn × 5 kampus = **Rp 100jt** | 2.250 target kampus × 0,2% conversion pilot thn-1 |
| **B2B Fintech (API risk-score)** | Rp 30jt/thn × 2 fintech = **Rp 60jt** | 50 fintech aktif × 4% conversion (lihat financial_plan §2.3) |
| **Data report lisensi** | Rp 30jt × 1 laporan = **Rp 30jt** | Pricing report: 1 laporan trend tahunan |
| **Workshop/komunitas** | Rp 5jt × 4 workshop = **Rp 20jt** | Premium tier activation event |
| **B2B HR (SaaS benefit)** | Rp 50rb/employee/bln × 1.000 employee × 12 bln = **Rp 600jt** (long-tail) | Tunda thn-2 setelah ada 1 case study |
| **TOTAL Thn-1** | (lihat financial_plan §3) | **Rp 242jt** revenue, **Rp 182jt gross profit** (gross margin 78%) |

---

## 6. Key Resources (KR)

| Resource | Detail | Bukti |
|---|---|---|
| **Dataset perilaku 350K** | 349.201 review Play + 582 OJK/media + 244 forum + 53 trends + 44 blog = **350.123 item** | `data/raw/` + `data/site/data.js::meta.total_multi_source` |
| **11 kategori fintech** | paylater, ecommerce, ewallet, pinjol, bank_digital, mobile_banking, p2p_lending, investasi, kartu_kredit, koperasi, travel | `data/site/data.js::meta.n_categories=11` |
| **Multinomial NB from-scratch** | F1=0,841, CV=0,848±0,002, vocab=4.446 (filtering min_df=5) | `scripts/sentiment_model.py` + `data/site/data.js::model` |
| **VADER ID lexicon 50+ kata** | Galbay/fintech domain (galbay, nunggak, dc, ilegal, dll) + multi-source slang (anjir, bangsat, capek, mantul) | `processing/id_lexicon.py` |
| **Behavioral severity scoring** | 0-100 score + bucket rendah/sedang/tinggi (31.028 / 4.436 / 504) | `scripts/behavior_analysis.py::score_severity` |
| **AI Coach (38 intents, 8 modul)** | M1 Galbay Basics, M2 Pinjol, M3 Debt Strategy, M4 DC Negotiation, M5 Recovery, M6 Legal, M7 App, M8 Mental Health | `app/api.py::CHATBOT_MODULES` |
| **3 game-changer** | Pinjol Blacklist (50+ DB), Debt Planner, Recovery Roadmap | `app/api.py` |
| **Pinjol database** | 50+ legal + 15 ilegal sample | `data/pinjol_database.json` |
| **Tech stack** | Flask 3, Python 3.12, scikit-learn, NLTK VADER, Playwright, DVC, Authlib, pytrends | `requirements.txt` (21 packages) |
| **Brand & UI** | Vibrant purple theme (#9b5de5), dark mode #0f0625, glassmorphism chatbot, premium gold | `app/static/css/style.css` |
| **Tests 308 passing** | API, auth, chatbot, routes, produk, simulasi, dll | `tests/` |
| **Tim** | 3 founder (Scraping, Fullstack, Modeling) + on-demand freelance | `docs/business_plan.md::Tim & RACI` |

---

## 7. Key Activities (KA)

| Aktivitas | Output | Justifikasi data |
|---|---|---|
| **Multi-source scraping** | Pipeline `scraper/*.py` (11 scraper) | 5 source aktif menghasilkan 350.123 items; scraping ulang berkala untuk menjaga freshness |
| **Modeling & retraining** | NB + VADER ID + behavioral severity | F1=0,841 perlu retrain berkala (drift detection per quarter) |
| **AI Coach training** | 38 intents, 8 modul | Update intent baru per pattern yang muncul di review (e.g. kata slang baru) |
| **Content engine** | TikTok/IG insight mingguan | Volume data 350K cukup untuk 1 insight/minggu tanpa overlap |
| **B2B sales & partnership** | Kontrak kampus + fintech | 5 kampus thn-1, 25 thn-2 (lihat financial_plan) |
| **Edu content production** | Mikro-lesson adaptif, chatbot FAQ | Top negative words = `lintah`, `tolol`, `sampah` → butuh tone edukatif, bukan menggurui |
| **Compliance & privacy** | Anonimisasi PII, UU PDP | `docs/data_strategy.md::Etika` |
| **Customer support B2C** | Email/Telegram, chatbot fallback | Premium tier dapat prioritas response <4 jam |

---

## 8. Key Partnerships (KP)

| Partner | Tipe | Nilai |
|---|---|---|
| **OJK** | Regulator (data source) | 79+ news OJK = landasan narasi regulasi (lihat `ojk_news.py`) |
| **Kampus (pilot)** | B2B anchor customer | 5 kampus thn-1 = case study & word-of-mouth Gen Z |
| **Fintech legal** | B2B customer + co-marketing | NPL reduction case study = narasi kuat untuk fundraising |
| **Komunitas edukasi finansial** | Distribution + content co-creation | Bantu distribusi ke 100K+ audiens tanpa CAC besar |
| **DVC + Google Drive** | Infra dataset | Dataset 350K+ di-track via DVC, didistribusi via GDrive (lihat `data/raw.dvc`) |
| **Auth provider (Google OAuth)** | Auth | `app/auth.py` pakai authlib untuk Google OAuth |
| **NLP libraries (NLTK, scikit-learn)** | Tech stack | VADER + Naive Bayes (lihat `requirements.txt`) |
| **Content creator (TikTok/IG)** | Distribution | 5-figure follower Gen Z financial creator = akuisisi organik |
| **Data cleaning service** | Outsource (thn-2+) | 180MB raw Play Store perlu cleaning/validasi manual di awal |

---

## 9. Cost Structure (CS$)

| Komponen | % | Thn-1 (estimasi) | Justifikasi |
|---|---|---|---|
| **Tim (3 founder + freelance)** | 55% | Rp 350jt | Founder = sweat equity, freelance untuk design + content |
| **Infra (cloud, DB, proxy)** | 12% | Rp 72jt | Scraping proxy (rotating IP) + hosting Flask + DVC storage |
| **Marketing & content** | 18% | Rp 108jt | TikTok content engine + IG ads + 1 event kampus |
| **Sales B2B** | 10% | Rp 60jt | Komisi sales + travel ke kampus/fintech |
| **Data acquisition & compliance** | 5% | Rp 30jt | Proxy premium, legal review UU PDP |
| **TOTAL** | 100% | **Rp 620jt OPEX** | Gross profit Rp 182jt → EBITDA (Rp 168jt) thn-1 (lihat financial_plan §3) |

**Cost-as-you-grow**: Biaya scrape proxy & cloud naik linear dengan volume data. Mitigasi: caching, delta-scraping (hanya app yang diupdate sejak scrape sebelumnya).

---

## Validasi: Konsistensi Antarblok

| Check | Hasil |
|---|---|
| CS ↔ VP | 8.340 distress (CS) dijawab dengan 3 game-changer + AI Coach (VP) ✓ |
| CS ↔ CH | Gen Z 18-27 dijangkau via TikTok + web app (CH) ✓ |
| VP ↔ KR | Behavioral coach (VP) didukung oleh 350K dataset + NB model (KR) ✓ |
| VP ↔ KA | "Diagnosis perilaku" butuh scraping+modeling+content engine (KA) ✓ |
| KA ↔ KR | Aktivitas scraping perlu scraper pipeline (KR) ✓ |
| RS ↔ KR | Premium Rp 29rb/bln butuh AI Coach unlimited (KR) ✓ |
| KP ↔ KA | OJK partnership (KP) mendukung aktivitas compliance (KA) ✓ |
| CS ↔ RS | B2B kampus (CS) match dengan lisensi B2B (RS) ✓ |

---

## Critical Risks & Mitigations

| # | Risk | Tipe | Severity | Mitigasi |
|---|---|---|---|---|
| 1 | **Scraping diblokir** (TikTok/Tokped/Shopee anti-bot) | Operasional | Tinggi | Multi-source diversification (5 source aktif). Backup: API partner, snapshot legal |
| 2 | **Kompetitor copy** (Flip/Bibit bikin fitur serupa) | Pasar | Tinggi | First-mover advantage via 350K dataset moat; cepat iterasi AI Coach |
| 3 | **Regulasi PDP/UU PDP** (pembatasan data pribadi) | Regulasi | Tinggi | Compliance-by-design: PII redaction sejak scraping (lihat `data_strategy.md::5.3`) |
| 4 | **Key person risk** (3 founder, thin team) | Operasional | Sedang | Dokumentasi SOP + open-source core (repositori publik) untuk continuity |
| 5 | **Model drift** (akurasi turun seiring perubahan bahasa Gen Z) | Teknis | Sedang | Retrain per quarter + monitoring macro_F1 alert; expand slang lexicon (sudah +20 kata di Round 6) |
| 6 | **Conversion B2C rendah** (3% asumsi bisa meleset) | Pasar | Sedang | Pivot ke B2B anchor lebih cepat (kampus+fintech) sebagai fallback |
| 7 | **Churn B2C tinggi** (8%/bln) | Finansial | Sedang | Retention: streak, gamification, milestone (Recovery Roadmap 30/60/90) |
| 8 | **Burn rate** (Rp 350jt OPEX thn-1, revenue baru Rp 242jt) | Finansial | Tinggi | Bootstrap ringan, founder salary 0 di awal; thn-2 EBITDA break-even |
| 9 | **Etika data** (dianggap predatory fintech) | Reputasi | Sedang | Tone edukatif non-menggurui (lihat top negative words → borrower butuh dilayani), compliance governance |
| 10 | **Anti-bot scraping cost** (proxy, captcha solver) | Operasional | Rendah | Snapshot berkala + incremental scraping, fallback ke partner API |

---

## Verifikasi & Sumber

- **Dataset aktual**: `data/site/data.js` (10,488 bytes, auto-generated oleh `python -m scripts.analyze`)
- **CSV intermediate**: `data/processed/all_reviews.csv` (52MB), `relevant_only.csv` (8,7MB)
- **Charts**: `data/site/assets/{confusion_matrix,top_neg_words,distress_trend,multi_source_breakdown,severity_distribution}.png`
- **Test regression**: `pytest tests/` → 308 pass, 0 fail
- **Model artifact**: `scripts/sentiment_model.py` (NB modular) + `processing/id_lexicon.py` (VADER ID)
- **Business context**: `docs/business_plan.md` (kerangka awal) + `docs/financial_plan.md` (proyeksi 3 tahun)

---

**Versi dokumen**: 1.0 (Regenerasi multi-source) · **Tanggal**: 2026-06-24 · **Branch**: `feat/multi-source-700k`
