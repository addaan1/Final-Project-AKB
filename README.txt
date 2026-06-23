GALBAY PREDICTOR — Financial Behavior Coach
"Mining Perilaku Digital Gen Z untuk Membangun Bisnis Financial
Behavior Coach Berbasis Big Data"
==================================================================

ISI FOLDER
----------
- index.html      : LANDING PAGE (halaman pembuka) — buka ini dulu
- dashboard.html  : DASHBOARD ANALISIS (data, modelling, BMC, dll)
- style.css       : Tema desain (ungu-lime, dark, modern)
- script.js       : Logika grafik + animasi (membaca data.js)
- data.js         : DATA ASLI hasil scraping + modelling (otomatis)
- assets/         : Gambar hasil modelling (confusion matrix, dll)
- README.txt      : File ini

CARA MEMBUKA
------------
1. Ekstrak SELURUH isi ZIP ke dalam satu folder.
2. Klik dua kali "index.html" (landing page).
3. Klik tombol "Buka Dashboard Analisis" untuk masuk ke dashboard.
4. Saat pertama dibuka butuh INTERNET (Chart.js & font dari CDN).
   Tanpa internet: teks & gambar tetap muncul, hanya grafik
   interaktif yang kosong.

PERUBAHAN SESUAI PERMINTAAN
---------------------------
- Landing page dan dashboard kini DIPISAH (2 file berbeda).
- Navigasi memakai TULISAN, bukan simbol/emoji — agar tidak bingung.
- Semua angka & grafik kini memakai DATA ASLI hasil scraping,
  bukan data dummy lagi.

MODELLING YANG DILAKUKAN
------------------------
- Algoritma : Multinomial Naive Bayes (dibangun dari nol)
- Tugas     : Klasifikasi sentimen ulasan (negatif vs positif)
- Data      : ulasan aplikasi fintech (Google Play)
- Output    : Accuracy, Precision, Recall, F1, Confusion Matrix,
              kata penanda sentimen, analisis perilaku galbay.

MENGOLAH ULANG DATA
-------------------
File analisis: scripts/analyze.py (Python: pandas, numpy, matplotlib).
Jalankan ulang untuk memperbarui data.js & assets/ bila data baru
tersedia:  python scripts/analyze.py

SUMBER DATA
-----------
Google Play Reviews, Forum Kaskus, Berita & siaran pers OJK.
Tahap lanjut: media sosial (TikTok/IG/X), Google Trends, marketplace.
