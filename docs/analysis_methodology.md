# Metodologi Analisis — Sentiment & Behavioral Modelling

Dokumentasi metodologi untuk 3 komponen modelling di final project Galbay Predictor:
**(A)** Naive Bayes sentiment classifier, **(B)** behavioral (galbay) analysis,
**(C)** VADER sentiment (NLTK). Untuk laporan/presentasi.

---

## A. Sentiment Classifier — Multinomial Naive Bayes (from scratch)

**File:** `scripts/sentiment_model.py` (dipanggil dari `scripts/analyze.py`)

### Pipeline

1. **Label:** review dengan skor 1-2 dilabeli negatif (0), skor 4-5 positif (1).
   Skor netral (3) dibuang dari data training/testing — klasifikasi biner, bukan 3-kelas.
2. **Tokenisasi:** regex `[a-zA-Z]+`, lowercase, buang token < 3 huruf dan stopword
   Indonesia (kata fungsi: "yang", "di", "dan", dst — lihat `STOPWORDS`).
3. **Vocabulary:** kata yang muncul di minimal `MIN_DF=5` dokumen training (membuang kata
   langka yang tidak punya daya pembeda statistik dan hanya menambah noise/overfitting).
4. **Split:** *stratified* 80/20 — proporsi label dijaga sama persis di train & test,
   bukan random permutation polos (yang bisa membuat test set kecil/timpang pada
   distribusi label yang tidak seimbang).
5. **Training:** Multinomial Naive Bayes dengan **Laplace (add-1) smoothing**, dihitung
   manual dari scratch (`P(word|class) = (count+1) / (total_words_in_class + |V|)`).
6. **Evaluasi:** confusion matrix, accuracy, precision/recall/F1 (kelas positif) **+
   macro-F1** (rata-rata precision/recall/F1 lintas kedua kelas — versi awal hanya
   melaporkan dari sudut kelas positif).
7. **Cross-validation (opsional):** `cross_validate()` — stratified k-fold (default k=5)
   untuk mean±std accuracy/F1, lebih meyakinkan daripada angka dari 1 kali split.

### Mengapa from scratch?

Tidak memakai `sklearn.naive_bayes` karena bagian ini secara eksplisit menjadi syarat
project: mendemonstrasikan pemahaman matematis Naive Bayes (Bayes' theorem + asumsi
independensi kata + Laplace smoothing), bukan sekadar memanggil library.

### Keterbatasan yang diketahui

- Bag-of-words mentah (count, bukan TF-IDF) — kata umum yang sering muncul di kedua
  kelas (mis. "aplikasi", sudah masuk stopword) bisa mendominasi tanpa pembobotan.
- Tidak ada stemming Bahasa Indonesia (mis. "membantu"/"terbantu"/"bantuan" dihitung
  sebagai token berbeda) — peluang improvement lanjutan kalau butuh akurasi lebih tinggi.

---

## B. Behavioral (Galbay) Analysis

**File:** `scripts/behavior_analysis.py` (dipanggil dari `scripts/analyze.py`)

### Taksonomi kategori

Setiap review yang relevan sudah ditandai dengan 0+ kategori perilaku saat scraping
(`matched_categories_str`, kolom hasil tahap labeling sebelum modelling):

| Key | Label | Termasuk distress? |
|---|---|---|
| `distress_langsung` | Distress Finansial Langsung | Ya |
| `tagihan_dan_penagihan` | Tagihan & Penagihan (DC) | Ya |
| `psikologi_regret_stress` | Psikologi: Penyesalan/Stres | Ya |
| `psikologi_avoidance` | Psikologi: Menghindar | Ya |
| `psikologi_impulsif` | Psikologi: Impulsif | Tidak |
| `bunga_dan_biaya` | Keluhan Bunga & Biaya | Tidak |
| `produk_fintech` | Diskusi Produk Fintech | Tidak |

`distress` = flag biner: 1 jika review mengandung minimal 1 kategori distress di atas.

### Severity score (0-100) — penambahan baru

Flag biner `distress` tidak bisa membedakan review yang menyentuh 1 sinyal galbay
dengan yang menyentuh banyak sinyal sekaligus. `score_severity()` menggabungkan dua
komponen, masing-masing dibatasi (capped) lalu diberi bobot 50%:

```
cat_score = min(jumlah kategori distress yang match, 3) / 3 * 50
kw_score  = min(jumlah keyword galbay yang match, 3) / 3 * 50
severity  = cat_score + kw_score   # 0-100
```

Dibucketkan: **rendah** (<33), **sedang** (33-66), **tinggi** (≥66) — dasar awal untuk
fitur produk seperti Recovery Roadmap, tanpa mengubah kontrak `distress` yang sudah
dipakai bagian lain (`cat_stats`, `app_stats`, timeline).

### Keyword scan

Regex sederhana per topik (gagal bayar, denda, DC, teror, ilegal, dst). Pattern
`pinjol ilegal` diperketat dengan word-boundary (`\bilegal\b|\blegal\b|\bojk\b`) — versi
awal (`ilegal| legal|ojk`, tanpa `\b`) bisa salah match substring di kata tak terkait
(mis. "legalisir").

---

## C. VADER Sentiment (NLTK) — diperluas untuk Bahasa Indonesia

**File:** `processing/sentiment.py` + `processing/id_lexicon.py`

### Masalah

VADER (`nltk.sentiment.vader`) adalah lexicon-based sentiment analyzer berbahasa
Inggris. Lexicon bawaannya nyaris tidak punya entri kata Indonesia, jadi tanpa
modifikasi, hampir semua teks ulasan Indonesia diberi skor **netral** secara default —
bukan karena teksnya benar-benar netral, tapi karena VADER tidak mengenali kata-katanya
sama sekali.

### Solusi: extend, jangan ganti algoritma

Tetap memakai VADER (sesuai requirement project), tapi mengisi 3 komponen yang hilang:

1. **Lexicon Indonesia** (`ID_SENTIMENT_LEXICON`, ~150 kata) di-merge ke
   `sia.lexicon` — mencakup kata sentimen umum (bagus, buruk, kecewa, puas, dst) dan
   istilah domain fintech/galbay (galbay, nunggak, dc, teror, ilegal, lancar, cair, dst).
2. **Negator Indonesia** (`tidak`, `bukan`, `tanpa`, `jangan`, `belum`, `tak`) di-merge
   ke `vader.NEGATE`, supaya pola seperti "tidak bagus" benar-benar dibalik ke negatif
   — tanpa ini, VADER hanya mengenali negator Inggris ("not", "n't").
3. **Booster Indonesia** (`sangat`/`amat` menaikkan intensitas, `agak`/`kurang`
   menurunkan) di-merge ke `vader.BOOSTER_DICT`.
4. **Normalisasi teks** — `analyze_sentiment()` memanggil
   `processing.preprocess.clean_text()` sebelum scoring, supaya slang ("gak", "nggak")
   ternormalisasi ke bentuk baku ("tidak") yang dikenali negator di atas, sekaligus
   membersihkan URL/mention/hashtag.

Trade-off yang disadari: `clean_text()` lowercase dan membuang tanda baca/emoji, jadi
sinyal intensitas dari huruf kapital/tanda seru/emoji bawaan VADER ikut hilang. Ini
tetap dianggap *net positive* dibanding bug awal (VADER buta total bahasa Indonesia).

### Validasi

`tests/test_sentiment.py` diperketat dari assert longgar (`in ("positive","neutral")`,
yang menutupi bug ini) menjadi assert deterministik, termasuk test khusus untuk negasi
("tidak bagus" → negatif) dan istilah domain ("...dc... galbay" → negatif).
