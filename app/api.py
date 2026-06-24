"""API logic untuk Skor Risiko Galbay, Simulasi Cicilan, Pinjol Checker,
Debt Planner, Recovery Roadmap, dan FAQ Chatbot (NLP-like).

Logika ini terpisah dari template agar:
- Mudah di-swap dengan ML model asli saat sudah siap
- Mudah di-test secara independen
- Versioned (saat ini: rule-based-v1, faq-nlp-v2)

Saat modeling tim sudah selesai, cukup:
1. Buat function `calculate_score_ml(inputs)` yang return format sama
2. Ganti pemanggilan di `calculate_score()` di bawah
3. Update `MODEL_VERSION` constant
"""
from __future__ import annotations

import json
import os
import re
import difflib
from pathlib import Path
from datetime import datetime

# =================================================================
# VERSION
# =================================================================
MODEL_VERSION = "rule-based-v1"
DISCLAIMER = "Demo Prototype — Skor berbasis rule-based dari insight data 602K multi-source (Play + OJK + Forum + Blog + YouTube + Threads + Trends). Model ML asli menyusul."


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
WAITLIST_FILE = Path("data/waitlist.json")


def add_to_waitlist(email: str, package: str = "general", name: str = "") -> dict:
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
        "name": name or "",
        "package": package,
        "timestamp": datetime.now().isoformat() + "Z",
    }
    data.append(entry)
    WAITLIST_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"valid": True, "duplicate": False, "total": len(data)}


# =================================================================
# 1. PINJOL BLACKLIST CHECKER
# =================================================================
PINJOL_DB_FILE = Path("data/pinjol_database.json")


def _load_pinjol_db() -> dict:
    """Load pinjol database."""
    if not PINJOL_DB_FILE.exists():
        return {"legal": [], "ilegal_sample": []}
    try:
        return json.loads(PINJOL_DB_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"legal": [], "ilegal_sample": []}


def check_pinjol_status(app_name: str) -> dict:
    """Cek apakah pinjol legal (terdaftar OJK) atau tidak.

    Args:
        app_name: nama aplikasi pinjol (case-insensitive, partial match)

    Returns:
        dict dengan: found, status, category, ojk_license, message, recommendations
    """
    if not app_name or not app_name.strip():
        return {"valid": False, "error": "Nama app kosong"}

    db = _load_pinjol_db()
    name_lower = app_name.lower().strip()

    def _match(app, query):
        """Match by name + aliases (case-insensitive, exact or partial)."""
        candidates = [app["name"]] + app.get("aliases", [])
        candidates_lower = [c.lower() for c in candidates]
        # Exact match
        if query in candidates_lower:
            return "exact"
        # Partial match
        for c in candidates_lower:
            if query in c or c in query:
                return "partial"
        return None

    # Exact match di legal
    for app in db.get("legal", []):
        m = _match(app, name_lower)
        if m == "exact":
            return {
                "valid": True,
                "found": True,
                "status": "legal",
                "status_label": "TERDAFTAR OJK",
                "name": app["name"],
                "category": app.get("category", ""),
                "ojk_license": app.get("ojk_license", ""),
                "playstore_id": app.get("playstore_id", ""),
                "message": f"{app['name']} TERDAFTAR di OJK dan legal beroperasi di Indonesia. Aman untuk digunakan.",
                "recommendations": [
                    "Pastikan baca bunga & biaya admin sebelum deal",
                    "Hindari pinjam lebih dari kemampuan bayar",
                    "Setel auto-debit untuk bayar tepat waktu",
                ],
                "disclaimer": "Status berdasarkan database internal kami. Untuk konfirmasi final, cek langsung di ojk.go.id",
            }

    # Partial match di legal
    for app in db.get("legal", []):
        m = _match(app, name_lower)
        if m == "partial":
            return {
                "valid": True,
                "found": True,
                "status": "legal_partial",
                "status_label": "MUNGKIN TERDAFTAR",
                "name": app["name"],
                "category": app.get("category", ""),
                "message": f"Mungkin yang Anda maksud: {app['name']} (terdaftar OJK). Periksa kembali nama aplikasi.",
                "recommendations": [
                    f"Verifikasi nama lengkap: {app['name']}",
                    "Buka website OJK untuk konfirmasi",
                ],
                "disclaimer": "Pencocokan parsial. Pastikan nama app benar.",
            }

    # Match di ilegal sample
    for app in db.get("ilegal_sample", []):
        m = _match(app, name_lower)
        if m in ("exact", "partial"):
            return {
                "valid": True,
                "found": True,
                "status": "ilegal",
                "status_label": "TIDAK TERDAFTAR / ILEGAL",
                "name": app["name"],
                "message": f"{app['name']} TIDAK TERDAFTAR di database OJK. Berisiko tinggi.",
                "recommendations": [
                    "JANGAN pinjam dari app ini",
                    "Laporkan ke OJK di 157 atau ojk.go.id",
                    "Hapus app dari HP untuk keamanan data",
                    "Cek alternatif legal di database kami",
                ],
                "disclaimer": "Daftar pinjol ilegal di-update berkala. Verifikasi langsung ke OJK.",
            }

    # Tidak ditemukan di database
    return {
        "valid": True,
        "found": False,
        "status": "unknown",
        "status_label": "TIDAK DIKENAL",
        "name": app_name,
        "message": f"'{app_name}' tidak ditemukan di database kami. Belum tentu legal/ilegal — perlu dicek manual.",
        "recommendations": [
            "Cek langsung di ojk.go.id (Sistem SLIK)",
            "Hindari app tanpa izin OJK yang jelas",
            "Waspadai app dengan bunga >30%/bulan",
            "Baca review Play Store, perhatikan keluhan DC",
        ],
        "disclaimer": "Database kami terbatas 24 app legal + 3 contoh ilegal. Untuk pinjol di luar ini, cek langsung ke OJK.",
    }


# =================================================================
# 2. DEBT SNOWBALL / AVALANCHE PLANNER
# =================================================================
def calculate_debt_planner(debts: list, extra_payment: float = 0) -> dict:
    """Hitung strategi Snowball vs Avalanche untuk bayar multiple utang.

    Args:
        debts: list of dict dengan keys: name, balance, bunga_pct, min_payment
        extra_payment: extra payment per bulan (untukåŠ é€Ÿ lunas)

    Returns:
        dict dengan: snowball, avalanche, comparison
    """
    if not debts or not isinstance(debts, list):
        return {"valid": False, "error": "Daftar utang kosong"}

    # Normalize data
    normalized = []
    for d in debts:
        try:
            normalized.append({
                "name": str(d.get("name", "Utang")).strip(),
                "balance": float(d.get("balance", 0)),
                "bunga_pct": float(d.get("bunga_pct", 0)),
                "min_payment": float(d.get("min_payment", 0)),
            })
        except (ValueError, TypeError):
            continue

    if not normalized:
        return {"valid": False, "error": "Format data utang tidak valid"}

    # Hitung total
    total_debt = sum(d["balance"] for d in normalized)
    total_min = sum(d["min_payment"] for d in normalized)
    total_interest_simple = sum(d["balance"] * d["bunga_pct"] / 100 for d in normalized)

    def simulate(strategy: str, debt_list: list) -> dict:
        """Simulate strategy: 'snowball' (smallest first) atau 'avalanche' (highest rate first)."""
        # Sort
        if strategy == "snowball":
            sorted_debts = sorted(debt_list, key=lambda d: d["balance"])
        else:  # avalanche
            sorted_debts = sorted(debt_list, key=lambda d: -d["bunga_pct"])

        debts = [{**d, "remaining": d["balance"], "paid_off_month": None} for d in sorted_debts]
        monthly_budget = max(total_min, 0) + max(extra_payment, 0)
        month = 0
        total_paid_interest = 0
        history = []

        while any(d["remaining"] > 0 for d in debts) and month < 600:  # max 50 tahun
            month += 1
            # Tambah bunga ke semua utang
            for d in debts:
                if d["remaining"] > 0:
                    interest = d["remaining"] * d["bunga_pct"] / 100
                    d["remaining"] += interest
                    total_paid_interest += interest

            # Bayar minimum untuk semua
            for d in debts:
                if d["remaining"] > 0:
                    pay = min(d["min_payment"], d["remaining"])
                    d["remaining"] -= pay

            # Alokasikan sisa budget ke target (snowball: smallest remaining; avalanche: highest rate)
            available = monthly_budget - sum(min(d["min_payment"], d["remaining"]) if d["remaining"] > 0 else 0 for d in debts)
            for d in debts:
                if d["remaining"] <= 0:
                    if d["paid_off_month"] is None:
                        d["paid_off_month"] = month - 1
                    continue
                # Alokasikan extra ke target (first debt belum lunas)
                extra_pay = min(available, d["remaining"])
                d["remaining"] -= extra_pay
                available -= extra_pay
                if available <= 0:
                    break

            # Check paid off
            for d in debts:
                if d["remaining"] <= 0 and d["paid_off_month"] is None:
                    d["paid_off_month"] = month

            # Simpan history (per 6 bulan)
            if month % 6 == 0 or month == 1:
                history.append({
                    "month": month,
                    "total_remaining": sum(d["remaining"] for d in debts),
                    "debts_paid": sum(1 for d in debts if d["paid_off_month"] is not None),
                })

        return {
            "strategy": strategy,
            "strategy_label": "Snowball (Bayar Terkecil Dulu)" if strategy == "snowball" else "Avalanche (Bayar Bunga Tertinggi Dulu)",
            "months_to_debt_free": month,
            "total_interest_paid": round(total_paid_interest, 0),
            "order": [d["name"] for d in sorted_debts],
            "paid_off_schedule": {d["name"]: d["paid_off_month"] for d in debts},
            "history": history[-10:],  # last 10 checkpoints
        }

    snowball = simulate("snowball", normalized)
    avalanche = simulate("avalanche", normalized)

    # Recommendation
    if avalanche["total_interest_paid"] < snowball["total_interest_paid"]:
        recommendation = "avalanche"
        reason = f"Avalanche menghemat Rp {snowball['total_interest_paid'] - avalanche['total_interest_paid']:,.0f} bunga."
    else:
        recommendation = "snowball"
        reason = "Snowball lebih cocok untuk motivasi (bayar terkecil dulu = quick win)."

    return {
        "valid": True,
        "debts_input": normalized,
        "total_debt": round(total_debt, 0),
        "total_min_payment": round(total_min, 0),
        "extra_payment": extra_payment,
        "snowball": snowball,
        "avalanche": avalanche,
        "recommendation": recommendation,
        "reason": reason,
        "disclaimer": "Simulasi dengan bunga simple (flat). Realita bisa lebih kompleks karena bunga majemuk.",
    }

# =================================================================
# 4. GALBAY RECOVERY ROADMAP — 30/60/90 hari
# =================================================================
def generate_recovery_roadmap(conditions: dict) -> dict:
    """Generate roadmap personal keluar dari galbay 30/60/90 hari.

    Args:
        conditions: dict dengan keys: total_utang, income_bulanan, sudah_dc, hari_telat

    Returns:
        dict dengan roadmap 30/60/90 hari + rekomendasi mingguan
    """
    try:
        total_utang = float(conditions.get("total_utang", 0))
        income = float(conditions.get("income_bulanan", 0))
        sudah_dc = conditions.get("sudah_dc", False)
        hari_telat = int(conditions.get("hari_telat", 0))
    except (ValueError, TypeError):
        return {"valid": False, "error": "Format input tidak valid"}

    if income <= 0:
        return {"valid": False, "error": "Income harus > 0"}
    if total_utang < 0:
        return {"valid": False, "error": "Total utang harus >= 0"}

    debt_to_income = (total_utang / (income * 12)) if income > 0 else 0
    severity = "kritis" if hari_telat > 30 or debt_to_income > 3 else ("tinggi" if hari_telat > 7 or debt_to_income > 1.5 else "sedang")

    if severity == "kritis":
        week1_2 = [
            "HARI 1-3: Kumpulkan semua info utang (pinjol, nominal, bunga, tenor, tgl jatuh tempo) di spreadsheet/notes",
            "HARI 1-3: Stop pinjam baru. Hapus app pinjol dari HP (mengurangi godaan)",
            "HARI 4-7: Buka semua email/SMS notifikasi tagihan. Catat tanggal jatuh tempo & total tagihan",
            "HARI 4-7: Cek skor OJK: ajukan SLIK di bank terdekat (gratis, butuh e-KTP)",
            "HARI 8-14: Negosiasi restrukturisasi ke pinjol utama (mulai dari bunga tertinggi)",
            "HARI 8-14: Cek apakah ada aset yang bisa dijual (motor, gadget, barang tak terpakai)",
            "HARI 8-14: Buka rekening terpisah khusus bayar utang. Setel auto-debit 30% income",
            "HARI 15-21: Mulai kerja sampingan (ojol, freelance, jualan online) — target Rp 500K-1jt/bln",
            "HARI 22-28: Bayar minimal semua utang tepat waktu (jangan telat lagi)",
            "HARI 22-28: Catat progress di spreadsheet: sisa utang, bulan lunas estimasi",
        ]
        week3_4 = [
            "MINGGU 5-6: Tutup utang paling kecil (snowball) — dapat motivasi psikologis",
            "MINGGU 5-6: Review kerja sampingan, tambah jam kalau bisa",
            "MINGGU 7-8: Negosiasi ulang ke DC yang agresif (pakai template AI Coach)",
            "MINGGU 7-8: Kalau punya kartu kredit, pertimbangkan balance transfer ke bunga lebih rendah",
            "MINGGU 7-8: Cari konselor keuangan (YLBHI, OJK, atau LSM lokal)",
            "Akhir bulan 2: Target turun 10-15% dari total utang",
        ]
        month3 = [
            "Bulan 3 penuh: 2-3 utang terbayar (yang terkecil). Momentum psikologis besar",
            "Bulan 3: Negosiasi debt consolidation (gabung beberapa utang jadi 1)",
            "Bulan 3: Mulai bangun emergency fund kecil (Rp 200K/bln)",
            "Akhir bulan 3: Total utang turun 25-30%",
            "Target bulan 3: Skor Risiko Galbay turun ke 'Waspada' (bukan 'Bahaya')",
        ]
    elif severity == "tinggi":
        week1_2 = [
            "HARI 1-3: Audit semua utang & catat di spreadsheet (nama, nominal, bunga, tenor)",
            "HARI 1-7: Stop pinjam baru. Evaluasi cash flow bulanan (income vs expense)",
            "HARI 8-14: Setel auto-debit minimum payment 1 hari sebelum jatuh tempo",
            "HARI 8-14: Cek apakah ada pengeluaran yang bisa di-cut (streaming, langganan, jajan)",
            "HARI 15-21: Bayar utang bunga tertinggi lebih besar (Avalanche) atau terkecil (Snowball)",
            "HARI 22-28: Mulai nabung emergency fund (walaupun kecil, Rp 100-200K/bln)",
        ]
        week3_4 = [
            "MINGGU 5-6: Tutup 1-2 utang terkecil (Snowball) untuk motivasi",
            "MINGGU 7-8: Review & adjust strategi berdasarkan progress",
            "Akhir bulan 2: Total utang turun 10-15%",
        ]
        month3 = [
            "Bulan 3: 2-3 utang terbayar",
            "Bulan 3: Bangun emergency fund 1x pengeluaran bulanan",
            "Bulan 3: Mulai investasi kecil (reksa dana pasar uang / deposito)",
            "Target: Skor Risiko turun ke 'Aman'",
        ]
    else:  # sedang
        week1_2 = [
            "HARI 1-7: Review & catat semua utang",
            "HARI 8-14: Setel auto-debit tepat waktu",
            "HARI 15-21: Bayar extra ke utang bunga tertinggi",
            "HARI 22-28: Mulai nabung emergency fund (target 1x gaji)",
        ]
        week3_4 = [
            "MINGGU 5-6: Tutup 1 utang terkecil (Snowball)",
            "MINGGU 7-8: Tinjau ulang budget bulanan",
            "Akhir bulan 2: Total utang turun 5-10%",
        ]
        month3 = [
            "Bulan 3: Pertahankan disiplin bayar tepat waktu",
            "Bulan 3: Tambah emergency fund + investasi kecil",
            "Target: Skor Risiko 'Aman'",
        ]

    return {
        "valid": True,
        "severity": severity,
        "severity_label": {"kritis": "KRITIS", "tinggi": "TINGGI", "sedang": "SEDANG"}[severity],
        "conditions": {
            "total_utang": total_utang,
            "income_bulanan": income,
            "debt_to_income_ratio": round(debt_to_income, 2),
            "sudah_dc": sudah_dc,
            "hari_telat": hari_telat,
        },
        "roadmap": {
            "minggu_1_2": week1_2,
            "minggu_3_4": week3_4,
            "bulan_3": month3,
        },
        "success_metrics": {
            "target_bulan_1": "Stop new debt. Tepat waktu bayar minimum.",
            "target_bulan_2": "Turun 10-15% dari total utang. 1-2 utang terbayar.",
            "target_bulan_3": "Turun 25-30% dari total. Skor Risiko turun ke Aman/Waspada.",
        },
        "disclaimer": "Roadmap ini panduan umum. Setiap situasi unik. Konsultasi dengan konselor keuangan profesional untuk kasus kompleks.",
    }



# =================================================================
# 5. FAQ CHATBOT (Phase 2: NLP-like, 35+ intents, 8 modules)
# =================================================================
# Phase 2 enhancements (vs Phase 1 rule-based):
# - Synonym resolution: "pinjol" matches "pinjaman online", "online", etc.
# - Typo tolerance: difflib fallback for partial token matches
# - Multi-intent: returns top 3 intents, allows follow-up questions
# - Sentiment detection: stressed/anxious/confused/positive/curious
# - Time-based greeting: pagi/siang/malam
# - Markdown answer: **bold** *italic* `code` lists, links
# - Context-aware: name handling, page context tips
# Backward compatible with v1: same _match_faq_intent(text) signature.

import difflib
from datetime import datetime as _dt

CHATBOT_MODEL_VERSION = "faq-nlp-v2"
CHATBOT_DISCLAIMER = (
    "Galbay AI Coach adalah asisten rule-based (FAQ NLP v2). "
    "Untuk kasus kompleks, konsultasi konselor keuangan profesional. "
    "Bukan pengganti nasihat hukum/medis."
)

# -----------------------------------------------------------------
# Module metadata (8 modules)
# -----------------------------------------------------------------
CHATBOT_MODULES = {
    "M1_galbay_basics": {
        "name": "Galbay Basics",
        "icon": "📚",
        "description": "Pengertian galbay, skor risiko, simulasi cicilan",
    },
    "M2_pinjol": {
        "name": "Pinjol & Legalitas",
        "icon": "⚖️",
        "description": "OJK legal, pinjol ilegal, bunga wajar",
    },
    "M3_debt_strategy": {
        "name": "Strategi Bayar Utang",
        "icon": "💰",
        "description": "Snowball, Avalanche, negosiasi cicilan",
    },
    "M4_dc_negotiation": {
        "name": "Negosiasi DC",
        "icon": "🤝",
        "description": "Cara negosiasi, hak borrower, template",
    },
    "M5_recovery": {
        "name": "Recovery Roadmap",
        "icon": "🛤️",
        "description": "30/60/90 hari keluar dari galbay",
    },
    "M6_legal_rights": {
        "name": "Hak Hukum",
        "icon": "🛡️",
        "description": "UU PDP, ITE, OJK, pelaporan ilegal",
    },
    "M7_app_rec": {
        "name": "Rekomendasi App",
        "icon": "📱",
        "description": "App aman, fitur premium, diskon",
    },
    "M8_mental_health": {
        "name": "Mental Health",
        "icon": "💚",
        "description": "Stress finansial, konseling, support",
    },
}

# -----------------------------------------------------------------
# Synonym map (canonical -> variants)
# -----------------------------------------------------------------
SYNONYMS = {
    "galbay": ["galbay", "gali bayar", "gali lubang", "tutup lubang", "lubang", "pinjaman", "utang", "hutang", "tagihan", "bayar"],
    "pinjol": ["pinjol", "pinjaman online", "online", "p2p", "lending", "pinjam", "kredit online", "cash loan"],
    "paylater": ["paylater", "pay later", "bayar nanti", "cicilan tanpa kartu", "bca paylater", "shopee paylater", "kredivo", "akulaku"],
    "ewallet": ["e wallet", "e-wallet", "dompet digital", "gopay", "ovo", "dana", "shopeepay", "linkaja"],
    "dc": ["dc", "debt collector", "debtcol", "penagih", "tagih", "nagih", "penagihan", "collector"],
    "cicilan": ["cicilan", "angsuran", "installment", "bulanan", "per bulan", "tenor"],
    "bunga": ["bunga", "interest", "rate", "persen", "%", "biaya", "fee"],
    "skor": ["skor", "score", "nilai", "rating", "kategori", "level"],
    "snowball": ["snowball", "bola salju", "metode bola salju", "kecil dulu", "utang terkecil"],
    "avalanche": ["avalanche", "longsor", "metode avalanche", "bunga tertinggi", "bunga besar dulu"],
    "ojk": ["ojk", "otoritas jasa keuangan", "regulator", "satu", "slik", "bi checking", "slik OJK"],
    "ilegal": ["ilegal", "illegal", "abal", "palsu", "bodong", "tak terdaftar", "gelap", "haram"],
    "ilegal_act": ["ilegal", "melanggar", "ancam", "intimidasi", "teror", "kekerasan", "sebar data"],
    "negosiasi": ["nego", "negosiasi", "tawar", "keringanan", "restrukturisasi", "restruk"],
    "premium": ["premium", "berbayar", "pro", "upgrade", "paket"],
    "data": ["data", "informasi", "dataset", "602", "602000", "sumber", "multi source"],
    "recovery": ["recovery", "pemulihan", "keluar", "selesaikan", "lunas", "bebas", "sembuh"],
    "selfreward": ["self reward", "reward", "hadiah", "gift", "traktir", "self care"],
    "konseling": ["konseling", "konsultan", "psikolog", "temen curhat", "curhat", "cerita"],
    "emergency": ["darurat", "emergency", "tolong", "bantuan", "sekarang", "malam ini", "hari ini"],
    "template": ["template", "contoh", "script", "teks", "format", "chat", "kirim"],
    "aplikasi": ["aplikasi", "app", "web", "website", "situs"],
    "fee": ["fee", "biaya admin", "admin", "biaya tambahan", "biaya tersembunyi", "potong"],
    "telat": ["telat", "terlambat", "nunggak", "lewat jatuh tempo", "lewat tempo", "denda"],
    "intimidasi": ["intimidasi", "ancam", "takut", "teror", "ganggu keluarga", "foto", "sebar", "aib"],
    "hapus_data": ["hapus data", "hapus info", "sebar data", "sebar aib", "foto aib", "aib"],
    "cuti": ["cuti", "libur", "tunda", "pause", "moratorium"],
    "konsolidasi": ["konsolidasi", "gabung", "satuin", "merge", "refinance"],
    "stop_langganan": ["berhenti", "stop", "uninstall", "hapus app", "tutup akun"],
    "utang_keluarga": ["keluarga", "orang tua", "ortu", "teman", "sodara", "pinjam keluarga"],
    "stress": ["stress", "stres", "cemas", "panik", "khawatir", "takut", "depresi", "bunuh diri", "pusing"],
    "tagihan": ["tagihan", "bills", "jatuh tempo", "due date"],
    "income": ["income", "penghasilan", "gaji", "pendapatan", "duit masuk"],
    "pengeluaran": ["pengeluaran", "expense", "biaya hidup", "shopping", "belanja"],
    "emergency_fund": ["dana darurat", "emergency fund", "tabungan darurat", "cadangan"],
    "tracking": ["tracking", "lacak", "monitor", "cek", "lihat", "progress"],
}


# -----------------------------------------------------------------
# FAQ Knowledge Base (35+ intents)
# -----------------------------------------------------------------
FAQ_KB = [
    # ===== M1: Galbay Basics =====
    {
        "intent": "apa_itu_galbay",
        "module": "M1_galbay_basics",
        "keywords": ["apa", "itu", "galbay", "gali", "bayar", "lubang", "artinya", "definisi", "pengertian"],
        "patterns": ["apa itu galbay", "galbay itu apa", "arti galbay", "gali bayar"],
        "answer": "**Galbay** = *Gali Lubang, Tutup Lubang*. Pola pinjam baru untuk bayar utang lama.\n\nTanda-tanda:\n- Pinjam A untuk bayar B\n- Cicilan tidak turun setelah bayar\n- Cuma bayar minimum, pokok tidak bergerak\n- Stres tiap tanggal jatuh tempo\n\nDi Galbay Predictor, kamu bisa cek **Skor Risiko** gratis untuk tahu seberapa parah kondisi kamu.",
        "suggestions": ["Cek skor risiko", "Pinjol ilegal?", "Cara recovery"],
        "related_actions": [
            {"label": "Hitung Skor Risiko", "href": "/dashboard/ringkasan"},
            {"label": "Pelajari Strategi Bayar", "href": "/dashboard/solusi"},
        ],
    },
    {
        "intent": "apa_itu_skor_risiko",
        "module": "M1_galbay_basics",
        "keywords": ["skor", "risiko", "score", "nilai", "kategori", "level", "aman", "waspada", "bahaya"],
        "patterns": ["apa itu skor risiko", "skor itu apa", "kategori skor"],
        "answer": "**Skor Risiko Galbay** adalah skor 0-100 yang menilai kemungkinan kamué™·å…¥ galbay.\n\n- **Aman (0-30)**: Keuangan sehat, pertahankan\n- **Waspada (31-60)**: Ada tanda risiko, mulai evaluasi\n- **Bahaya (61-100)**: Butuh intervensi segera\n\nSkor dihitung dari: jumlah pinjol, paylater, e-wallet, total utang, telat bayar, dan pola self-reward. [Cek skormu sekarang](/dashboard/ringkasan).",
        "suggestions": ["Cek skor saya", "Bunga wajar?", "Pinjol ilegal?"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },
    {
        "intent": "simulasi_cicilan",
        "module": "M1_galbay_basics",
        "keywords": ["simulasi", "cicilan", "hitung", "kalkulator", "berapa", "bulan"],
        "patterns": ["simulasi cicilan", "hitung cicilan", "kalkulator cicilan"],
        "answer": "**Simulasi Cicilan** bantu kamu hitung total bayar + bunga sebelum deal.\n\nInput: nominal pinjam, bunga (%/tahun), tenor (bulan).\n\nLayanan ini di halaman **[Simulasi Cicilan](/dashboard/produk)**. Gratis, tanpa login tambahan.",
        "suggestions": ["Bunga wajar?", "Cek skor risiko", "Pinjol ilegal?"],
        "related_actions": [
            {"label": "Buka Simulasi", "href": "/dashboard/produk"},
        ],
    },

    # ===== M2: Pinjol =====
    {
        "intent": "pinjol_ilegal",
        "module": "M2_pinjol",
        "keywords": ["pinjol", "ilegal", "illegal", "abal", "palsu", "bodong", "tak terdaftar", "gelap", "haram", "cek", "legal"],
        "patterns": ["apa itu pinjol ilegal", "pinjol ilegal", "cara cek pinjol legal", "cek legalitas pinjol"],
        "answer": "**Pinjol ilegal** = pinjol *tidak terdaftar OJK*. Ciri-ciri:\n- Bunga > 0.8% per hari (> 24% per bulan)\n- Akses kontak, foto, SMS tanpa izin\n- DC agresif, sebar data, intimidasi\n- Tidak ada call center resmi\n\nCara cek legal: **[Pinjol Checker](/dashboard/produk)** atau cek di [SILO OJK](https://www.ojk.go.id/).",
        "suggestions": ["Cek pinjol legal?", "DC agresif", "Lapor pinjol ilegal"],
        "related_actions": [
            {"label": "Cek Legalitas Pinjol", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "cara_cek_pinjol_legal",
        "module": "M2_pinjol",
        "keywords": ["cek", "legal", "ojk", "terdaftar", "sah", "resmi", "silo", "satu"],
        "patterns": ["cara cek pinjol legal", "pinjol aman", "pinjol terdaftar ojk", "cek legalitas"],
        "answer": "3 cara cek legalitas pinjol:\n\n1. **[Pinjol Checker Galbay](/dashboard/produk)** — input nama app, langsung ketahuan\n2. **SILO OJK** ([ojk.go.id](https://www.ojk.go.id/)) — daftar 200+ pinjol resmi\n3. **SLIK** — cek histori kredit kamu (ada pinjol gelap yang nyangkut)\n\n**Red flag**: bunga di atas 0.8%/hari, minta akses kontak sebelum pinjam, tidak ada NPWP/izin OJK.",
        "suggestions": ["Pinjol ilegal?", "Bunga wajar?", "Lapor DC ilegal"],
        "related_actions": [
            {"label": "Buka Pinjol Checker", "href": "/dashboard/produk"},
            {"label": "Ke SILO OJK", "href": "https://www.ojk.go.id/", "external": True},
        ],
    },
    {
        "intent": "bunga_tinggi_normal",
        "module": "M2_pinjol",
        "keywords": ["bunga", "tinggi", "normal", "wajar", "berapa", "persen", "maksimum", "rate"],
        "patterns": ["bunga pinjol berapa", "bunga wajar", "bunga tinggi", "bunga maksimum"],
        "answer": "Bunga pinjol legal (peraturan OJK 2023):\n\n- **Pinjol konvensional**: maks **0.3% per hari** (≤ 10.95% per tahun flat)\n- **Pinjol dengan agunan (KTA)**: maks **24% per tahun**\n- **Pinjol syariah**: margin setara, tidak boleh lebih\n\n**Red flag ilegal**: > 0.8% per hari, atau ada biaya tersembunyi (admin, provisi, denda).\n\nSelalu baca detail sebelum deal. Cek di **[Pinjol Checker](/dashboard/produk)** dulu.",
        "suggestions": ["Pinjol ilegal?", "Simulasi cicilan", "Negosiasi cicilan"],
        "related_actions": [
            {"label": "Simulasi Cicilan", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "paylater_vs_pinjol",
        "module": "M2_pinjol",
        "keywords": ["paylater", "pinjol", "bedanya", "beda", "vs", "mana"],
        "patterns": ["bedanya paylater sama pinjol", "paylater vs pinjol", "paylater apa bedanya"],
        "answer": "**Paylater** = cicilan yang *dibenamkan di e-commerce/platform* (Shopee, Tokopedia, GoPay Later). Limit ditentukan platform, bayar penuh = 0% bunga.\n\n**Pinjol** = pinjaman *tunai* dari platform fintech (Kredivo, Akulaku, Dana Cair). Limit lebih fleksibel, bunga harian.\n\nKeduanya **terdaftar OJK** jika legal. Risiko hampir sama kalau kamu gak bayar. **Bahaya**: kalau bayar minimum terus, bunganya numpuk.\n\nCek apakah app kamu legal di **[Pinjol Checker](/dashboard/produk)**.",
        "suggestions": ["Pinjol ilegal?", "Bunga wajar?", "Snowball vs Avalanche"],
        "related_actions": [
            {"label": "Cek Legalitas", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "hapus_data_diri",
        "module": "M2_pinjol",
        "keywords": ["hapus", "data", "foto", "sebar", "aib", "kontak", "intimidasi", "ancaman"],
        "patterns": ["hapus data pinjol", "pinjol sebar data", "pinjol sebar aib", "hapus foto"],
        "answer": "**Pinjol ilegal sering sebar data/foto kontak**. Ini **melanggar UU PDP No. 27/2022** & **UU ITE No. 19/2016**.\n\nLangkah:\n1. **Screenshot semua bukti** (chat, foto, ancaman)\n2. **Lapor ke OJK** ([ojk.go.id](https://www.ojk.go.id/)) + adukan ke **Kominfo** ([aduankonten.id](https://aduankonten.id))\n3. **Lapor polisi** (cyber crime) untuk ancaman/pemerasan\n4. **Pinjol Checker Galbay** bisa identifikasi legal/ilegal otomatis.\n\nKamu punya hak atas data pribadi. Jangan bayar di bawah ancaman.",
        "suggestions": ["Lapor DC ilegal", "DC agresif", "Hukum pinjol ilegal"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk"},
            {"label": "Lapor Kominfo", "href": "https://aduankonten.id", "external": True},
        ],
    },

    # ===== M3: Debt Strategy =====
    {
        "intent": "snowball_vs_avalanche",
        "module": "M3_debt_strategy",
        "keywords": ["snowball", "avalanche", "vs", "mana", "lebih", "baik", "metode", "strategi", "bayar", "utang", "bola", "salju", "longsor"],
        "patterns": ["snowball vs avalanche", "snowball atau avalanche", "mana yang lebih baik", "bola salju", "metode longson"],
        "answer": "**Snowball** = bayar utang *terkecil* dulu (biar ada quick win, motivasi).\n\n**Avalanche** = bayar utang *bunga tertinggi* dulu (biar hemat total bunga).\n\n**Rekomendasi**:\n- Kalau **butuh motivasi** & banyak utang kecil → Snowball\n- Kalau **fokus hemat bunga** → Avalanche\n- Kalau **income terbatas** → Avalanche (long-term lebih murah)\n\nCek total bunga di **[Debt Planner](/dashboard/produk)** — lihat mana yang lebih cocok untuk situasi kamu.",
        "suggestions": ["Negosiasi cicilan", "Cek skor risiko", "Cara recovery"],
        "related_actions": [
            {"label": "Buka Debt Planner", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "negosiasi_cicilan",
        "module": "M3_debt_strategy",
        "keywords": ["nego", "negosiasi", "cicilan", "keringanan", "restrukturisasi", "restruk", "tawar", "bisa"],
        "patterns": ["bisa nego cicilan", "negosiasi cicilan", "keringanan cicilan", "restrukturisasi"],
        "answer": "**Ya, bisa nego cicilan**. Tapi realistis — pinjol legal biasanya hanya kasih:\n- **Perpanjangan tenor** (cicilan lebih kecil, total bayar lebih besar)\n- **Diskon pelunasan** (kalau mau lunas penuh sebelum tenor)\n\n**Pinjol ilegal** tidak bisa dipercaya — bayar = hangus, gak ada nego.\n\n**Tips**:\n1. Ajukan *restruk* resmi via app/call center\n2. Punya **slip gaji + rekening koran** sebagai bukti kemampuan\n3. Jangan transfer ke rekening pribadi DC (harus resmi)\n\nLihat **[Debt Planner](/dashboard/produk)** untuk simulasi sebelum nego.",
        "suggestions": ["DC agresif", "Snowball vs Avalanche", "Lapor DC ilegal"],
        "related_actions": [
            {"label": "Hitung Debt Plan", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "konsolidasi_utang",
        "module": "M3_debt_strategy",
        "keywords": ["konsolidasi", "gabung", "satuin", "merge", "refinance", "satu tempat"],
        "patterns": ["gabung utang", "konsolidasi utang", "satuin semua utang"],
        "answer": "**Konsolidasi** = gabung semua utang ke 1 tempat, biasanya bunga lebih rendah.\n\n**Opsi**:\n- **KTA bank** (bunga 10-15%/tahun, tenor 1-5 tahun)\n- **Refinance properti** (kalau punya rumah, bunga 7-9%)\n- **Pinjol legal** dengan bunga lebih rendah (jarang, biasanya pinjol gak refinance)\n\n**Plus**: 1 tagihan, gak lupa, skor kredit naik.\n**Minus**: butuh agunan / kredit bagus, proses 1-2 minggu.\n\nCek **[Debt Planner](/dashboard/produk)** untuk simulasi hemat bunga.",
        "suggestions": ["Snowball vs Avalanche", "Cek skor risiko", "Bunga wajar?"],
        "related_actions": [
            {"label": "Buka Debt Planner", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "berapa_utang_normal",
        "module": "M3_debt_strategy",
        "keywords": ["berapa", "utang", "normal", "wajar", "dti", "rasio"],
        "patterns": ["berapa utang yang normal", "utang normal", "dti ideal"],
        "answer": "Rasio utang (DTI) yang sehat:\n- **< 30% income**: Sehat ✅\n- **30-40%**: Waspada ⚠️\n- **> 40%**: Bahaya, fokus bayar dulu 💨\n\n**DTI** = (total cicilan per bulan / income per bulan) × 100%.\n\nContoh: income 5jt, cicilan 2jt → DTI 40% (waspada).\n\nCek skormu di **[Skor Risiko](/dashboard/ringkasan)** — sudah include DTI + jumlah pinjol aktif.",
        "suggestions": ["Cek skor", "Snowball vs Avalanche", "Cara recovery"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },

    # ===== M4: DC Negotiation =====
    {
        "intent": "dc_agresif",
        "module": "M4_dc_negotiation",
        "keywords": ["dc", "agresif", "ancam", "intimidasi", "takut", "kasar", "kotor", "teror", "sebar"],
        "patterns": ["dc agresif", "dc ancam", "dc takuti", "dc sebar data"],
        "answer": "**DC agresif = ilegal** (kalau pinjol legal, DC harus profesional).\n\n**Yang boleh DC**: telepon, SMS, email, kunjungan (jam 8-17).\n\n**Yang TIDAK boleh**:\n- Ancam, teriak, kata-kata kotor\n- Sebar data/foto ke keluarga, kantor, medsos\n- Telepon tengah malam (>21.00)\n- Akses kontak tanpa izin\n- Perintasan fisik / kekerasan\n\n**Langkah**:\n1. **Jangan panik**. Mute/tolak panggilan\n2. **Screenshot semua bukti** (chat, rekaman, foto)\n3. **Lapor OJK + Kominfo + Polisi** (cyber crime)\n\nCek apakah DC legit di **[Pinjol Checker](/dashboard/produk)**.",
        "suggestions": ["Lapor DC ilegal", "Hapus data", "Hukum pinjol ilegal"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk"},
            {"label": "Lapor Kominfo", "href": "https://aduankonten.id", "external": True},
        ],
    },
    {
        "intent": "cara_nego_dc",
        "module": "M4_dc_negotiation",
        "keywords": ["nego", "negosiasi", "dc", "debt", "collector", "bicara", "tagih", "tidak", "ada", "uang"],
        "patterns": ["cara nego dc", "bicara dengan dc", "dc tagih terus"],
        "answer": "**Tips negosiasi dengan DC**:\n\n1. **Jangan hindari**. Makin dihindari, makin agresif.\n2. **Tetap tenang & sopan**. DC manusia, bukan musuh.\n3. **Akui utang**: *\"Saya tahu ada tagihan Rp X. Saya mau selesaikan.\"*\n4. **Tanya bukti**: *\"Bisa kirim surat tagihan resmi? Bukan ancaman.\"*\n5. **Tawarkan rencana**: *\"Saya bisa bayar Rp 500rb per minggu mulai Senin.\"*\n6. **Minta restrukturisasi**: perpanjang tenor, diskon pelunasan.\n7. **Dokumentasikan**: screenshot, rekam (kalau 1 pihak, legal).\n\n**Hak kamu**: DC gak boleh intimidasi, sebar data, ancam keluarga. Itu ilegal.",
        "suggestions": ["DC agresif", "Lapor DC ilegal", "Template chat DC"],
        "related_actions": [],
    },
    {
        "intent": "template_chat",
        "module": "M4_dc_negotiation",
        "keywords": ["template", "contoh", "script", "chat", "kirim", "dc", "debt", "collector"],
        "patterns": ["template chat dc", "contoh chat ke dc", "script negosiasi"],
        "answer": "**Template chat untuk DC** (sopan + tegas):\n\n*\"Selamat [pagi/siang/sore], saya [nama], borrower untuk [nama pinjol] dengan nomor kontrak [no]. Saya mengakui ada tunggakan dan ingin melunasinya secara bertanggung jawab.*\n\n*Saat ini kemampuan saya Rp [nominal] per [minggu/bulan]. Saya mohon restrukturisasi tenor / diskon pelunasan. Saya minta surat resmi, bukan ancaman via telepon/SMS.*\n\n*Jika Bapak/Ibu dari debt collector ilegal, saya akan melapor ke OJK dan Polisi. Terima kasih.\"*\n\nKirim via **WhatsApp** (ada jejak digital), bukan telepon. Simpan semua chat sebagai bukti.",
        "suggestions": ["Cara nego DC", "DC agresif", "Lapor DC ilegal"],
        "related_actions": [
            {"label": "Cek Pinjol Legal", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "lapor_dc",
        "module": "M4_dc_negotiation",
        "keywords": ["lapor", "dc", "ilegal", "polisi", "ojk", "kominfo", "pengaduan"],
        "patterns": ["lapor dc ilegal", "cara lapor dc", "lapor debt collector"],
        "answer": "**Cara lapor DC ilegal**:\n\n1. **OJK** ([ojk.go.id](https://www.ojk.go.id/)) — untuk pinjol ilegal & fintech nakal\n2. **Kominfo** ([aduankonten.id](https://aduankonten.id)) — untuk sebar data, ancaman via medsos\n3. **Polisi Cyber Crime** ([ccic.polri.go.id](https://ccic.polri.go.id)) — untuk ancaman, pemerasan, kekerasan\n4. **Yayasan Lembaga Konsumen Indonesia (YLKI)** — bantuan hukum gratis\n\n**Bukti yang dibutuhkan**:\n- Screenshot chat/telepon DC\n- Rekaman suara (kalau 1 pihak, legal)\n- Bukti transfer (kalau pernah bayar)\n- Nama DC + nama pinjol\n\n**Jangan** transfer ke rekening pribadi. Minta **resi resmi**.",
        "suggestions": ["DC agresif", "Hapus data", "Hukum pinjol ilegal"],
        "related_actions": [
            {"label": "Lapor OJK", "href": "https://www.ojk.go.id/", "external": True},
            {"label": "Lapor Kominfo", "href": "https://aduankonten.id", "external": True},
        ],
    },

    # ===== M5: Recovery =====
    {
        "intent": "cara_recovery",
        "module": "M5_recovery",
        "keywords": ["cara", "keluar", "recovery", "galbay", "lunas", "selesaikan", "bebas", "sembuh", "pulih"],
        "patterns": ["cara keluar dari galbay", "cara recovery", "gimana supaya lunas"],
        "answer": "**Recovery dari galbay** butuh 3 fase:\n\n**Fase 1 (Minggu 1-2)**: Hentikan pendarahan\n- Stop pinjam baru\n- Daftar semua utang (nominal, bunga, tenor, tgl jatuh tempo)\n- Cek SLIK di bank terdekat\n- Hapus app pinjol dari HP\n\n**Fase 2 (Minggu 3-4)**: Negosiasi\n- Hubungi pinjol utama, ajukan restrukturisasi\n- Mulai kerja sampingan (target +Rp 500rb/bln)\n- Buka rekening khusus bayar utang\n\n**Fase 3 (Bulan 2-3)**: Eksekusi\n- Bayar tepat waktu minimal\n- Turun 10-15% dari total utang\n- Bikin emergency fund mini\n\nCek **[Roadmap 30/60/90 hari](/dashboard/produk)** — dipersonalisasi sesuai kondisi kamu.",
        "suggestions": ["Cek skor risiko", "Snowball vs Avalanche", "Negosiasi cicilan"],
        "related_actions": [
            {"label": "Buka Recovery Roadmap", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "telat_30_hari",
        "module": "M5_recovery",
        "keywords": ["telat", "30", "hari", "nunggak", "lewat", "tempo", "denda", "kritis", "parah"],
        "patterns": ["telat 30 hari", "telat sebulan", "sudah 30 hari telat"],
        "answer": "**Telat 30 hari = Kritis**. Dampak:\n- Denda + bunga menumpuk (bisa 2x lipat)\n- Masuk **SLIK** (catatan hitam BI/OJK) → 5 tahun ganggu KTA/kartu kredit\n- Pinjol mulai kirim **DC** (bisa sah, bisa ilegal)\n- Skor kredit turun drastis\n\n**Langkah emergency**:\n1. **Minggu 1**: Cek total tagihan + bunga final di app\n2. **Minggu 1**: Hubungi CS, ajukan **restrukturisasi** (perpanjang tenor)\n3. **Minggu 2**: Prioritaskan bayar **pokok**, bukan bunga\n4. **Minggu 2**: Stop DC ilegal, minta **bukti tagihan resmi**\n5. **Bulan 2**: Lunasi bertahap (mulai dari bunga tertinggi)\n\nBuka **[Recovery Roadmap](/dashboard/produk)** — dipersonalisasi untuk severity **KRITIS**.",
        "suggestions": ["Cara recovery", "DC agresif", "Lapor DC ilegal"],
        "related_actions": [
            {"label": "Buka Roadmap", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "telat_7_hari",
        "module": "M5_recovery",
        "keywords": ["telat", "7", "hari", "seminggu", "minggu", "lewat", "nunggak"],
        "patterns": ["telat 7 hari", "telat seminggu", "telat satu minggu"],
        "answer": "**Telat 7 hari** masih recoverable. Denda biasanya 1-5% dari cicilan.\n\n**Langkah cepat**:\n1. **Bayar hari ini juga** (minimal 50% kalau tidak full)\n2. Aktifkan **auto-debit** untuk bulan depan\n3. Setel **reminder H-3** sebelum jatuh tempo\n4. Cek apakah ada keringanan (beberapa pinjol kasih *grace period* 1x)\n\n**Jangan**: pinjam dari pinjol lain untuk tutup telat (itu *galbay*).",
        "suggestions": ["Cara recovery", "Cek skor", "Self reward boleh?"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },
    {
        "intent": "self_reward_aman",
        "module": "M5_recovery",
        "keywords": ["self", "reward", "hadiah", "gift", "traktir", "belanja", "beli", "boleh", "aman"],
        "patterns": ["self reward boleh", "belanja boleh gak", "reward aman"],
        "answer": "**Self reward boleh, asal proporsional**.\n\n**Rule 5%**:\n- Maksimal 5% income per bulan untuk self-reward\n- Contoh: income 5jt → reward maks Rp 250rb/bln\n\n**Waktu yang aman**:\n- Setelah bayar semua tagihan tepat waktu\n- Setelah punya emergency fund minimal 1 bulan expense\n- Saat skor Risiko = **Aman**\n\n**Waktu yang TIDAK aman**:\n- Baru bayar minimum\n- Masih punya tunggakan\n- Skor Risiko = Waspada/Bahaya\n\nCek **[Skor Risiko](/dashboard/ringkasan)** untuk lihat apakah kamu *qualified* self-reward bulan ini.",
        "suggestions": ["Cek skor", "Berapa utang normal?", "Cara recovery"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },

    # ===== M6: Legal Rights =====
    {
        "intent": "hukum_pinjol_ilegal",
        "module": "M6_legal_rights",
        "keywords": ["hukum", "pinjol", "ilegal", "uu", "pasal", "pidana", "pidankan", "gugatan"],
        "patterns": ["hukum pinjol ilegal", "uu pinjol", "pasal pinjol"],
        "answer": "**Pinjol ilegal bisa dipidanakan**:\n\n- **UU PDP No. 27/2022**: sebar data pribadi = **pidana 4 tahun + denda 4 M**\n- **UU ITE No. 19/2016**: ancaman digital = **pidana 6 tahun**\n- **KUHP Pasal 368**: pemerasan = **pidana 9 tahun**\n- **UU Perlindungan Konsumen**: bunga tidak wajar = **pidana 5 tahun**\n\n**Tindakan**: Kumpulkan bukti → lapor OJK + Kominfo + Polisi. Pinjol ilegal bukan kreditor sah, gak ada utang moral/legal.\n\nCek legal/ilegal di **[Pinjol Checker](/dashboard/produk)**.",
        "suggestions": ["Lapor DC", "Hapus data", "DC agresif"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "hak_borrower",
        "module": "M6_legal_rights",
        "keywords": ["hak", "borrower", "konsumen", "pinjol", "debitur", "perlindungan"],
        "patterns": ["hak borrower", "hak sebagai peminjam", "hak konsumen pinjol"],
        "answer": "**Hak kamu sebagai borrower** (UU OJK + UU Perlindungan Konsumen):\n\n1. **Info jelas**: bunga, biaya, tenor, denda WAJIB diungkap di awal\n2. **Privasi data**: pinjol gak boleh sebar data ke pihak ketiga tanpa izin\n3. **DC profesional**: telepon cuma jam 8-17, gak boleh ancam/sebar aib\n4. **Restrukturisasi**: berhak ajukan keringanan kalau gak mampu\n5. **Keluhan**: berhak lapor ke OJK kalau pinjol langgar aturan\n6. **Waktu berpikir**: 7 hari cooling-off untuk kredit > Rp 5jt\n\nKalau dilanggar, **lapor** — kamu dilindungi hukum.",
        "suggestions": ["Lapor DC", "Hukum pinjol ilegal", "Pinjol ilegal?"],
        "related_actions": [
            {"label": "Lapor OJK", "href": "https://www.ojk.go.id/", "external": True},
        ],
    },
    {
        "intent": "biaya_tersembunyi",
        "module": "M6_legal_rights",
        "keywords": ["biaya", "tersembunyi", "admin", "provinsi", "denda", "fee", "potong"],
        "patterns": ["biaya tersembunyi pinjol", "biaya admin", "denda telat"],
        "answer": "**Waspadai biaya tersembunyi** (umum di pinjol ilegal):\n\n- **Biaya admin/provisi**: 5-15% dari nominal pinjam (potong di awal)\n- **Denda telat**: 1-5% per hari dari cicilan (bisa compound)\n- **Biaya transfer**: 5-10rb per transaksi\n- **Asuransi paksa**: 1-3% dari pokok\n- **Denda pelunasan awal**: 5-10% dari sisa pokok\n\n**Cara hitung efektif**: bunga flat 0.5%/hari = **effective rate ~180% per tahun**.\n\nPinjol legal OJK **wajib** disclose semua biaya di aplikasi. Cek di **[Pinjol Checker](/dashboard/produk)**.",
        "suggestions": ["Bunga wajar?", "Pinjol ilegal?", "Simulasi cicilan"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "slik_ojk",
        "module": "M6_legal_rights",
        "keywords": ["slik", "bi", "checking", "skor", "kredit", "ojk", "histori", "riwayat"],
        "patterns": ["slik ojk", "bi checking", "cek skor kredit"],
        "answer": "**SLIK (Sistem Layanan Informasi Keuangan)** = catatan kredit resmi dari OJK (sebelumnya BI Checking).\n\n- **Skor 1-2 (Kolektibilitas 1-2)**: Sehat ✅\n- **Skor 3 (Kurang Lancar)**: Waspada ⚠️\n- **Skor 4-5 (Diragukan/Macet)**: Bahaya 💨 — 5 tahun ganggu KTA/kartu kredit\n\n**Cara cek**: Bawa e-KTP ke **bank terdekat** (gratis). Bisa juga via **portal SLIK OJK** ([ojk.go.id](https://www.ojk.go.id/)).\n\nPenting untuk tahu *dari pinjol mana* kamu punya tunggakan. Galbay Predictor bisa bantu analisis pola dari data Google Play reviews.",
        "suggestions": ["Cek skor risiko", "Telat 30 hari", "Cara recovery"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },

    # ===== M7: App Recommendation =====
    {
        "intent": "aplikasi_aman",
        "module": "M7_app_rec",
        "keywords": ["aplikasi", "aman", "data", "privacy", "privasi", "galbay"],
        "patterns": ["aplikasi ini aman gak", "data saya gimana", "galbay aman"],
        "answer": "**Galbay Predictor aman & privasi terjaga**:\n\n- **Tidak ada registrasi data pribadi**\n- **Tidak menyimpan input skor/planner** (semua diproses *client-side* + *stateless server*)\n- **Demo login** cuma untuk coba fitur (bisa pakai email dummy)\n- **Google OAuth** via Google resmi, tidak ada password yang kami simpan\n- **Demo badge** di pojok = simulasi, bukan produk komersial\n\nLihat detail di **[Privacy Policy](/privacy)** dan **[Terms](/terms)**.",
        "suggestions": ["Cara pakai website", "Data sumber", "Premium dapat apa?"],
        "related_actions": [
            {"label": "Lihat Privacy", "href": "/privacy"},
        ],
    },
    {
        "intent": "premium_dapat_apa",
        "module": "M7_app_rec",
        "keywords": ["premium", "dapat", "apa", "fitur", "pro", "berbayar", "benefit", "keuntungan"],
        "patterns": ["premium dapat apa", "fitur premium", "benefit premium"],
        "answer": "**Galbay Premium** (Rp 49rb/bln atau Rp 399rb/tahun):\n\n- 🤖 **AI Coach unlimited** (chatbot lebih dalam, follow-up questions)\n- 💾 **Save unlimited** skor & roadmap (free: 3 history)\n- 📊 **Advanced analytics**: tren 6 bulan, perbandingan antar utang\n- 🎯 **Personalized action plan** mingguan via email\n- 📞 **Priority support** (response < 4 jam)\n- 🎁 **Eksklusif konten** (modul lanjutan galbay recovery)\n\n**[Lihat detail di halaman Pricing](/dashboard/produk)**. Ada diskon 50% di tahun pertama!",
        "suggestions": ["Diskon premium?", "Cara pakai website", "Data sumber"],
        "related_actions": [
            {"label": "Lihat Premium", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "diskon_premium",
        "module": "M7_app_rec",
        "keywords": ["diskon", "promo", "potongan", "harga", "kupon", "voucher", "kode", "diskon"],
        "patterns": ["ada diskon gak", "promo premium", "kode diskon"],
        "answer": "**Promo Premium**:\n\n- **Diskon 50%** tahun pertama (Rp 199rb/tahun, dari Rp 399rb)\n- **Gratis 14 hari** untuk user baru (coba dulu, baru bayar)\n- **Bulan pertama** gratis untuk user yang daftar waitlist\n\n**[Daftar Premium](/dashboard/produk)** atau **[Join waitlist](/waitlist)** untuk dapat notifikasi promo.",
        "suggestions": ["Premium dapat apa?", "Cara pakai", "Data sumber"],
        "related_actions": [
            {"label": "Lihat Premium", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "cara_pakai_website",
        "module": "M7_app_rec",
        "keywords": ["cara", "pakai", "website", "web", "app", "pakai", "penggunaan", "panduan", "tutorial"],
        "patterns": ["cara pakai web", "cara pakai galbay", "tutorial"],
        "answer": "**Cara pakai Galbay Predictor**:\n\n1. **Ringkasan** → Lihat insight umum dari 602K data multi-source (Play + OJK + Forum + Blog + YouTube + Threads + Trends)\n2. **Analisis** → Confusion matrix, sentiment breakdown, app comparison, multi-source distribution\n3. **Solusi** → Business Model Canvas dari 9 blok data-driven\n4. **Produk** → Skor Risiko, Pinjol Checker, Debt Planner, Recovery Roadmap, Simulasi Cicilan\n5. **Kesimpulan** → Key findings + rekomendasi\n\nCukup **login** (gratis) untuk akses semua fitur. Premium untuk unlimited AI Coach + advanced analytics.",
        "suggestions": ["Cek skor", "Pinjol Checker", "Recovery Roadmap"],
        "related_actions": [
            {"label": "Mulai", "href": "/dashboard/ringkasan"},
        ],
    },
    {
        "intent": "data_sumber",
        "module": "M7_app_rec",
        "keywords": ["data", "sumber", "602", "ribu", "ulasan", "review", "dataset", "asal", "multi", "source"],
        "patterns": ["data dari mana", "sumber data", "dataset"],
        "answer": "**Dataset Galbay Predictor (7 source multi-source, 602K total)**:\n\n- **Google Play Store**: 599.000 review (53 app finansial Gen Z, 11 kategori)\n- **OJK + media**: 460 artikel (regulator & narasi pasar)\n- **Forum Kaskus**: 244 threads (komunitas diskusi utang)\n- **Blog Indonesia**: 1.056 posts (Medium, Hipwee, Kumparan, dll)\n- **YouTube (yt-dlp)**: 283 video + 1.331 komentar\n- **Threads (Meta)**: 231 posts (bahasa natural Gen Z)\n- **Google Trends**: 786 records time-series 5 tahun (minat pencarian publik)\n- **Periode**: 2015-2026 (11 tahun)\n- **Relevan**: 58.120 review (9,7% — setelah filter 65+ keyword galbay)\n- **Distress signal**: 13.827 review (23,8% dari relevan) → basis B2C user potensial\n\n**Bukan data primer**: ini *analisis sekunder* dari data publik. Tidak merepresentasikan semua pengguna Indonesia.\n\nLihat detail metodologi di **[Kesimpulan](/dashboard/kesimpulan)**.",
        "suggestions": ["AI atau rule-based?", "Premium dapat apa?", "Cara pakai"],
        "related_actions": [
            {"label": "Lihat Kesimpulan", "href": "/dashboard/kesimpulan"},
        ],
    },
    {
        "intent": "ai_atau_rule_based",
        "module": "M7_app_rec",
        "keywords": ["ai", "ml", "machine", "learning", "model", "rule", "based", "pakai", "teknologi"],
        "patterns": ["pakai ai gak", "rule based atau ai", "model ml"],
        "answer": "**Saat ini: Hybrid**:\n\n- **Skor Risiko**: rule-based scoring (bobot pinjol, paylater, telat, dll) — *siap di-swap ke ML model* saat data latih cukup\n- **Chatbot**: rule-based FAQ NLP v2 (35+ intents, 8 modul, sinonim, typo tolerance, sentiment)\n- **Pinjol Checker**: database lookup + pattern matching\n- **Debt Planner**: deterministic (snowball/avalanche algorithm)\n- **Recovery Roadmap**: rule-based (severity threshold)\n\n**Roadmap**: Ganti ke *Random Forest / XGBoost* saat data latih internal siap. Sekarang fokus *prototype & UX*.\n\nLihat **[Kesimpulan](/dashboard/kesimpulan)** untuk detail.",
        "suggestions": ["Data sumber", "Premium dapat apa?", "Cara pakai"],
        "related_actions": [
            {"label": "Lihat Kesimpulan", "href": "/dashboard/kesimpulan"},
        ],
    },
    {
        "intent": "konsultan_keuangan",
        "module": "M7_app_rec",
        "keywords": ["konsultan", "konseling", "keuangan", "gratis", "bantuan", "profesional", "temen", "curhat"],
        "patterns": ["konsultan keuangan gratis", "bantuan profesional", "ada konsultan"],
        "answer": "**Konsultan keuangan gratis/terjangkau**:\n\n- **OJK**: 157 (hotline pengaduan & konsultasi konsumen)\n- **Lembaga Konsumen**: YLKI (Yayasan Lembaga Konsumen Indonesia) — konsultasi gratis via web\n- **Bank**: banyak bank punya *financial planner* gratis untuk nasabah prioritas\n- **LSM**: PFID (Pusat Fintech & Inovasi Digital) — edukasi fintech gratis\n- **Komunitas**: r/IndonesiaFinansial (Reddit), Finansialku forum\n\n**Gratis vs Berbayar**:\n- Gratis: edukasi umum, pengaduan, simulasi\n- Berbayar: rencana personal, negosiasi DC, mediasi hukum\n\nLihat **[Chat AI Coach](/dashboard/produk)** untuk konsultasi 24/7.",
        "suggestions": ["Konseling berapa", "Stress finansial", "Cara recovery"],
        "related_actions": [
            {"label": "Chat AI", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "konseling_berapa",
        "module": "M7_app_rec",
        "keywords": ["konseling", "berapa", "biaya", "harga", "psikolog", "konsultan"],
        "patterns": ["konseling berapa", "biaya konseling", "psikolog murah"],
        "answer": "**Estimasi biaya konseling keuangan**:\n\n- **AI Coach Galbay**: **GRATIS** (dengan limitasi), Premium unlimited Rp 49rb/bln\n- **Konsultan online (PFID, Finansialku)**: Rp 50-150rb/sesi\n- **Psikolog finansial**: Rp 200-500rb/sesi\n- **Financial planner tersertifikasi (CFP)**: Rp 500rb-1.5jt/konsultasi\n- **Hotline OJK 157**: **GRATIS**\n\n**Untuk Gen Z dengan budget terbatas**:\n1. Mulai dari **AI Coach Galbay** (gratis)\n2. **Komunitas online** (Reddit, Telegram)\n3. **Konsultan PFID** (terjangkau)\n4. **Profesional bersertifikat** kalau kasus kompleks",
        "suggestions": ["Konsultan keuangan", "Cara recovery", "Stress finansial"],
        "related_actions": [
            {"label": "Buka Chat", "href": "/dashboard/produk"},
        ],
    },

    # ===== M8: Mental Health =====
    {
        "intent": "stress_finansial",
        "module": "M8_mental_health",
        "keywords": ["stress", "stres", "cemas", "panik", "khawatir", "takut", "gelisah", "pusing", "mental", "mental health"],
        "patterns": ["stress finansial", "cemas galbay", "panik utang", "depresi utang"],
        "answer": "**Stress finansial itu nyata, dan kamu tidak sendirian**. 65% Gen Z Indonesia melaporkan *financial anxiety* (survei 2024).\n\n**Tanda-tanda**:\n- Susah tidur karena mikirin tagihan\n- Gak mau buka app banking\n- Malu cerita ke keluarga/teman\n- Moody tiap tanggal 1\n- Makan/olahraga berubah drastis\n\n**Langkah pertama**:\n1. **Akui perasaannya** (nggak ada yang salah dengan merasa stress)\n2. **List semua utang di kertas** (clarity = control)\n3. **Bicara ke 1 orang terpercaya** (teman, keluarga, partner)\n4. **Cek Skor Risiko** — kebanyakan orang ternyata *Tidak separah yang mereka kira*\n5. **[Konsultasi gratis](/dashboard/produk)** via AI Coach\n\nKalau pikiran *self-harm* muncul, hubungi **119 ext 8** (Sejiwa) atau **Into The Light Indonesia**.",
        "suggestions": ["Cek skor", "Konsultan gratis", "Cara recovery"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
            {"label": "Hubungi Sejiwa", "href": "https://www.into-the-light.id/", "external": True},
        ],
    },
    {
        "intent": "self_harm",
        "module": "M8_mental_health",
        "keywords": ["bunuh", "diri", "self", "harm", "menyakiti", "mati", "ending", "putus asa", "ç»æœ›", "ç»æœ›", "ç»æœ›"],
        "patterns": ["bunuh diri", "self harm", "putus asa", "menyakiti diri"],
        "answer": "**Kamu penting, dan ini bisa lewat**. Tolong bicara ke seseorang hari ini:\n\n🆘 **Hotline 24/7**:\n- **Sejiwa (119 ext 8)** — Kemenkes RI, gratis\n- **Into The Light** ([intothelightid.org](https://www.into-the-light.id/))\n- **LSM Jangan Bunuh Diri** (021-9696 9293 / 0858-9150-0029)\n- **Yayasan Pulih** ([yayasanpulih.org](http://yayasanpulih.org))\n\n**Masalah finansial bisa selesai. Kamu tidak sendirian.** Bicara ke teman, keluarga, atau profesional — itu langkah pertama.\n\nSaya bisa bantu **rencana pembayaran** kalau kamu mau. **[Cek Skor Risiko](/dashboard/ringkasan)** dulu, biar ada titik terang.",
        "suggestions": ["Cek skor", "Stress finansial", "Konsultan gratis"],
        "related_actions": [
            {"label": "Hubungi Sejiwa", "href": "https://www.into-the-light.id/", "external": True},
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },
    {
        "intent": "emergency_dc",
        "module": "M4_dc_negotiation",
        "keywords": ["emergency", "darurat", "tolong", "dc", "sekarang", "telepon", "malam", "hari", "ini"],
        "patterns": ["dc telepon sekarang", "darurat dc", "dc malam ini"],
        "answer": "**DC nelpon sekarang? Tenang, ini langkah cepat**:\n\n1. **Jangan angkat** (kalau panik). Tunggu 5 menit, tarik napas.\n2. **Cek legal/ilegal** di **[Pinjol Checker](/dashboard/produk)** — input nama app-nya\n3. **Kalau ilegal**: jangan bayar, dokumentasi, lapor OJK + Kominfo\n4. **Kalau legal**: angkat, tanya *nomor kontrak + surat tagihan resmi*\n5. **Ajak keluarga** (kalau DC agresif, gak sendirian lebih aman)\n6. **Mute DC malam hari** (>21.00 ilegal) — rekam sebagai bukti\n\n**Kamu punya hak menolak telepon, asal sopan**. *\"Saya mau verifikasi dulu, mohon kirim via email/app.\"*\n\nLihat **[Cara Nego DC](/dashboard/produk)**.",
        "suggestions": ["DC agresif", "Lapor DC", "Cek pinjol legal"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "tagihan_terlalu_banyak",
        "module": "M5_recovery",
        "keywords": ["tagihan", "banyak", "banyak", "lupa", "track", "mana", "mana aja", "jatuh tempo"],
        "patterns": ["tagihan terlalu banyak", "lupa tagihan", "gak tau tagihan mana"],
        "answer": "**Cara manage tagihan banyak**:\n\n1. **Spreadsheet/NOTES**: kolom = *nama pinjol, total, bunga, tenor, tgl jatuh tempo, link app*\n2. **Setel auto-debit** dari rekening gaji (H-1 dari jatuh tempo)\n3. **Reminder H-3** (Google Calendar / Todoist)\n4. **Akun email khusus** untuk tagihan (auto-filter dari promo)\n5. **Bayar tanggal 25-30** (sebelum gajian akhir bulan), bukan saat baru gajian (biar gak kegoda)\n\n**Tools gratis**:\n- **Google Sheets** template budgeting\n- **Wallet by BudgetBakers** (app gratis, track multi-account)\n- **Galbay Predictor** — chart distribusi tagihan kamu\n\nCek **[Skor Risiko](/dashboard/ringkasan)** untuk lihat berapa banyak utang aktif.",
        "suggestions": ["Cek skor", "Snowball vs Avalanche", "Auto-debit"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/ringkasan"},
        ],
    },
    {
        "intent": "auto_debit",
        "module": "M3_debt_strategy",
        "keywords": ["auto", "debit", "otomatis", "potong", "otomatis", "rekening", "tagihan"],
        "patterns": ["auto debit", "setel otomatis", "potong otomatis"],
        "answer": "**Auto-debit = penyelamat dari telat**:\n\n**Cara setup**:\n1. Buka app pinjol → **Pengaturan / Settings**\n2. Pilih **Auto-debit** / **Bayar otomatis**\n3. Hubungkan rekening gaji\n4. Setel tanggal H-1 dari jatuh tempo\n\n**Tips**:\n- **Jangan hubungkan** rekening utama (terlalu berisiko kalau saldo kurang)\n- **Buka rekening khusus** untuk bayar utang (uang gaji langsung dipecah 30-50% ke sini)\n- **Sisa** =生活费è´¹ + emergency fund\n\n**Real case**: Auto-debit menurunkan telat bayar 70% (survei OJK 2023).\n\nLihat **[Cara Recovery](/dashboard/produk)** untuk setup lengkap.",
        "suggestions": ["Cara recovery", "Tagihan banyak", "Cek skor"],
        "related_actions": [
            {"label": "Recovery Roadmap", "href": "/dashboard/produk"},
        ],
    },

    # ===== Default fallback =====
    {
        "intent": "default_fallback",
        "module": "M1_galbay_basics",
        "keywords": [],
        "patterns": [],
        "answer": "Hmm, saya belum yakin maksudnya. Bisa jelaskan lebih spesifik?\n\n**Mau tanya soal apa?**\n- **Galbay basics** → *apa itu galbay, skor risiko, simulasi cicilan*\n- **Pinjol** → *legal/ilegal, bunga wajar, cek OJK*\n- **Strategi bayar** → *snowball, avalanche, negosiasi*\n- **DC / penagih** → *nego, template chat, lapor*\n- **Recovery** → *cara keluar, telat 30 hari, roadmap 30/60/90*\n- **Hukum** → *hak borrower, UU PDP, biaya tersembunyi*\n- **Mental health** → *stress, cemas, konseling*\n\nKlik salah satu **chip topik** di atas, atau ketik pertanyaanmu lebih spesifik ya!",
        "suggestions": ["Apa itu galbay", "Cek pinjol legal", "Snowball vs Avalanche", "Cara recovery"],
        "related_actions": [
            {"label": "Lihat Semua Topik", "href": "/dashboard/produk"},
        ],
    },
]


# -----------------------------------------------------------------
# Tokenizer + Synonym expansion
# -----------------------------------------------------------------
_STOPWORDS = {
    "yang", "di", "dan", "ini", "itu", "saya", "aku", "kamu", "mau",
    "tidak", "ga", "gak", "nggak", "enggak", "ya", "dong", "sih",
    "kok", "deh", "aja", "juga", "udah", "sudah", "belum", "lagi",
    "bisa", "dapat", "akan", "kalo", "kalau", "kalau", "tapi",
    "tapi", "soal", "tentang", "untuk", "buat", "bagi", "dari",
    "ke", "pada", "dengan", "atau", "ada", "seperti", "yaitu",
    "yaitu", "bahwa", "karena", "sebab", "oleh", "sangat", "amat",
    "terlalu", "banget", "bgt", "doang", "cuma", "aja", "loh",
}


def _tokenize(text: str) -> list[str]:
    """Lowercase, remove punctuation, split. Drop stopwords."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS and len(t) > 1]
    return tokens


def _expand_with_synonyms(tokens: list[str]) -> set[str]:
    """Expand tokens using SYNONYMS — add all variants for any canonical match."""
    expanded = set(tokens)
    for token in tokens:
        for canonical, variants in SYNONYMS.items():
            if token in variants or token == canonical:
                expanded.update(variants)
                expanded.add(canonical)
    return expanded


def _detect_sentiment(text: str) -> str:
    """Detect user sentiment from message."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["bunuh", "mati", "self harm", "putus asa", "ç»æœ›", "ç»æœ›"]):
        return "crisis"
    if any(w in text_lower for w in ["panik", "takut", "khawatir", "cemas", "gelisah", "stress", "depresi"]):
        return "stressed"
    if any(w in text_lower for w in ["bingung", "gimana", "gak tau", "tidak tahu", "?", "apa", "kapan"]):
        return "curious"
    if any(w in text_lower for w in ["marah", "kesel", "kesal", "jengkel", "emosi", "sebel", "sebal"]):
        return "frustrated"
    if any(w in text_lower for w in ["makasih", "terima kasih", "thanks", "thank you", "👍", "❤️ï¸", "❤️"]):
        return "grateful"
    if any(w in text_lower for w in ["keren", "bagus", "membantu", "helpful", "mantap", "oke"]):
        return "positive"
    return "neutral"


def _get_time_greeting() -> str:
    """Time-based greeting (pagi/siang/sore/malam)."""
    hour = _dt.now().hour
    if 5 <= hour < 11:
        return "Selamat pagi"
    if 11 <= hour < 15:
        return "Selamat siang"
    if 15 <= hour < 18:
        return "Selamat sore"
    return "Selamat malam"


def _format_answer_markdown(text: str) -> str:
    """Convert markdown to safe HTML.

    Supports:
    - **bold** → <strong>
    - *italic* → <em>
    - `code` → <code>
    - ```code blocks``` → <pre><code>
    - [link](url) → <a href>
    - - lists / 1. ordered
    - newlines → <br>
    """
    if not text:
        return ""

    # Code blocks first (```...```)
    text = re.sub(
        r"```([\s\S]*?)```",
        r"<pre><code>\1</code></pre>",
        text,
    )

    # Inline code (`...`)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold (**...**)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

    # Italic (*...*) — careful not to catch bold
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)

    # Links [text](url)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        text,
    )

    # Markdown lists (- item)
    lines = text.split("\n")
    in_ul = False
    in_ol = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            if in_ol:
                new_lines.append("</ol>")
                in_ol = False
            if not in_ul:
                new_lines.append("<ul>")
                in_ul = True
            new_lines.append(f"<li>{stripped[2:].strip()}</li>")
        elif re.match(r"^\d+\.\s", stripped):
            if in_ul:
                new_lines.append("</ul>")
                in_ul = False
            if not in_ol:
                new_lines.append("<ol>")
                in_ol = True
            new_lines.append(f"<li>{re.sub(r'^\d+\.\s', '', stripped)}</li>")
        else:
            if in_ul:
                new_lines.append("</ul>")
                in_ul = False
            if in_ol:
                new_lines.append("</ol>")
                in_ol = False
            new_lines.append(line)
    if in_ul:
        new_lines.append("</ul>")
    if in_ol:
        new_lines.append("</ol>")
    text = "\n".join(new_lines)

    # Newlines → <br> (outside of <pre>)
    parts = re.split(r"(<pre>[\s\S]*?</pre>)", text)
    for i, part in enumerate(parts):
        if not part.startswith("<pre>"):
            parts[i] = part.replace("\n", "<br>")
    text = "".join(parts)

    return text


def _score_intent(entry: dict, tokens: set[str], expanded: set[str]) -> float:
    """Score a single FAQ entry against user tokens."""
    if not tokens:
        return 0.0
    keywords = set(entry.get("keywords", []))
    patterns = entry.get("patterns", [])

    # Direct keyword match in expanded set
    keyword_matches = len(keywords & expanded)
    if keyword_matches == 0:
        # Fallback: difflib fuzzy match (typo tolerance)
        fuzzy_hits = 0
        for kw in keywords:
            for tok in tokens:
                if len(tok) >= 4 and len(kw) >= 4:
                    ratio = difflib.SequenceMatcher(None, tok, kw).ratio()
                    if ratio > 0.8:
                        fuzzy_hits += 1
                        break
        if fuzzy_hits == 0:
            return 0.0
        keyword_matches = fuzzy_hits * 0.6

    # Pattern matching (whole pattern must be substring of normalized message)
    # Use ORIGINAL tokens only (no synonym expansion) to avoid over-matching
    pattern_match = 0.0
    for pat in patterns:
        pat_tokens = _tokenize(pat)
        if pat_tokens and all(p in set(tokens) for p in pat_tokens):
            pattern_match = 1.0
            break

    # Score: 60% keyword overlap + 40% pattern match
    coverage = keyword_matches / max(len(keywords), 1)
    score = (coverage * 0.6) + (pattern_match * 0.4)
    return min(score, 1.0)


def _match_faq_intent_v2(message: str) -> tuple[dict, float, list[dict]]:
    """Match user message to top 3 FAQ intents.

    Returns:
        (best_entry, confidence, [secondary_intents])
    """
    if not message or not message.strip():
        return FAQ_KB[-1], 0.0, []  # default_fallback

    tokens = _tokenize(message)
    if not tokens:
        return FAQ_KB[-1], 0.0, []

    expanded = _expand_with_synonyms(tokens)

    scored = []
    for entry in FAQ_KB:
        if entry["intent"] == "default_fallback":
            continue
        score = _score_intent(entry, set(tokens), expanded)
        if score > 0:
            scored.append((entry, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return FAQ_KB[-1], 0.0, []  # default_fallback

    best, conf = scored[0]
    secondary = [
        {"intent": e["intent"], "module": e.get("module"), "confidence": round(s, 2)}
        for e, s in scored[1:4]
    ]
    return best, conf, secondary


# -----------------------------------------------------------------
# Backward compat: v1 signature
# -----------------------------------------------------------------
def _match_faq_intent(message: str) -> tuple[dict, float]:
    """v1 backward-compat wrapper for _match_faq_intent_v2."""
    best, conf, _ = _match_faq_intent_v2(message)
    return best, conf


# -----------------------------------------------------------------
# Main chat handler v2
# -----------------------------------------------------------------
def chat_faq_handler(
    message: str,
    user_name: str | None = None,
    page_context: str | None = None,
) -> dict:
    """Process a user message and return structured response.

    Args:
        message: raw user input
        user_name: optional name for personalization
        page_context: optional current page (for context-aware tips)

    Returns:
        dict with valid, intent, module, confidence, answer, answer_html,
        suggestions, related_actions, secondary_intents, sentiment, greeting,
        model_version, disclaimer
    """
    if not message or not message.strip():
        return {
            "valid": False,
            "error": "Pesan kosong. Yuk ketik pertanyaanmu!",
            "model_version": CHATBOT_MODEL_VERSION,
            "disclaimer": CHATBOT_DISCLAIMER,
        }

    best, conf, secondary = _match_faq_intent_v2(message)
    sentiment = _detect_sentiment(message)
    greeting = _get_time_greeting()

    answer = best["answer"]
    answer_html = _format_answer_markdown(answer)

    # Context-aware: if user is on a specific page, add tip
    context_tip = ""
    if page_context == "ringkasan":
        context_tip = "\n\n💡 *Kamu ada di halaman Ringkasan — coba cek Skor Risiko gratis!*"
    elif page_context == "produk":
        context_tip = "\n\n💡 *Kamu ada di halaman Produk — Pinjol Checker & Debt Planner tersedia.*"
    elif page_context == "solusi":
        context_tip = "\n\n💡 *Kamu ada di halaman Solusi — 4 modul recovery siap dibaca.*"

    if context_tip:
        answer_html += _format_answer_markdown(context_tip)

    # Personalization with name (only if name given)
    name_prefix = ""
    if user_name and sentiment in ("stressed", "crisis", "frustrated"):
        name_prefix = f"{user_name}, "

    return {
        "valid": True,
        "intent": best["intent"],
        "module": best.get("module"),
        "module_name": CHATBOT_MODULES.get(best.get("module", ""), {}).get("name"),
        "module_icon": CHATBOT_MODULES.get(best.get("module", ""), {}).get("icon"),
        "confidence": round(conf, 2),
        "answer": answer,
        "answer_html": answer_html,
        "suggestions": best.get("suggestions", []),
        "related_actions": best.get("related_actions", []),
        "secondary_intents": secondary,
        "sentiment": sentiment,
        "greeting": greeting,
        "name_prefix": name_prefix,
        "model_version": CHATBOT_MODEL_VERSION,
        "disclaimer": CHATBOT_DISCLAIMER,
    }
