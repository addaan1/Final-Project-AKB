@echo off
REM ============================================================
REM Galbay Predictor — Full Multi-Source Scraping Pipeline
REM Target: 700K rows dari 9 source (skip Twitter/X)
REM ============================================================
setlocal enabledelayedexpansion

REM --- Konfigurasi ---
set VENV=.venv\Scripts\activate.bat
set SCRAPER_SLEEP=1.5
set MAX_PAGES=2
set MAX_PER_QUERY=60
set MAX_PLAY_PER_APP=25000
set TIKTOK_VIDEOS=30
set TIKTOK_COMMENTS=50
set FORUM_THREADS=100
set FORUM_POSTS=100
set YOUTUBE_VIDEOS=20
set YOUTUBE_COMMENTS=50
set NEWS_ARTICLES=50

echo === Galbay Predictor Multi-Source Pipeline ===
echo.

REM --- Aktivasi virtualenv ---
if exist "%VENV%" (
    call %VENV%
) else (
    echo [WARN] .venv tidak ditemukan, pakai global Python
)

REM --- Set env untuk polite rate-limit ---
set SCRAPER_SLEEP_SECONDS=%SCRAPER_SLEEP%

REM --- 1) Google Play (backbone, 349K -> 500K) ---
echo.
echo === [1/9] Google Play reviews (backbone, target 500K) ===
python -m scraper.runner -s play_reviews -m all --max-per-app %MAX_PLAY_PER_APP% --count %MAX_PLAY_PER_APP%
if errorlevel 1 echo [WARN] Play gagal, lanjut source berikutnya.

REM --- 2) TikTok komentar (target 50K) ---
echo.
echo === [2/9] TikTok komentar (target 50K) ===
python -m scraper.runner -s tiktok --max-videos %TIKTOK_VIDEOS% --max-comments %TIKTOK_COMMENTS%
if errorlevel 1 echo [WARN] TikTok gagal, lanjut.

REM --- 3) Forum Kaskus + Reddit (target 10K) ---
echo.
echo === [3/9] Forum Kaskus + Reddit (target 10K) ===
python -m scraper.runner -s forum --max-threads %FORUM_THREADS% --max-posts %FORUM_POSTS%
if errorlevel 1 echo [WARN] Forum gagal, lanjut.

REM --- 4) YouTube komentar (target 5K) ---
echo.
echo === [4/9] YouTube komentar (target 5K) ===
python -m scraper.runner -s youtube --max-videos %YOUTUBE_VIDEOS% --max-comments %YOUTUBE_COMMENTS%
if errorlevel 1 echo [WARN] YouTube gagal, lanjut.

REM --- 5) Marketplace Shopee + Tokopedia (target 50K, BARU) ---
echo.
echo === [5/9] Marketplace Shopee + Tokopedia (target 50K) ===
python -m scraper.runner -s marketplace --marketplace both --marketplace-pages %MAX_PAGES%
if errorlevel 1 echo [WARN] Marketplace gagal, lanjut.

REM --- 6) News OJK + media (target 1K) ---
echo.
echo === [6/9] News OJK + media (target 1K) ===
python -m scraper.runner -s ojk_news --max-articles %NEWS_ARTICLES%
if errorlevel 1 echo [WARN] News gagal, lanjut.

REM --- 7) Blog Medium + Dailysia (target 500) ---
echo.
echo === [7/9] Blog Medium + Dailysia (target 500) ===
python -m scraper.runner -s blogs
if errorlevel 1 echo [WARN] Blog gagal, lanjut.

REM --- 8) AppStore iOS (target 30K) ---
echo.
echo === [8/9] AppStore iOS (target 30K) ===
python -m scraper.runner -s appstore -m all
if errorlevel 1 echo [WARN] AppStore gagal, lanjut.

REM --- 9) Google Trends (time-series 12 bulan) ---
echo.
echo === [9/9] Google Trends (time-series 12 bulan) ===
python -m scraper.runner -s google_trends
if errorlevel 1 echo [WARN] Trends gagal, lanjut.

REM --- Summary ---
echo.
echo === RINGKASAN UKURAN DATA ===
python -c "import os, glob; total=0; [print(f'  {os.path.basename(f):50s} {os.path.getsize(f)/1024/1024:>8.2f} MB') or (total := total + os.path.getsize(f)/1024/1024) for f in sorted(glob.glob('data/raw/*')) if not os.path.basename(f).startswith('.')]; print(f'  TOTAL: {total:.2f} MB')"

echo.
echo === Pipeline selesai. Lanjut ke FASE 3 (processing) ===
endlocal
