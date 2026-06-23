"""API logic untuk Skor Risiko Galbay dan Simulasi Cicilan.

Logika ini terpisah dari template agar:
- Mudah di-swap dengan ML model asli saat sudah siap
- Mudah di-test secara independen
- Versioned (saat ini: rule-based-v1)

Saat modeling tim sudah selesai, cukup:
1. Buat function `calculate_score_ml(inputs)` yang return format sama
2. Ganti pemanggilan di `calculate_score()` di bawah
3. Update `MODEL_VERSION` constant
"""
from __future__ import annotations

# =================================================================
# VERSION
# =================================================================
MODEL_VERSION = "rule-based-v1"
DISCLAIMER = "Demo Prototype — Skor berbasis rule-based dari insight data 349K ulasan Google Play. Model ML asli menyusul."


# =================================================================
# SKOR RISIKO GALBAY — Rule-based scoring
# =================================================================
# Bobot risiko per faktor (total max ~135, di-cap ke 100):
# - pinjol: 20, paylater: 10, e-wallet: 5, bank digital: 3
# - utang: 0 / 10 / 20 / 30
# - self reward 1-3: 5, 4-6: 15, 7+: 25
# - telat bayar: 0 / 15 / 25
# - debt collector: 0 / 25
# - feeling: 0 / 10 / 15

APP_RISK_WEIGHTS = {
    "pinjol": 20,
    "paylater": 10,
    "ewallet": 5,
    "bank": 3,
}

UTANG_RISK = {"0": 0, "lt5": 10, "5to20": 20, "gt20": 30}
TELAT_RISK = {"0": 0, "1": 15, "2": 25}
DC_RISK = {"0": 0, "1": 25}
FEELING_RISK = {"0": 0, "1": 10, "2": 15}

CATEGORY_LABELS = {
    "aman": {
        "name": "AMAN",
        "desc": "Keuangan digital kamu sehat. Pertahankan pola ini!",
    },
    "waspada": {
        "name": "WASPADA",
        "desc": "Ada tanda-tanda risiko. Mulai hati-hati dan evaluasi kebiasaan.",
    },
    "bahaya": {
        "name": "BAHAYA",
        "desc": "Risiko galbay tinggi. Butuh intervensi dan perubahan perilaku segera.",
    },
}

RECOMMENDATIONS = {
    "pinjol": "<strong>Hindari pinjol baru.</strong> Prioritaskan melunasi yang ada. Cek modul <em>Cara Recovery dari Galbay</em>.",
    "paylater": "<strong>Kurangi paylater.</strong> Bayar penuh setiap bulan, jangan cuma cicilan minimum.",
    "ewallet": "<strong>Monitor saldo &amp; transaksi.</strong> Pastikan tidak ada auto-debit yang lupa.",
    "bank": "<strong>Pantau limit kredit.</strong> Jangan pakai >30% limit untuk jaga skor kredit.",
    "utang": "<strong>Buat rencana pembayaran.</strong> Prioritaskan utang dengan bunga tertinggi (avalanche method).",
    "selfreward": "<strong>Tunda checkout 24 jam.</strong> Gunakan aturan \"tidur dulu sebelum bayar\". Coba Simulasi Cicilan sebelum deal.",
    "telat": "<strong>Setel auto-debit.</strong> Aktifkan pengingat tagihan H-3. Keterlambatan = biaya tambahan yang memberatkan.",
    "dc": "<strong>Jangan hindari, negosiasikan.</strong> Lihat modul <em>Cara Negosiasi dengan DC</em>. Kamu punya hak sebagai borrower.",
    "feeling": "<strong>Jangan abaikan sinyal.</strong> Stress finansial itu nyata. Pertimbangkan sesi konseling atau modul <em>Habit Building</em>.",
}


def calculate_score(inputs: dict) -> dict:
    """Hitung Skor Risiko Galbay.

    Args:
        inputs: dict dengan keys: apps (list), utang (str), selfreward (int),
                telat (str), dc (str), feeling (str)

    Returns:
        dict dengan: score, category, category_label, description,
                     recommendations, model_version, disclaimer
    """
    apps = inputs.get("apps", []) or []
    utang = str(inputs.get("utang", "0"))
    selfreward = int(inputs.get("selfreward", 3))
    telat = str(inputs.get("telat", "0"))
    dc = str(inputs.get("dc", "0"))
    feeling = str(inputs.get("feeling", "0"))

    risk = 0
    factors = []

    # 1. Apps
    for app in apps:
        r = APP_RISK_WEIGHTS.get(app, 0)
        risk += r
        if r > 0:
            factors.append({"type": app, "weight": r})

    # 2. Utang
    ur = UTANG_RISK.get(utang, 0)
    risk += ur
    if ur > 0:
        factors.append({"type": "utang", "weight": ur})

    # 3. Self reward
    if selfreward <= 3:
        sr = 5
    elif selfreward <= 6:
        sr = 15
    else:
        sr = 25
    risk += sr
    if sr > 5:
        factors.append({"type": "selfreward", "weight": sr})

    # 4. Telat
    tr = TELAT_RISK.get(telat, 0)
    risk += tr
    if tr > 0:
        factors.append({"type": "telat", "weight": tr})

    # 5. DC
    dcr = DC_RISK.get(dc, 0)
    risk += dcr
    if dcr > 0:
        factors.append({"type": "dc", "weight": dcr})

    # 6. Feeling
    fr = FEELING_RISK.get(feeling, 0)
    risk += fr
    if fr > 0:
        factors.append({"type": "feeling", "weight": fr})

    # Cap 0-100
    score = min(100, max(0, round(risk)))
    category = "aman" if score <= 30 else ("waspada" if score <= 60 else "bahaya")
    cat = CATEGORY_LABELS[category]

    # Top 3 recommendations by weight
    top3 = sorted(factors, key=lambda f: f["weight"], reverse=True)[:3]
    recs = [RECOMMENDATIONS.get(f["type"], "Pertahankan perilaku baik.") for f in top3]
    if not recs:
        recs = ["Pertahankan perilaku baik dan terus monitor keuangan digital kamu."]

    return {
        "score": score,
        "category": category,
        "category_label": cat["name"],
        "description": cat["desc"],
        "recommendations": recs,
        "model_version": MODEL_VERSION,
        "disclaimer": DISCLAIMER,
    }


# =================================================================
# SIMULASI CICILAN
# =================================================================
def calculate_simulation(nominal: float, bunga_pct: float, tenor: int, admin: float) -> dict:
    """Hitung simulasi cicilan.

    Args:
        nominal: jumlah pinjaman (Rp)
        bunga_pct: bunga per bulan (%)
        tenor: tenor dalam bulan
        admin: biaya admin (Rp)

    Returns:
        dict dengan: cicilan, total_bunga, total_bayar, bunga_efektif_tahunan,
                     warning, tip, valid
    """
    # Validasi
    errors = []
    if nominal is None or nominal < 0:
        errors.append("nominal harus >= 0")
    if bunga_pct is None or bunga_pct < 0:
        errors.append("bunga_pct harus >= 0")
    if tenor is None or tenor < 1:
        errors.append("tenor harus >= 1")
    if admin is None or admin < 0:
        errors.append("admin harus >= 0")

    if errors:
        return {"valid": False, "errors": errors}

    # Hitung
    total_bunga = nominal * (bunga_pct / 100) * tenor
    total_bayar = nominal + total_bunga + admin
    cicilan = total_bayar / tenor if tenor > 0 else 0
    bunga_efektif = (total_bunga / nominal * (12 / tenor) * 100) if nominal > 0 and tenor > 0 else 0

    # Warning & tip
    warning = None
    if bunga_efektif > 100:
        warning = (
            f"Bunga efektif {bunga_efektif:.0f}%/tahun — "
            f"{(bunga_efektif / 12):.0f}x lipat KTA bank (~12%). "
            f"Sangat memberatkan. Pertimbangkan opsi lain."
        )
        tip = "Bunga >100%/tahun = predatory lending. Coba negosiasi tenor lebih panjang atau cari alternatif KTA bank."
    elif bunga_efektif > 36:
        warning = (
            f"Bunga efektif {bunga_efektif:.0f}%/tahun — "
            f"di atas rata-rata KTA bank (12-18%). Hati-hati."
        )
        tip = "Masih dalam batas wajar tapi bisa dinegosiasi. Bandingkan dengan KTA bank sebelum commit."
    elif bunga_efektif > 18:
        tip = "Bunga dalam batas wajar. Pastikan tenor sesuai kemampuan bayar bulanan."
    else:
        tip = "Bunga rendah. Pastikan tidak ada biaya tersembunyi lain (asuransi, provisi)."

    return {
        "valid": True,
        "nominal": nominal,
        "bunga_pct": bunga_pct,
        "tenor": tenor,
        "admin": admin,
        "cicilan": round(cicilan),
        "total_bunga": round(total_bunga),
        "total_bayar": round(total_bayar),
        "bunga_efektif_tahunan": round(bunga_efektif, 1),
        "warning": warning,
        "tip": tip,
    }


# =================================================================
# WAITLIST (demo, simpan ke JSON file)
# =================================================================
import json
import os
from pathlib import Path
from datetime import datetime

WAITLIST_FILE = Path("data/waitlist.json")


def add_to_waitlist(email: str, package: str = "general") -> dict:
    """Tambah email ke waitlist (demo, simpan ke JSON file)."""
    if not email or "@" not in email:
        return {"valid": False, "error": "Email tidak valid"}

    WAITLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if WAITLIST_FILE.exists():
        try:
            data = json.loads(WAITLIST_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = []
    else:
        data = []

    # Cegah duplikat
    if any(entry.get("email") == email for entry in data):
        return {"valid": True, "duplicate": True, "total": len(data)}

    entry = {
        "email": email,
        "package": package,
        "timestamp": datetime.now().isoformat() + "Z",
    }
    data.append(entry)
    WAITLIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"valid": True, "duplicate": False, "total": len(data)}
