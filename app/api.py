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

    # ===== ROUND 13: EXPANDED FAQ (60+ intents) =====

    # --- M1 Galbay Basics (3 new) ---
    {
        "intent": "apa_itu_financial_coach",
        "module": "M1_galbay_basics",
        "keywords": ["financial", "coach", "pelatih", "keuangan", "pribadi", "adalah", "apa", "itu"],
        "patterns": ["apa itu financial coach", "financial coach itu apa"],
        "answer": "**Financial Coach** adalah pelatih keuangan pribadi yang bantu kamu:\n\n- 🎯 **Diagnosa** pola keuangan kamu (bukan judgement)\n- 🗺 **Roadmap** keluar dari masalah (bukan teori doang)\n- 🤝 **Accountability** partner yang ngingetin target\n- 💡 **Edukasi** kapan & bagaimana bayar utang\n\nBedanya dengan konsultan keuangan:\n- **Konsultan**: fokus angka & investasi (untuk yang sudah punya uang)\n- **Coach**: fokus perilaku & kebiasaan (untuk yang mau berubah)\n\n**Galbay Predictor** adalah financial coach berbasis AI + data 602K ulasan nyata Indonesia. Gratis, tanpa login.",
        "suggestions": ["Cek skor risiko", "Cara recovery", "Pinjol legal?"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/galbay-score"},
        ],
    },
    {
        "intent": "galbay_berapa_lama",
        "module": "M1_galbay_basics",
        "keywords": ["berapa", "lama", "galbay", "selesai", "waktu", "kapan", "tuntas", "lunas"],
        "patterns": ["berapa lama galbay", "kapan selesai galbay"],
        "answer": "**Berapa lama galbay selesai?**\n\nBergantung severity:\n- **Ringan** (1-2 tagihan, gaji cukup): 3-6 bulan\n- **Sedang** (3-5 tagihan, gaji pas-pasan): 6-12 bulan\n- **Berat** (5+ tagihan, DC agresif): 12-24 bulan\n- **Kritis** (DC datang, aset disita): 24-36+ bulan\n\n**Realita**: Rata-rata Gen Z butuh **8-14 bulan** dengan konsistensi.\n\n**Formula sukses**:\n1. **Bulan 1-2**: Stop pinjam baru, list semua utang\n2. **Bulan 3-6**: Negosiasi restrukturisasi, mulai cicil\n3. **Bulan 6-12**: Lunasi satu per satu (snowball)\n4. **Bulan 12+**: Bangun emergency fund\n\nMulai dari **[Recovery Roadmap 30/60/90 hari](/dashboard/produk)**.",
        "suggestions": ["Cara recovery", "Snowball vs Avalanche", "Auto debit"],
        "related_actions": [
            {"label": "Recovery Roadmap", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "apakah_galbay_berdosa",
        "module": "M1_galbay_basics",
        "keywords": ["dosa", "berdosa", "haram", "salah", "moral", "agama", "islam", "kristen", "budha", "hindu"],
        "patterns": ["apakah galbay berdosa", "galbay itu haram"],
        "answer": "**Apakah galbay (gagal bayar) berdosa?**\n\nIni pertanyaan personal & religius. Berikut perspektif umum:\n\n- **Islam**: Utang adalah tanggung jawab (QS Al-Baqarah: 280). Gagal bayar dengan sengaja = makruh. Tapi kalau karena *sambil mempertahankan harga diri* & sedang berusaha, banyak ulama bilang tidak berdosa.\n- **Kristen**: Roma 13:8 - bayar utang. Tapi ada grace untuk yang tidak mampu (Ulangan 15:1-2).\n- **Universal**: Yang penting **niat & effort** untuk bayar. Kalau lagi proses & jujur = tidak salah.\n\n**Yang WAJIB dihindari**:\n- ❌ **Menghindari DC dengan bohong** = tidak etis\n- ❌ **Pinjam baru untuk bayar utang lama** = infinitely worse\n- ✅ **Jujur tentang kondisi** + **komitmen bayar** = ethical\n\nLihat **[AI Coach](/dashboard/produk)** untuk strategi bayar.",
        "suggestions": ["Cara recovery", "Negosiasi DC", "DC agresif"],
        "related_actions": [],
    },

    # --- M2 Pinjol (4 new) ---
    {
        "intent": "pinjol_terdaftar",
        "module": "M2_pinjol",
        "keywords": ["terdaftar", "registrasi", "izin", "sah", "legal", "resmi", "pinjol", "aplikasi"],
        "patterns": ["pinjol terdaftar", "apakah terdaftar", "izin pinjol"],
        "answer": "**Pinjol terdaftar OJK** artinya ada di daftar resmi **SILO OJK** (Sistem Informasi Layanan Otoritas Jasa Keuangan).\n\nCiri-ciri pinjol legal:\n- ✅ Ada di [SILO OJK](https://www.ojk.go.id/silo)\n- ✅ NPWP + izin usaha jelas\n- ✅ Bunga <= 0.3%/hari (pinjol konvensional)\n- ✅ Bunga <= 24%/tahun (KTA/Kartu Kredit)\n- ✅ Tidak minta akses kontak, foto, SMS, gallery\n- ✅ Customer service di aplikasi (bukan SMS misterius)\n- ✅ Call center resmi (bukan nomor random)\n\nCek sekarang di **[Pinjol Checker Galbay](/dashboard/produk)** (24+ database, gratis).",
        "suggestions": ["Cek pinjol legal", "Bunga wajar?", "Pinjol ilegal?"],
        "related_actions": [
            {"label": "Pinjol Checker", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "bunga_tahunan_vs_harian",
        "module": "M2_pinjol",
        "keywords": ["bunga", "tahunan", "harian", "konversi", "efektif", "flat", "perbedaan", "vs", "annual", "monthly"],
        "patterns": ["bunga tahunan vs harian", "konversi bunga", "bunga efektif"],
        "answer": "**Bunga tahunan vs bunga harian** - cara konversi:\n\n**Formula**:\n```\nBunga Tahunan = Bunga Harian × 365 hari\n```\n\n**Contoh**:\n- **Kredivo**: 0.6%/hari flat = **219%/tahun** (efektif)\n- **Akulaku**: 0.7%/hari = **255%/tahun**\n- **Shopee Paylater**: 2.6%/bulan flat = **~31%/tahun** (mulai 2024)\n- **Kartu Kredit**: 2.5%/bulan = **30%/tahun**\n- **KTA Bank**: 12-24%/tahun (flat)\n\n**Rumus efektif vs flat**:\n```\nFlat 2.6%/bulan = 31.2%/tahun (nominal)\nEfektif 2.6%/bulan = ~36%/tahun (compound)\n```\n\n**Batas OJK**: Maks **0.3%/hari flat** (= 109.5%/tahun flat).\n\nCek bunga spesifik app di **[Simulasi Cicilan](/dashboard/produk)** (gratis).",
        "suggestions": ["Bunga wajar?", "Cek pinjol legal", "Pinjol ilegal?"],
        "related_actions": [],
    },
    {
        "intent": "pinjol_gratis",
        "module": "M2_pinjol",
        "keywords": ["pinjol", "gratis", "tanpa", "bunga", "0%", "nol", "interest", "free"],
        "patterns": ["pinjol gratis", "pinjol tanpa bunga"],
        "answer": "**Pinjol gratis 0% bunga** - apakah ada?\n\n**Realistis**: Hampir tidak ada. Tapi ada **opsi 0% bunga terbatas**:\n\n1. **Paylater 0% untuk transaksi pertama** (Kredivo, Akulaku, Shopee Paylater)\n   - Syarat: bayar penuh sebelum jatuh tempo, biasanya 30 hari\n   - Setelah itu kembali ke bunga normal (~2.6%/bulan)\n2. **Promo cicilan 0%** untuk merchant tertentu\n   - Tokopedia, Shopee, Lazada sering ada\n   - Berlaku untuk barang spesifik (elektronik, fashion)\n3. **Pinjol mikro dari LSM** (bukan komersial)\n   - YLBHI, PFID untuk穷人 (poor)\n   - Limit kecil, bunga sosial\n\n**Waspada**: \"0% tanpa syarat\" = jebakan. Selalu baca fine print!\n\n**[Simulasi Cicilan](/dashboard/produk)** untuk hitung total bayar.",
        "suggestions": ["Bunga wajar?", "Pinjol legal?", "Cicilan 0%"],
        "related_actions": [
            {"label": "Simulasi", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "pinjol_aman_untuk_mahasiswa",
        "module": "M2_pinjol",
        "keywords": ["mahasiswa", "mahasiswi", "anak", "kuliah", "kampus", "pinjol", "aman", "rekomendasi"],
        "patterns": ["pinjol aman untuk mahasiswa", "rekomendasi pinjol mahasiswa"],
        "answer": "**Rekomendasi pinjol untuk mahasiswa** (WAJIB baca):\n\n**🏆 Opsi AMAN** (untuk dana darurat, bukan lifestyle):\n- **Shopee Paylater / Tokopedia Paylater** - 0% untuk transaksi, bunga rendah setelahnya\n- **OVO Paylater** - jika sudah approved, limit kecil dulu\n- **Kartu kredit mahasiswa** (bank) - edukasi keuangan via bank\n\n**🚫 JANGAN** (high risk untuk mahasiswa):\n- **Pinjol ilegal** (bunga 0.8-2%/hari) - bisa tagih keluarga\n- **Akulaku Kredit Pintar** - sering over-limit诱惑\n- **Limit tinggi instant** - godaan lifestyle\n\n**Tips mahasiswa**:\n1. **Maksimal pinjam** = 1x uang saku/bulan\n2. **Bayar penuh** sebelum jatuh tempo (jangan minimum payment)\n3. **Jangan pinjam untuk**: party, fashion, konser\n4. **OK pinjam untuk**: buku, laptop, kebutuhan kuliah produktif\n\nCek legalitas di **[Pinjol Checker](/dashboard/produk)**.",
        "suggestions": ["Pinjol legal?", "Cek skor", "Cara recovery"],
        "related_actions": [],
    },

    # --- M3 Strategi (3 new) ---
    {
        "intent": "bayar_pokok_vs_bunga",
        "module": "M3_debt_strategy",
        "keywords": ["bayar", "pokok", "bunga", "dulu", "prioritas", "mana", "utang"],
        "patterns": ["bayar pokok dulu", "pokok vs bunga"],
        "answer": "**Bayar pokok atau bunga dulu?**\n\n**Prinsip dasar**:\n- **Bayar bunga wajib** (kalau tidak, dendanya numpuk)\n- **Setelah bunga, fokus bayar pokok** (supaya utang menyusut)\n\n**Strategi konkret**:\n1. **Bayar minimum semua tagihan** dulu (jangan ada yang telat)\n2. **Pilih 1 utang fokus** (bunga TERTINGGI), bayar ekstra ke pokok\n3. **Setelah itu** → berikutnya, snowball effect\n\n**Contoh**:\n- Tagihan A: min Rp 200.000, bayar 200rb (bunga handled)\n- Tagihan B: min Rp 300.000, bayar 1.000.000 → 700rb ke pokok\n- Sisakan 700rb untuk ditabung/darurat\n\n**Jangan pernah**: hanya bayar minimum di semua tagihan (utang tidak akan turun).\n\nLihat **[Debt Planner](/dashboard/produk)** untuk simulasi.",
        "suggestions": ["Snowball vs Avalanche", "Cara recovery", "Auto debit"],
        "related_actions": [
            {"label": "Debt Planner", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "restrukturisasi_pengertian",
        "module": "M3_debt_strategy",
        "keywords": ["restrukturisasi", "pengertian", "apa", "itu", "arti", "definisi"],
        "patterns": ["apa itu restrukturisasi", "pengertian restrukturisasi"],
        "answer": "**Restrukturisasi utang** = negosiasi mengubah syarat pembayaran (lebih ringan):\n\n**Jenis restrukturisasi**:\n1. **Perpanjangan tenor**: 12 bulan → 24 bulan (cicilan lebih kecil)\n2. **Penurunan bunga**: 24%/tahun → 12%/tahun (total bayar lebih kecil)\n3. **Penghapusan denda**: denda telat Rp 500.000 → dihapus\n4. **Grace period**: 3 bulan bayar bunga saja, pokok mulai bulan 4\n5. **Konsolidasi**: gabung 3 utang jadi 1 (bunga lebih rendah)\n\n**Yang bisa dinegosiasi**:\n- Bunga (turun dari 0.3%/hari ke 0.15%/hari?)\n- Tenor (dari 6 bulan ke 12 bulan?)\n- Admin fee (dihapus?)\n- Denda (50% off?)\n\n**Yang TIDAK bisa dinegosiasi**:\n- Pokok utang (nilai asli)\n- Status di SLIK OJK (tetap tercatat)\n\n**[AI Coach](/dashboard/produk)** untuk template negosiasi.",
        "suggestions": ["Cara negosiasi", "Konsolidasi utang", "Snowball vs Avalanche"],
        "related_actions": [],
    },
    {
        "intent": "konsolidasi_dengan_keluarga",
        "module": "M3_debt_strategy",
        "keywords": ["konsolidasi", "keluarga", "orang", "tua", "ortu", "teman", "pinjam", "keluarga", "gabung"],
        "patterns": ["konsolidasi dengan keluarga", "pinjam keluarga untuk bayar utang"],
        "answer": "**Konsolidasi dengan keluarga** - boleh, tapi penuh risiko:\n\n**Pro**:\n- ✅ Bunga = 0% (atau 0,5%/tahun = family rate)\n- ✅ Tenor fleksibel (tidak ada pressure dari bank)\n- ✅ Tekanan psikologis berkurang\n\n**Kontra**:\n- ❌ **Relasi keluarga rusak** kalau tidak bisa bayar\n- ❌ **Trust hilang** seumur hidup\n- ❌ **Malu** kalau diomeli saat gathering keluarga\n- ❌ **Tidak ada legal protection** (kalau dispute, ga bisa ke pengadilan)\n\n**Best practices** kalau mau:\n1. **Tulis perjanjian** (meskipun informal): nominal, tenor, jadwal bayar\n2. **Bayar tepat waktu** - lebih penting dari bank!\n3. **Jangan pinjam dari yang ga mampu** (orang tua yang pensiun, misalnya)\n4. **Sampaikan jumlah realistis** - jangan sembunyikan\n\n**Alternatif**: coba **[Konsolidasi pinjol legal OJK](/dashboard/produk)** dulu sebelum pinjam keluarga.\n\n**[AI Coach](/dashboard/produk)** untuk strategi.",
        "suggestions": ["Snowball vs Avalanche", "Konsolidasi pinjol", "Cara recovery"],
        "related_actions": [],
    },

    # --- M4 DC Negotiation (4 new) ---
    {
        "intent": "dc_telpon_malam",
        "module": "M4_dc_negotiation",
        "keywords": ["dc", "telpon", "malam", "pagi", "subuh", "kapan", "waktu", "jam"],
        "patterns": ["dc telpon malam", "dc telpon subuh"],
        "answer": "**DC telpon malam / subuh / hari libur** - ini LEGAL atau ILEGAL?\n\n**❌ ILEGAL** (melanggar UU PDP & etika):\n- Telpon **malam hari** (>21:00)\n- Telpon **subuh** (<07:00)\n- Telpon **hari Minggu / libur nasional**\n- Telpon **berkali-kali** dalam 1 jam (>3x)\n- **Ancaman atau intimidasi** dalam telpon\n- **Memaksa** pembayaran instan\n\n**✅ LEGAL** (waktu yang wajar):\n- Telpon **pukul 08:00-20:00** (jam kerja)\n- **Maks 1-2x sehari** (bukan spam)\n- **Sopan & profesional**\n- **Reminder tagihan** (bukan ancaman)\n\n**Jika DC langgar**:\n1. **Screenshot** semua bukti (chat, log telpon, rekaman)\n2. **Lapor OJK** (157) & **Kominfo** (aduankonten.id)\n3. **Polisi cyber crime** (cybercrime@polri.go.id)\n\nLatihan di **[DC Chat Simulator](/tools/dc-simulator)** - gratis!",
        "suggestions": ["DC agresif", "Cara nego DC", "Lapor DC ilegal"],
        "related_actions": [
            {"label": "DC Simulator", "href": "/tools/dc-simulator"},
        ],
    },
    {
        "intent": "dc_datang_kerumah",
        "module": "M4_dc_negotiation",
        "keywords": ["dc", "datang", "rumah", "kantor", "tempat", "kerja", "penagihan", "tatap", "muka"],
        "patterns": ["dc datang ke rumah", "dc datang ke kantor"],
        "answer": "**DC datang ke rumah / kantor** - ini TINDAKAN LEGAL?\n\n**Boleh (LEGAL)**:\n- ✅ DC **resmi** dari perusahaan terdaftar (bawa ID card + surat tugas)\n- ✅ Datang di **jam kerja** (08:00-17.00)\n- ✅ **Bersikap sopan**, tidak mengancam\n- ✅ **Tujuan**: konfirmasi domisili atau negosiasi\n\n**Tidak boleh (ILEGAL)**:\n- ❌ **Paksa masuk** rumah tanpa izin\n- ❌ **Ancam di depan** tetangga / rekan kerja\n- ❌ **Bawa preman / debt collector liar**\n- ❌ **Intimidasi fisik** atau barang berharga disita\n- ❌ **Sebar data** ke orang sekitar\n\n**Yang harus Anda lakukan**:\n1. **Minta ID card & surat tugas** - WAJIB\n2. **Rekam** (audio/video) untuk dokumentasi\n3. **Jangan bayar** di tempat (tunai ke DC liar = fraud)\n4. **Minta waktu 7 hari** untuk cek legalitas\n5. **Hubungi OJK** (157) kalau ada yang mencurigakan\n\nLatihan di **[DC Chat Simulator](/tools/dc-simulator)**.",
        "suggestions": ["DC agresif", "Cara nego DC", "Lapor DC ilegal"],
        "related_actions": [],
    },
    {
        "intent": "dc_minimal_tagihan",
        "module": "M4_dc_negotiation",
        "keywords": ["dc", "minta", "minimal", "tagihan", "bayar", "berapa", "minimum"],
        "patterns": ["dc minta minimal bayar", "minimum bayar dc"],
        "answer": "**DC minta bayar minimal** - ini trik atau legitimate?\n\n**Trik umum DC**:\n- **\"Bayar minimal 30%\"** - ini TIDAK ada aturannya. Pinjol tidak boleh paksa nominal tertentu.\n- **\"Bayar sekarang, sisanya nanti\"** - biasanya DC lupa follow up, Anda rugi sudah bayar sebagian\n- **\"Bayar cash ke rekening pribadi\"** - BAHAYA, fraud!\n\n**Yang legitimate**:\n- DC hanya boleh **ingatkan tagihan** (tidak paksa nominal)\n- Anda yang **menentukan** mau bayar berapa\n- Pembayaran harus ke **rekening resmi perusahaan** (bukan pribadi)\n\n**Strategi aman**:\n1. **Jangan bayar parsial** tanpa konfirmasi restrukturisasi tertulis\n2. **Minta surat perjanjian** via email sebelum transfer\n3. **Verifikasi** ke customer service resmi (bukan cuma DC ini)\n4. **Sisihkan** dulu, bayar sekaligus kalau deal sudah final\n\nLatihan role-play di **[DC Chat Simulator](/tools/dc-simulator)**.",
        "suggestions": ["DC agresif", "Cara nego DC", "Template chat"],
        "related_actions": [],
    },
    {
        "intent": "kirim_bukti_transfer_palsu",
        "module": "M4_dc_negotiation",
        "keywords": ["bukti", "transfer", "palsu", "fake", "foto", "edit", "tipu", "dc"],
        "patterns": ["kirim bukti transfer palsu", "fake bukti transfer"],
        "answer": "**Kirim bukti transfer palsu ke DC** - ini BANYAK yang tanya. Jawabnya:\n\n**❌ JANGAN PERNAH. Ini ilegal & sangat berisiko.**\n\n**Konsekuensi hukum**:\n- **UU ITE Pasal 35**: pemalsuan dokumen elektronik = pidana **12 tahun**\n- **Pasal 263 KUHP**: pemalsuan surat = pidana **6 tahun**\n- **Bisa dituntut** oleh pinjol + DC + bahkan pihak ketiga yang dirugikan\n- **SLIK OJK** akan record ini sebagai fraud\n\n**Konsekuensi lain**:\n- ❌ **DC akan cek mutasi** rekening Anda (bisa dalam 1 jam)\n- ❌ **Tagihan naik** karena denda 'telat bayar'\n- ❌ **Hilang kesempatan** restrukturisasi di masa depan\n- ❌ **Kasus serius**: bisa masuk **pidana penipuan**\n\n**Yang benar kalau belum ada uang**:\n- ✅ **Jujur** bilang belum bisa bayar sekarang\n- ✅ **Tawarkan** tanggal spesifik yang PASTI bisa\n- ✅ **Minta** keringanan / restrukturisasi\n- ✅ **Jangan transfer** ke rekening pribadi DC (fraud detection)\n\n**[AI Coach](/dashboard/produk)** untuk negosiasi yang benar.",
        "suggestions": ["DC agresif", "Cara nego DC", "Template chat"],
        "related_actions": [],
    },

    # --- M5 Recovery (3 new) ---
    {
        "intent": "recovery_tanpa_kerja",
        "module": "M5_recovery",
        "keywords": ["recovery", "tanpa", "kerja", "nganggur", "pengangguran", "dipecat", "phk"],
        "patterns": ["recovery tanpa kerja", "galbay tapi nganggur"],
        "answer": "**Recovery dari galbay TANPA kerja / PHK** - ini skenario terberat:\n\n**Yang harus dilakukan**:\n\n**Minggu 1-2 (Darurat)**:\n- ✅ **Stop** semua payment (kecuali yang tagihan telat >30 hari)\n- ✅ **Hubungi** semua pinjol via email: \"saya PHK, mohon restrukturisasi 6-12 bulan\"\n- ✅ **Lapor** Dinas Tenaga Kerja (minta pesangon resmi)\n- ✅ **Cek** BPJS Ketenagakerjaan (claim JHT)\n\n**Minggu 3-4 (Survival)**:\n- ✅ **Pinjol ilegal** (kalau ada): fokus hukum, jangan bayar\n- ✅ **Pinjol legal**: negosiasi restrukturisasi (bunga 0%, tenor panjang)\n- ✅ **Income darurat**: jualan online, freelance, kerja serabutan\n\n**Bulan 2-6**:\n- ✅ **Side hustle** sampai income > 2x pengeluaran\n- ✅ **Mulai bayar** utang yang paling kecil (snowball)\n\nLihat **[Recovery Roadmap](/dashboard/produk)** untuk plan detail.",
        "suggestions": ["Cara recovery", "DC agresif", "Snowball vs Avalanche"],
        "related_actions": [],
    },
    {
        "intent": "recovery_setelah_phk",
        "module": "M5_recovery",
        "keywords": ["setelah", "phk", "pecat", "berhenti", "diberhentikan", "recovery", "setelah"],
        "patterns": ["recovery setelah phk", "setelah dipecat"],
        "answer": "**Recovery setelah PHK (Pemutusan Hubungan Kerja)**:\n\n**Minggu 1 (Urgensi)**:\n- ✅ Klaim **JHT** BPJS Ketenagakerjaan (uang tunai pesangon)\n- ✅ Klaim **JP** (Jaminan Pensiun) jika usia 55+\n- ✅ Cek **asuransi** yang ada benefit PHK\n- ✅ **Stop** semua payment non-essential\n\n**Minggu 2 (Komunikasi)**:\n- ✅ **Email** semua pinjol: \"saya baru PHK, mohon keringanan 50-100%\"\n- ✅ **Bank**: minta restrukturisasi KTA (biasanya disetujui karena Anda masih punya histori baik)\n- ✅ **Negosiasi** tempo 6-12 bulan grace period\n\n**Bulan 2-6 (Recovery)**:\n- ✅ **Side hustle** (ojol, freelance, jualan online)\n- ✅ **Apply** lowongan baru (target: income 1.5x pengeluaran)\n- ✅ **Bayar** utang yang paling kecil dulu (snowball)\n\n**Tips penting**:\n- ❌ **Jangan pinjam** baru untuk bayar yang lama\n- ✅ **Jujur** ke keluarga, jangan sembunyikan\n- ✅ **Cari konseling** gratis (RSJ, LSM)\n\n**[AI Coach](/dashboard/produk)** untuk strategi personal.",
        "suggestions": ["Cara recovery", "Snowball", "Konsolidasi"],
        "related_actions": [],
    },
    {
        "intent": "mulai_nabung_sedikit",
        "module": "M5_recovery",
        "keywords": ["nabung", "menabung", "sedikit", "kecil", "mulai", "dari", "nol", "emergency", "fund"],
        "patterns": ["mulai nabung sedikit", "nabung dari nol"],
        "answer": "**Mulai nabung dari Rp 0** (atau Rp 50.000) - bisa kok:\n\n**Prinsip**:\n- ✅ **Nabung = bayar diri sendiri** (prioritas, bukan sisa)\n- ✅ **Mulai kecil** (Rp 50.000/bulan sudah valid)\n- ✅ **Otomatis** (auto-debit, ga terasa)\n- ✅ **Pisah rekening** (jangan satu sama belanja)\n\n**Strategi**:\n1. **Buka rekening terpisah** (bebas admin, misal: Jenius, Jago)\n2. **Auto-debit** Rp 50.000/minggu (lebih sering = lebih terasa)\n3. **Pakai amplop** untuk 'tabungan fisik' (visual reinforcement)\n4. **Round-up** belanja (misal: belanja Rp 47.500, auto save Rp 2.500)\n\n**Target realistis**:\n- **Rp 500.000** = 2 bulan\n- **Rp 1.000.000** = 4 bulan\n- **Rp 5.000.000** (emergency fund 1 bulan) = 1-2 tahun\n\n**[Emergency Runway](/tools/emergency-runway)** untuk hitung kebutuhan.\n\n**[AI Coach](/dashboard/produk)** untuk strategi personal.",
        "suggestions": ["Emergency Runway", "Auto debit", "Cara recovery"],
        "related_actions": [],
    },

    # --- M6 Hukum (3 new) ---
    {
        "intent": "lapor_pinpol_berapa_lama",
        "module": "M6_legal_rights",
        "keywords": ["lapor", "pinpol", "berapa", "lama", "proses", "respon", "waktu", "hari"],
        "patterns": ["lapor pinjol berapa lama", "proses laporan ojk"],
        "answer": "**Lapor pinjol ilegal ke OJK - berapa lama prosesnya?**\n\n**Tahapan**:\n1. **Hari 1-7**: Lapor via [OJK](https://www.ojk.go.id) atau 157 (call center)\n2. **Minggu 1-2**: OJK verifikasi data & perusahaan pinjol\n3. **Bulan 1-3**: OJK investigasi & pemanggilan\n4. **Bulan 3-6**: Sanksi administratif (denda, cabut izin) atau **pidana** (jika terbukti)\n\n**Yang mempercepat**:\n- ✅ Bukti lengkap (screenshot, kwitansi, chat log)\n- ✅ Banyak korban (laporan kolektif)\n- ✅ Kasus berulang (DC sebar data, ancaman)\n\n**Yang TIDAK otomatis**:\n- ❌ OJK tidak otomatis freeze tagihan Anda\n- ❌ Pinjol tidak otomatis ganti rugi\n- ❌ SLIK tidak otomatis bersih (harus proses pengadilan)\n\n**Untuk pinjol legal** (bukan ilegal): lapornya ke **YLBHI** atau **LSM konsumen** untuk mediasi.\n\n**[AI Coach](/dashboard/produk)** untuk template laporan.",
        "suggestions": ["Lapor DC ilegal", "Pinjol ilegal?", "Hukum pinjol"],
        "related_actions": [],
    },
    {
        "intent": "hak_refuse_dc",
        "module": "M6_legal_rights",
        "keywords": ["hak", "tolak", "refuse", "menolak", "dc", "debt", "collector", "bohong"],
        "patterns": ["hak menolak dc", "bisa menolak dc"],
        "answer": "**Hak MENOLAK DC** - apa saja yang boleh Anda tolak?\n\n**Anda BOLEH menolak**:\n- ❌ **Bayar tanpa surat resmi** (minta surat dulu!)\n- ❌ **Bayar ke rekening pribadi** (hanya rekening perusahaan)\n- ❌ **Memberi akses** ke kontak, foto, gallery\n- ❌ **Pertemuan di tempat** yang tidak Anda sukai\n- ❌ **Telpon di luar jam kerja** (>20:00 atau <08:00)\n- ❌ **Menandatangan dokumen** tanpa Anda baca dulu\n- ❌ **Memberikan data sensitif** (KK, NPWP, foto selfie)\n- ❌ **DC menggunakan bahasa** kasar / ancaman\n\n**Anda TIDAK boleh menolak**:\n- ❌ **Komunikasi total** (jangan block, masih harus dengar)\n- ❌ **Mengingkari utang** (tetap harus bayar, negosiasi saja)\n- ❌ **Pindah alamat** tanpa kasih tahu (ilegal)\n\n**[DC Chat Simulator](/tools/dc-simulator)** untuk latihan.",
        "suggestions": ["DC agresif", "Cara nego DC", "Hukum pinjol ilegal"],
        "related_actions": [
            {"label": "DC Simulator", "href": "/tools/dc-simulator"},
        ],
    },
    {
        "intent": "pembelaan_diri_di_pengadilan",
        "module": "M6_legal_rights",
        "keywords": ["pembelaan", "diri", "pengadilan", "kartu", "tipis", "hukum", "saya", "tidak", "mampu"],
        "patterns": ["pembelaan diri di pengadilan", "tidak mampu bayar di pengadilan"],
        "answer": "**Pembelaan diri di pengadilan untuk gagal bayar** - opsi hukum Anda:\n\n**1. Mediasi** (WAJIB sebelum sidang):\n- Biasanya pinjol mau damai kalau Anda tunjukkan itikad baik\n- Hasil: restrukturisasi, keringanan, atau waktu lebih lama\n- **70% kasus** mediasi menghasilkan deal\n\n**2. Eksepsi / Keberatan**:\n- **Pinjol ilegal**: Anda bisa tuntut balik (pemerasan, penyalahgunaan data)\n- **Bunga melebihi aturan**: Anda minta bunga direduksi\n- **DC nakal**: bukti intimidasi = pidana untuk DC\n\n**3. Pembuktian kemampuan**:\n- Tunjukkan **slip gaji** / surat keterangan tidak mampu\n- Tunjukkan **beban utang** total (bukan hanya 1 pinjol)\n- Minta **cicilan ringan** yang realistis\n\n**Tips**:\n- ✅ **Hire pengacara** (banyak yang pro-bono di YLBHI)\n- ✅ **Siapkan semua dokumen** - rapi + kronologis\n- ✅ **Jangan bohong** - hakim bisa detect\n\n**[AI Coach](/dashboard/produk)** untuk strategi mediasi.",
        "suggestions": ["Hukum pinjol ilegal", "Lapor DC", "Cara recovery"],
        "related_actions": [],
    },

    # --- M7 App Rec (3 new) ---
    {
        "intent": "aplikasi_gratis_alternatif",
        "module": "M7_app_rec",
        "keywords": ["aplikasi", "gratis", "alternatif", "pengganti", "mirip", "budgeting", "keuangan", "app"],
        "patterns": ["aplikasi gratis alternatif", "alternatif aplikasi budgeting"],
        "answer": "**Aplikasi gratis alternatif** untuk tracking keuangan:\n\n**🇮🇩 Indonesia**:\n- **Money Lover** - multi-account, IDR\n- **Catatan Keuangan** - simple, no ads\n- **Wallet** - simple UI, IDR\n- **Finansialku** - komunitas + budget\n- **TMRW (Tomorrow)** - Gen Z vibe, dark mode\n\n**🌍 Global**:\n- **Wallet by BudgetBakers** - 250+ bank sync\n- **Monefy** - offline, sync ke cloud\n- **Bluecoins** - powerful, free\n- **Spendee** - visual, colorful\n\n**Bedanya dengan Galbay Predictor**:\n- ✅ Galbay fokus **pencegahan** (bukan tracking)\n- ✅ AI Coach untuk **decision support**\n- ✅ **Risk scoring** personal\n- ✅ **Recovery tools** (snowball, negosiasi, DC simulator)\n\n**[Galbay Score](/galbay-score)** - gratis, tanpa login!",
        "suggestions": ["Cek skor", "Premium dapat apa?", "Cara pakai website"],
        "related_actions": [],
    },
    {
        "intent": "blu_jago_seabank_beda",
        "module": "M7_app_rec",
        "keywords": ["blu", "jago", "seabank", "neo", "bank", "digital", "beda", "mana", "bagus"],
        "patterns": ["blu jago seabank beda", "bank digital terbaik"],
        "answer": "**BLU vs Jago vs SeaBank** - bank digital comparison:\n\n| Fitur | blu (BCA) | Jago | SeaBank |\n|---|---|---|---|\n| **Bunga tabungan** | 3-4%/thn | 3-5%/thn | 4-6%/thn (paling tinggi) |\n| **Min saldo** | Rp 10.000 | Rp 0 | Rp 0 |\n| **Biaya admin** | Gratis | Gratis | Gratis |\n| **Transfer** | Gratis ke BCA | Gratis antar bank (beberapa) | Gratis |\n| **Limit harian** | Rp 50 juta | Rp 1 miliar | Rp 1 miliar |\n| **Parent** | BCA Digital | Bank Jago (Michel Khairi) | Bank Seabank Indonesia |\n| **Best for** | User BCA existing | Cash management UMKM | High yield saving |\n\n**Rekomendasi**:\n- **Suka BCA + cashback**: blu\n- **Bisa Investasi + reksa dana**: Jago\n- **Mau bunga tabungan tinggi**: SeaBank\n\n**Tips**: Punya 2-3 bank digital **jangan** sekaligus - susah tracking!\n\n**[Galbay Score](/galbay-score)** untuk evaluasi personal.",
        "suggestions": ["Aplikasi gratis alternatif", "Cek skor", "Cara recovery"],
        "related_actions": [],
    },
    {
        "intent": "kartu_kredit_vs_paylater",
        "module": "M7_app_rec",
        "keywords": ["kartu", "kredit", "vs", "paylater", "bandingkan", "beda", "mana", "bagus"],
        "patterns": ["kartu kredit vs paylater", "bandingkan kartu kredit paylater"],
        "answer": "**Kartu Kredit vs Paylater** - mana yang lebih aman?\n\n**Kartu Kredit**:\n- ✅ Limit besar (Rp 5-100 juta)\n- ✅ Cicilan 0% untuk merchant tertentu (sampai 24 bulan)\n- ✅ Reward point / cashback\n- ✅ **Perlindungan konsumen** lebih kuat (UU Kartu Kredit)\n- ❌ **Annual fee** Rp 100-500rb/tahun\n- ❌ Bunga tinggi kalau telat (~2.5-3.5%/bulan)\n- ❌ **Seleksi ketat** (gampang ditolak kalau belum stable)\n\n**Paylater**:\n- ✅ **Tanpa annual fee**\n- ✅ **Approval mudah** (instant)\n- ✅ **Limit kecil** (Rp 500rb - 5 juta) - \"lebih terkontrol\"\n- ❌ **Bunga tinggi** (~2.6%/bulan = Shopee Paylater)\n- ❌ Perlindungan konsumen **lebih lemah**\n- ❌ **DC lebih agresif** untuk tagihan kecil\n\n**Rekomendasi**:\n- **Budget < Rp 5 juta/bulan**: Paylater (limit terkontrol)\n- **Budget > Rp 5 juta/bulan**: Kartu Kredit (proteksi lebih baik)\n- **Selalu bayar PENUH** sebelum jatuh tempo (jangan minimum!)\n\n**[Pinjol Checker](/dashboard/produk)** - cek legalitas sebelum daftar.",
        "suggestions": ["Cek pinjol legal", "Bunga wajar?", "Aplikasi gratis"],
        "related_actions": [],
    },

    # --- M8 Mental Health (2 new) ---
    {
        "intent": "konseling_gratis_online",
        "module": "M8_mental_health",
        "keywords": ["konseling", "gratis", "online", "psikolog", "tempat", "curhat", "stress", "galbay"],
        "patterns": ["konseling gratis online", "konseling online gratis"],
        "answer": "**Konseling gratis online** untuk stress finansial:\n\n**🇮🇩 Indonesia**:\n- **YLBHI** (Yayasan Lembaga Bantuan Hukum Indonesia) - hukum + keuangan gratis\n- **Sejiwa** (119 ext 8) - hotline krisis 24/7\n- **Kemenkes** (Halo Kemenkes 1500567) - kesehatan jiwa\n- **Into The Light** - depresi & bunuh diri prevention\n- **LSM Consumidor**: perlindungan konsumen\n\n**🌐 Global (online)**:\n- **7 Cups** (7cups.com) - free chat dengan listener\n- **BetterHelp** (trial gratis) - video call psikolog\n- **Calm** (meditation app, free tier) - stress management\n- **Mindful** - latihan mindfulness gratis\n\n**Untuk Gen Z Indonesia**:\n- **Yayasan Pulih** - trauma healing\n- **JAGA** (Jaringan dukungan Kesehatan Jiwa) - chat & forum\n- **Bicarakan.id** - 1-on-1 chat dengan psikolog (free trial)\n\n**Mulai dari AI Coach dulu**: [Galbay AI Coach](/dashboard/produk) - gratis, 24/7.",
        "suggestions": ["Stress finansial", "Konseling berapa", "Self harm"],
        "related_actions": [],
    },
    {
        "intent": "meditasi_untuk_stres_finansial",
        "module": "M8_mental_health",
        "keywords": ["meditasi", "meditation", "stress", "finansial", "cemas", "tenang", "calm", "teknik", "napas"],
        "patterns": ["meditasi untuk stress finansial", "cara menenangkan pikiran dari utang"],
        "answer": "**Meditasi untuk stress finansial** - 5 teknik cepat:\n\n**1. Box Breathing (4-4-4-4)** - 1 menit:\n- Tarik napas 4 detik\n- Tahan 4 detik\n- Buang 4 detik\n- Tahan 4 detik\n- Ulangi 4x\n\n**2. 5-4-3-2-1 Grounding** - 3 menit:\n- 5 hal yang **bisa Anda LIHAT**\n- 4 hal yang **bisa Anda SENTUH**\n- 3 hal yang **bisa Anda DENGAR**\n- 2 hal yang **bisa Anda CIUM**\n- 1 hal yang **bisa Anda RASAKAN**\n\n**3. Body Scan** - 5 menit:\n- Duduk / berbaring\n- Mulai dari kaki, 'scan' ke atas\n- Sadari setiap bagian tanpa menghakimi\n- Lepaskan tegang di setiap area\n\n**4. Affirmation** (ulang 3x):\n- \"Saya sudah berusaha. Itu sudah cukup.\"\n- \"Saya akan memilih 1 langkah kecil hari ini.\"\n- \"Ini hanya sementara. Saya akan melewatinya.\"\n\n**5. Journaling** (5 menit):\n- Tulis 3 hal yang Anda syukuri (bukan masalah!)\n- Tulis 1 langkah kecil yang bisa Anda ambil HARI INI\n\n**[AI Coach](/dashboard/produk)** untuk dipandu via chat.\n\n**Kritis?** Hubungi **Sejiwa 119 ext 8** (24/7).",
        "suggestions": ["Stress finansial", "Konseling gratis online", "Konsultan"],
        "related_actions": [],
    },
    {
        "intent": "dukungan_keluarga",
        "module": "M8_mental_health",
        "keywords": ["dukungan", "keluarga", "bicara", "orang", "tua", "pasangan", "teman", "curhat", "stress"],
        "patterns": ["dukungan keluarga saat galbay", "cara cerita ke keluarga"],
        "answer": "**Dukungan keluarga saat galbay** - cara cerita:\n\n**Kenapa harus cerita?**:\n- ✅ **Beban psikologis** turun 50% setelah cerita\n- ✅ Keluarga bisa jadi **financial support** (tidak selalu uang!)\n- ✅ **Cegah depresi** & keputusan impulsif\n\n**Cara cerita** (script):\n1. **Pilih waktu** yang tenang (makan malam, weekend)\n2. **Mulai dari fakta**: \"Saya mau cerita sesuatu. Saya punya utang Rp X juta.\"\n3. **Jangan minta uang dulu** - minta dukungan emosional dulu\n4. **Tunjukkan plan**: \"Saya sudah punya strategi [snowball/avalanche]. Saya butuh support.\"\n5. **Minta spesifik**: \"Bisa tolong ingetin saya untuk bayar tanggal 25?\"\n\n**Yang harus dihindari**:\n- ❌ **Cerita pas panik** - bikin semua panik\n- ❌ **Minta full payment** - terlalu berat\n- ❌ **Sembunyikan terus** - makin buruk lama-lama\n\n**Untuk ortu yang strict**:\n- Pilih momen **success kecil** (misal: \"Saya sudah lunasi 1 tagihan!\")\n- Baru ceritakan sisanya.\n\n**[AI Coach](/dashboard/produk)** bisa jadi curhat pertama sebelum cerita ke keluarga.",
        "suggestions": ["Stress finansial", "Konseling gratis", "Konsolidasi keluarga"],
        "related_actions": [],
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
                    if ratio >= 0.8:
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

    # Smart fallback: if best confidence < 0.1, return default + suggest top 3 closest
    if conf < 0.1:
        fallback = FAQ_KB[-1]  # default_fallback
        # Augment the default fallback with the top 3 closest intents
        if scored:
            top3 = scored[:3]
            suggestions = []
            for e, s in top3:
                # Get the first suggestion from each close entry, or use the intent name
                entry_suggestions = e.get("suggestions", [])
                if entry_suggestions:
                    suggestions.append(entry_suggestions[0])
            if suggestions:
                # Update default_fallback suggestions
                fallback = {**fallback, "suggestions": suggestions[:4]}

        return fallback, conf, secondary

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


# =================================================================
# TOOLS: DC Chat Simulator (Multi-Turn v2)
# =================================================================
# Each scenario is a sequence of turns. User picks an option (A/B/C/D)
# per turn. DC responds. After last turn, scoring happens based on
# accumulated criteria.
DC_SCENARIOS: list[dict] = [
    {
        "id": "agresif_tekan",
        "title": "DC Tekanan Agresif",
        "difficulty": "Mudah",
        "description": "DC nelpon teriak-teriak, minta bayar hari ini juga. Anda harus tetap tenang dan negosiasi.",
        "tone": "agresif",
        "key_points": [
            "Tetap tenang, jangan emosional",
            "Akui ada tanggungan tanpa janji bayar",
            "Minta bukti identitas & tagihan resmi",
            "Tawarkan negosiasi restrukturisasi, bukan penolakan",
        ],
        "evaluation_criteria": {
            "calm": "Tetap tenang & profesional",
            "verify": "Minta bukti identitas/tagihan",
            "negotiate": "Tawarkan solusi (bukan sekadar tolak/bayar)",
            "no_threat": "Tidak mengancam balik",
        },
        "turns": [
            {
                "dc_message": "Pak/Bu, ini dari [nAMA PINJOL]. Saya sudah tunggu 2 minggu. Bayar SEKARANG juga! Kalau tidak, saya sebar data Anda ke semua kontak. Teman, keluarga, semua tau Anda penipu!",
                "options": [
                    {"label": "A. Teriak balik: 'Lo jangan ganggu keluarga saya! Saya akan lapor polisi!'", "score": 15, "criteria": {"calm": 0, "no_threat": 0, "negotiate": 0, "verify": 0}, "feedback": "Reaktif & emosional. DC jadi makin agresif, kasus makin sulit."},
                    {"label": "B. Tenang: 'Pak, saya terima teleponnya. Saya memang punya tanggungan. Bisa kirimkan surat tagihan resmi & nama lengkap Bapak?'", "score": 85, "criteria": {"calm": 25, "verify": 25, "negotiate": 10, "no_threat": 25}, "feedback": "Tepat! Tenang, verifikasi identitas dulu sebelum lanjut."},
                    {"label": "C. Panik: 'OK saya transfer sekarang, jangan sebar! Berapa nomornya?'", "score": 10, "criteria": {"calm": 0, "negotiate": 0, "verify": 0, "no_threat": 15}, "feedback": "Bayar di bawah tekanan = DC belajar intimidasi berhasil. Besok DC akan ancam lagi."},
                    {"label": "D. Diam & tutup telepon", "score": 25, "criteria": {"calm": 20, "no_threat": 20, "verify": 0, "negotiate": 0}, "feedback": "Menghindari bukan solusi. DC akan nelpon lagi besok dengan ancaman lebih besar."},
                ]
            },
            {
                "dc_message": "OK Pak, ini nomor saya 0812-3456-7890, nama saya Budi. Tagihan Rp 3.500.000 sudah jatuh tempo 14 hari. Gimana mau bayar berapa?",
                "options": [
                    {"label": "A. 'Saya tidak bisa bayar sama sekali.'", "score": 15, "criteria": {"negotiate": 0, "realistic": 0}, "feedback": "Terlalu defensif. DC tidak punya solusi untuk ditawarkan."},
                    {"label": "B. 'Saya bisa cicil Rp 500.000/bulan selama 7 bulan. Apakah ada keringanan bunga?'", "score": 95, "criteria": {"calm": 15, "negotiate": 25, "realistic": 25, "verify": 15}, "feedback": "Excellent! Angka spesifik, jangka waktu jelas, tawar keringanan."},
                    {"label": "C. 'Saya sudah bilang ga punya uang, yauda saya mati aja.'", "score": 5, "criteria": {"calm": 0, "negotiate": 0, "realistic": 0}, "feedback": "Self-harm. Kami akan direct ke crisis hotline."},
                    {"label": "D. 'Saya mau bayar penuh, tapi kasih saya waktu 30 hari.'", "score": 50, "criteria": {"negotiate": 20, "realistic": 10, "verify": 0}, "feedback": "Boleh, tapi tanpa keringanan bunga = Anda rugi. Selalu tawar restrukturisasi."},
                ]
            },
            {
                "dc_message": "OK Pak, cicilan Rp 500.000/bulan OK. Tapi bunganya tetap flat 10%/tahun. Deal?",
                "options": [
                    {"label": "A. 'Deal. Saya bayar mulai tanggal 25 bulan ini.'", "score": 75, "criteria": {"negotiate": 20, "specific": 25, "realistic": 15}, "feedback": "Baik. Komitmen spesifik, tapi tidak push keringanan admin."},
                    {"label": "B. 'Pak, kalau bisa bunga turun ke 6%/tahun, saya deal. Plus bebas biaya admin?'", "score": 95, "criteria": {"negotiate": 25, "specific": 20, "realistic": 25}, "feedback": "Perfect negotiation! Push untuk keringanan, tidak menyerah di deal pertama."},
                    {"label": "C. 'Ga deal, saya pikir-pikir dulu.'", "score": 30, "criteria": {"negotiate": 0, "specific": 5}, "feedback": "Menunda = DC akan ancam lagi. Ambil deal dengan keringanan tambahan."},
                    {"label": "D. 'OK, deal.'", "score": 60, "criteria": {"negotiate": 10, "specific": 20}, "feedback": "OK tapi missed opportunity untuk keringanan."},
                ]
            },
            {
                "dc_message": "OK deal Pak, bunga 6%, bebas admin, Rp 500.000/bulan mulai 25 bulan ini. Saya akan kirim surat perjanjian via email. Bukti transfer ke rekening resmi PT XYZ di bank BCA ya. Ada pertanyaan?",
                "options": [
                    {"label": "A. 'OK Pak, terima kasih. Mohon email konfirmasinya ya.'", "score": 90, "criteria": {"polite": 25, "verify": 20, "specific": 20}, "feedback": "Tepat! Konfirmasi via email untuk dokumentasi. Profesional."},
                    {"label": "B. 'OK thanks.' (langsung tutup)", "score": 40, "criteria": {"polite": 10, "verify": 5}, "feedback": "Kurang sopan. DC ingat Anda di interaksi berikutnya."},
                    {"label": "C. 'Pak, tolong juga dicancel tagihan ke kontak-kontak saya. Saya sudah dibayar.'", "score": 70, "criteria": {"polite": 15, "verify": 25, "specific": 15}, "feedback": "Penting! Minta klarifikasi sebar data sudah dihentikan. Bagus."},
                    {"label": "D. 'OK, saya transfer ke rekening atas nama pribadi ya Pak?'", "score": 10, "criteria": {"verify": 0, "polite": 5}, "feedback": "BAHAYA! Transfer ke rekening pribadi = fraud. Pastikan ke rekening perusahaan resmi."},
                ]
            },
        ],
    },
    {
        "id": "sebar_data",
        "title": "DC Ancam Sebar Data",
        "difficulty": "Sedang",
        "description": "DC ancam akan sebar foto/kontak ke semua orang. Anda punya hak hukum (UU PDP).",
        "tone": "intimidasi",
        "key_points": [
            "Jangan transfer di bawah tekanan (ini ilegal)",
            "Dokumentasikan ancaman (screenshot)",
            "Lapor ke OJK + Kominfo + polisi (cyber crime)",
            "Tegaskan hak atas data pribadi (UU PDP)",
        ],
        "evaluation_criteria": {
            "calm": "Tetap tenang tanpa panik",
            "legal": "Tahu hak hukum (UU PDP) & ancam lapor",
            "document": "Dokumentasikan ancaman",
            "no_payment": "TIDAK membayar di bawah tekanan",
        },
        "turns": [
            {
                "dc_message": "Pak, saya sudah kasih waktu 3 hari. Kalau hari ini tidak transfer Rp 2.000.000, saya akan kirim foto selfie + tagihan Anda ke semua kontak WhatsApp. Teman kerja, pacar, ortu, semua akan tau!",
                "options": [
                    {"label": "A. Panik: 'OK saya transfer sekarang, jangan sebar!'", "score": 10, "criteria": {"calm": 0, "legal": 0, "no_payment": 0}, "feedback": "Tunai di bawah tekanan. DC belajar ancaman = efektif. Akan diulangi."},
                    {"label": "B. 'Pak, ancam sebar data itu melanggar UU PDP No. 27/2022. Saya akan screenshot chat ini dan laporkan ke OJK + Kominfo + polisi. Mari bicara solusi legal.'", "score": 95, "criteria": {"calm": 25, "legal": 25, "document": 20, "no_threat": 20}, "feedback": "Perfect! Tenang, tahu UU, ancam balik dengan legal. DC gentar."},
                    {"label": "C. 'Saya tidak peduli, sebar saja.'", "score": 15, "criteria": {"calm": 5, "no_threat": 25, "legal": 0}, "feedback": "Biarin DC sebar = data Anda disebar. Tetap harus laporkan. Tenang tapi tetap report."},
                    {"label": "D. 'Pak, tolong jangan sebar, saya ada uang, transfer sekarang juga.'", "score": 5, "criteria": {"calm": 0, "legal": 0, "no_payment": 0}, "feedback": "Iniintimidasi berhasil. DC akan jadi makin agresif ke orang lain juga."},
                ]
            },
            {
                "dc_message": "Pak, tenang, kita sama-sama cari solusi. Saya bisa keringanan 20% kalau Anda bayar 50% hari ini. Deal?",
                "options": [
                    {"label": "A. 'Pak, keringanan saya hargai. Saya akan bayar 50% setelah dapat konfirmasi restrukturisasi tertulis. Boleh via email?'", "score": 90, "criteria": {"calm": 25, "negotiate": 20, "verify": 20, "document": 15}, "feedback": "Tepat! Acknowledge keringanan, minta dokumentasi. Aman."},
                    {"label": "B. 'Deal! Saya transfer 50% sekarang.'", "score": 50, "criteria": {"negotiate": 15, "no_payment": 0}, "feedback": "OK deal, tapi tanpa konfirmasi tertulis = risiko. Minta surat perjanjian dulu."},
                    {"label": "C. 'Ga deal. Saya lapor OJK sekarang juga.'", "score": 40, "criteria": {"legal": 25, "no_threat": 20}, "feedback": "Lapor OK, tapi menutup pintu negosiasi. Bisa balance: ancam lapor + tetap buka ruang negosiasi."},
                    {"label": "D. 'Pak, sebelum lanjut, bisa kirim nama lengkap, perusahaan, dan surat penagihan resmi?'", "score": 85, "criteria": {"calm": 20, "verify": 25, "document": 15}, "feedback": "Bagus! Verifikasi dulu sebelum deal. Protect yourself."},
                ]
            },
            {
                "dc_message": "OK Pak, ini surat restrukturisasi resmi dari PT XYZ. Cicilan Rp 800.000/bulan selama 3 bulan. Apakah deal?",
                "options": [
                    {"label": "A. 'Deal. Saya bayar mulai besok. Mohon email konfirmasinya.'", "score": 80, "criteria": {"polite": 15, "specific": 20, "verify": 20}, "feedback": "Bagus! Deal dengan komitmen spesifik + dokumentasi."},
                    {"label": "B. 'Deal.' (tanpa klarifikasi)", "score": 40, "criteria": {"specific": 5, "verify": 5}, "feedback": "Terlalu singkat. Selalu confirm date & method."},
                    {"label": "C. 'Pak, apakah tagihan ke kontak saya sudah dicancel? Saya butuh jaminan itu.'", "score": 90, "criteria": {"calm": 20, "verify": 25, "specific": 20}, "feedback": "Penting! Pastikan sebar data dihentikan. Ini hak Anda."},
                    {"label": "D. 'Deal. Saya transfer hari ini juga.'", "score": 35, "criteria": {"calm": 10, "verify": 5}, "feedback": "Transfer mendadak tanpa konfirmasi = risiko. Selalu minta email confirmation dulu."},
                ]
            },
        ],
    },
    {
        "id": "konsolidasi",
        "title": "DC Mau Tahu Posisi",
        "difficulty": "Mudah",
        "description": "DC nelpon sopan, tanya kemampuan bayar & tawarkan solusi.",
        "tone": "profesional",
        "key_points": [
            "Jujur tentang kondisi keuangan",
            "Sebutkan nominal yang realistis bisa dibayar",
            "Minta opsi restrukturisasi (cicilan, penundaan)",
            "Konfirmasi kesepakatan via email/surat",
        ],
        "evaluation_criteria": {
            "honest": "Jujur tentang kemampuan bayar",
            "realistic": "Nominal realistis (bukan over/under promise)",
            "negotiate": "Minta opsi (restrukturisasi/cicilan)",
            "polite": "Tetap sopan & profesional",
        },
        "turns": [
            {
                "dc_message": "Selamat pagi, saya Adi dari [nama pinjol]. Saya ditugaskan follow up tagihan Anda sebesar Rp 2.500.000 yang sudah jatuh tempo 30 hari. Bisa ceritakan posisi keuangan Anda saat ini?",
                "options": [
                    {"label": "A. 'Saya ga mau bayar sama sekali!'", "score": 5, "criteria": {"honest": 0, "polite": 0, "negotiate": 0}, "feedback": "Tidak profesional. DC tidak bisa bantu kalau Anda tidak engage."},
                    {"label": "B. 'Pak Adi, terima kasih sudah menghubungi. Jujur, income saya 4 juta, tanggungan 3, cicilan lain 1.5 juta. Saya bisa cicil Rp 300.000/bulan.'", "score": 95, "criteria": {"honest": 25, "realistic": 25, "negotiate": 20, "polite": 15}, "feedback": "Excellent! Jujur, spesifik angka, sopan, tawarkan solusi. Profesional."},
                    {"label": "C. 'Pokoknya saya ga bisa, bye.'", "score": 10, "criteria": {"polite": 0, "negotiate": 0, "honest": 0}, "feedback": "Tutup komunikasi = DC escalate ke atasan / DC kedua."},
                    {"label": "D. 'Saya mau bayar lunas, kasih saya 90 hari.'", "score": 35, "criteria": {"honest": 5, "realistic": 5, "negotiate": 15}, "feedback": "Over-promise. Kalau ga bisa bayar nanti, trust rusak & DC escalate."},
                ]
            },
            {
                "dc_message": "OK Pak, cicilan Rp 300.000/bulan. Berapa bulan tenor?",
                "options": [
                    {"label": "A. '8 bulan cukup.'", "score": 70, "criteria": {"specific": 20, "realistic": 15, "negotiate": 15}, "feedback": "Bagus, ada angka. Tapi 8 bulan = total 2.4jt dari 2.5jt tagihan, masih kurang."},
                    {"label": "B. '8 bulan, dan mohon keringanan bunga 50% ya Pak, supaya totalnya ga terlalu besar.'", "score": 95, "criteria": {"specific": 20, "realistic": 20, "negotiate": 25, "polite": 10}, "feedback": "Perfect! Negosiasi bunga + tenor spesifik."},
                    {"label": "C. 'Berapa pun bisa Pak, yang penting ga ditagih terus.'", "score": 25, "criteria": {"honest": 0, "specific": 0}, "feedback": "Terlalu pasrah. DC jadi curiga Anda ga serius."},
                    {"label": "D. 'Saya pikir dulu ya Pak.'", "score": 30, "criteria": {"specific": 0, "negotiate": 0}, "feedback": "Menunda = DC akan follow up lagi. Lebih baik commit sekarang."},
                ]
            },
            {
                "dc_message": "OK deal Pak, 8 bulan Rp 300.000/bulan, bunga flat 6%/tahun. Saya kirim surat perjanjian via email. Ada lagi yang mau ditanyakan?",
                "options": [
                    {"label": "A. 'OK Pak terima kasih banyak, sangat membantu.'", "score": 85, "criteria": {"polite": 25, "verify": 15, "specific": 15}, "feedback": "Tepat! Sopan + komitmen. Tutup dengan baik."},
                    {"label": "B. 'Pak, bisa sekalian konsolidasi dengan 2 pinjol lain saya? Saya ada 3 tagihan total 5jt.'", "score": 90, "criteria": {"polite": 15, "negotiate": 25, "specific": 20}, "feedback": "Excellent! Inisiatif konsolidasi. DC bisa connect dengan tim konsolidasi."},
                    {"label": "C. 'OK bye.' (langsung tutup)", "score": 35, "criteria": {"polite": 5, "verify": 5}, "feedback": "Kurang sopan, kesan Anda ga respect effort DC."},
                    {"label": "D. 'OK, saya transfer 5 menit lagi ya.'", "score": 30, "criteria": {"specific": 5, "verify": 5}, "feedback": "Jangan buru-buru. Confirm via email dulu sebelum transfer."},
                ]
            },
        ],
    },
    {
        "id": "emergency_kritis",
        "title": "DC di Masa Kritis",
        "difficulty": "Sulit",
        "description": "Anda benar-benar tidak punya uang. DC minta nominal realistis.",
        "tone": "negosiator",
        "key_points": [
            "Bersikap kooperatif, bukan defensif",
            "Kasih angka terkecil yang benar-benar mampu",
            "Minta keringanan bunga + admin",
            "Konfirmasi tanggal bayar yang PASTI",
        ],
        "evaluation_criteria": {
            "cooperative": "Kooperatif (bukan defensif)",
            "specific": "Kasih angka & tanggal SPESIFIK",
            "acknowledge": "Acknowledge keringanan yang ditawarkan",
            "realistic": "Tidak over-promise",
        },
        "turns": [
            {
                "dc_message": "Pak, saya tahu situasinya sulit. Tapi ini sudah 60 hari. Saya perlu tahu, kalau saya tawarkan keringanan 30%, Anda bisa bayar berapa? Kapan?",
                "options": [
                    {"label": "A. 'Saya beneran ga punya uang sama sekali.'", "score": 20, "criteria": {"cooperative": 10, "specific": 0}, "feedback": "Terlalu pesimis. DC tidak bisa bantu tanpa angka."},
                    {"label": "B. 'Pak, terima kasih keringanannya. Jujur, saya bisa bayar Rp 200.000 tanggal 25 bulan ini. Sisanya bulan depan Rp 200.000. Apakah ini cukup?'", "score": 95, "criteria": {"cooperative": 25, "acknowledge": 20, "specific": 25, "realistic": 20}, "feedback": "Perfect! Acknowledge keringanan + angka spesifik + tanggal jelas. DC setuju."},
                    {"label": "C. 'Saya tidak mau janji, kita lihat nanti aja.'", "score": 5, "criteria": {"cooperative": 0, "realistic": 0, "specific": 0}, "feedback": "Tidak ada commitment. DC tidak punya alasan untuk keringanan. Eskalasi."},
                    {"label": "D. 'Saya bisa lunas semua bulan depan.'", "score": 15, "criteria": {"realistic": 0, "cooperative": 5}, "feedback": "Over-promise. Kalau ga bisa, trust rusak parah."},
                ]
            },
            {
                "dc_message": "OK Pak, Rp 200.000 tanggal 25 ini, Rp 200.000 tanggal 25 bulan depan. Tapi bunga flat 8%/tahun. Deal?",
                "options": [
                    {"label": "A. 'Deal Pak. Saya bayar tanggal 25 ini via transfer bank. Mohon email konfirmasinya.'", "score": 90, "criteria": {"acknowledge": 20, "specific": 20, "realistic": 25, "polite": 10}, "feedback": "Sangat baik! Komitmen + tanggal spesifik + minta dokumentasi."},
                    {"label": "B. 'Pak, bisa bunga 4% aja ya, kan keringanan 30% biasanya termasuk bunga.'", "score": 80, "criteria": {"acknowledge": 15, "negotiate": 20, "specific": 20}, "feedback": "Tawar lagi! Selalu negotiate, ga ada ruginya."},
                    {"label": "C. 'Deal.' (singkat)", "score": 50, "criteria": {"specific": 15, "realistic": 15}, "feedback": "OK tapi missed opportunity + kurang profesional."},
                    {"label": "D. 'Pak, tolong juga keringanan biaya admin 50% ya.'", "score": 85, "criteria": {"acknowledge": 15, "negotiate": 25, "specific": 20}, "feedback": "Tepat! Push keringanan lebih jauh. Selalu tawar."},
                ]
            },
            {
                "dc_message": "OK Pak, deal final: Rp 200.000 x 2x tanggal 25, bunga 4%, tanpa admin. Saya kirim surat perjanjian via email hari ini. Ada pertanyaan?",
                "options": [
                    {"label": "A. 'OK Pak, terima kasih banyak. Saya akan bayar tepat waktu.'", "score": 90, "criteria": {"cooperative": 25, "acknowledge": 20, "polite": 20, "specific": 15}, "feedback": "Tepat! Komitmen, sopan, dokumentasi. Profesional."},
                    {"label": "B. 'Pak, tolong pastikan tagihan ini tidak di-escalate ke atasan kalau saya bayar tepat waktu.'", "score": 85, "criteria": {"cooperative": 20, "specific": 20, "realistic": 15}, "feedback": "Bagus! Penting memastikan tidak ada eskalasi yang tidak perlu."},
                    {"label": "C. 'OK.' (singkat)", "score": 40, "criteria": {"polite": 5, "specific": 5}, "feedback": "Terlalu singkat. DC tidak yakin Anda serius."},
                    {"label": "D. 'Pak, kalau saya telat 1-2 hari, tolong kasih tahu sebelum escalate. Saya akan bayar begitu ada.'", "score": 85, "criteria": {"cooperative": 25, "acknowledge": 15, "specific": 20}, "feedback": "Excellent! Komunikasi terbuka. Tanda kematangan finansial."},
                ]
            },
        ],
    },
]


def evaluate_dc_response(scenario: dict, user_response: str) -> dict:
    """Evaluate user response ke DC scenario (LEGACY single-turn scoring).

    Used as fallback for any scenario without 'turns' key.
    Scoring: 0-100 (4 criteria × 25 pts each).
    """
    if not user_response or len(user_response.strip()) < 5:
        return {
            "valid": False,
            "score": 0,
            "feedback": ["Respons terlalu pendek. Coba lebih detail & profesional."],
            "criteria_scores": {},
            "verdict": "Perlu Perbaikan",
            "verdict_color": "#ef4444",
            "verdict_msg": "Respons minimal. Latih dengan role-play atau template.",
        }

    text = user_response.lower().strip()
    criteria = scenario.get("evaluation_criteria", {})
    scores: dict[str, int] = {}
    feedback_parts: list[str] = []

    # Calm check
    is_calm = (
        not any(w in text.upper() * 3 for w in text.split() if len(w) > 3)
        and not any(p in text for p in ["babi", "anjir banget", "bodoh", "tolol", "bangsat"])
    )
    if "calm" in criteria:
        scores["calm"] = 25 if is_calm else 10
        if not is_calm:
            feedback_parts.append("⚠️ Tetap tenang — DC sering provoke emosi. Jangan teriak balik.")

    # Legal/verify
    has_legal = any(kw in text for kw in [
        "identitas", "kartu pengenal", "ktp", "kartu nama",
        "uu pdp", "uu ite", "ojk", "kominfo", "polisi", "polisi cyber",
        "bukti", "tagihan resmi", "surat",
    ])
    if "verify" in criteria or "legal" in criteria:
        key = "verify" if "verify" in criteria else "legal"
        scores[key] = 25 if has_legal else 5
        if not has_legal:
            feedback_parts.append("📋 Selalu minta bukti identitas & surat tagihan resmi. DC ilegal sering tanpa dokumen.")

    # Negotiate
    has_negotiate = any(kw in text for kw in [
        "restrukturisasi", "cicil", "cicilan", "keringanan", "jadwal",
        "bayar sebagian", "parsial", "分期", "bertahap", "30%", "50%",
        "restruk", "diskon",
    ])
    if "negotiate" in criteria or "cooperative" in criteria:
        key = "negotiate" if "negotiate" in criteria else "cooperative"
        scores[key] = 25 if has_negotiate else 8
        if not has_negotiate:
            feedback_parts.append("🤝 Tawarkan solusi konkret (restrukturisasi, cicilan, keringanan), bukan sekadar tolak atau iya.")

    # Document
    has_doc = any(kw in text for kw in [
        "screenshot", "dokumentasi", "rekam", "bukti chat", "simpan",
        "record", "saya rekam",
    ])
    if "document" in criteria:
        scores["document"] = 25 if has_doc else 8
        if not has_doc:
            feedback_parts.append("📸 Dokumentasikan ancaman (screenshot) untuk bukti pelaporan.")

    # No payment under threat
    has_no_pay = not any(kw in text for kw in [
        "ok saya transfer", "ok saya bayar", "siap transfer", "transfer sekarang",
        "bayar sekarang juga",
    ])
    if "no_payment" in criteria:
        scores["no_payment"] = 25 if has_no_pay else 0
        if not has_no_pay:
            feedback_parts.append("🚨 Jangan bayar di bawah ancaman! Itu ilegal. Anda punya hak untuk negosiasi fair.")

    # Honest / specific
    has_specific = bool(re.search(r"\d+\s*(juta|ribu|rb|jt|k|%)", text)) or any(
        kw in text for kw in ["bulan ini", "akhir bulan", "tanggal", "minggu", "hari"]
    )
    if "honest" in criteria or "specific" in criteria:
        key = "honest" if "honest" in criteria else "specific"
        scores[key] = 25 if has_specific else 8
        if not has_specific:
            feedback_parts.append("🎯 Kasih angka & tanggal SPESIFIK (misal: 'Rp 300.000 tanggal 25'). Jangan vague.")

    # Polite check
    has_polite = any(kw in text for kw in [
        "pak", "bu", "mas", "mba", "terima kasih", "mohon", "maaf",
        "silakan", "tolong",
    ])
    if "polite" in criteria:
        scores["polite"] = 25 if has_polite else 8
        if not has_polite:
            feedback_parts.append("🙏 Tetap sopan. Pakai 'Pak/Bu', 'terima kasih', 'mohon' — DC lebih terbuka jika Anda sopan.")

    # No threat back
    no_threat_back = not any(kw in text for kw in [
        "saya akan bunuh", "saya lapor polisi", "saya sebar", "saya hajar",
    ])
    if "no_threat" in criteria:
        scores["no_threat"] = 25 if no_threat_back else 0
        if not no_threat_back:
            feedback_parts.append("⚠️ Jangan mengancam balik. Fokus pada solusi, bukan emosional.")

    # Acknowledge
    has_ack = any(kw in text for kw in [
        "keringanan", "diskon", "potong", "thank you for", "terima kasih untuk",
        "saya hargai", "saya appreciate",
    ])
    if "acknowledge" in criteria:
        scores["acknowledge"] = 25 if has_ack else 5
        if not has_ack:
            feedback_parts.append("🙏 Acknowledge tawaran keringanan DC ('Terima kasih keringanannya...') — ini menunjukkan kooperatif.")

    # Realistic check
    over_promise = any(kw in text for kw in [
        "saya bayar lunas besok", "akan lunas minggu ini", "pokoknya saya bayar semua",
    ])
    if "realistic" in criteria:
        scores["realistic"] = 0 if over_promise else 25
        if over_promise:
            feedback_parts.append("⚠️ Jangan over-promise. Lebih baik realistis agar bisa ditepati.")

    total = sum(scores.values())
    max_possible = len(criteria) * 25
    if max_possible == 0:
        max_possible = 100
    final_score = round((total / max_possible) * 100)

    if final_score >= 80:
        verdict = "Sangat Baik"
        verdict_color = "#84cc16"
        verdict_msg = "Anda menunjukkan respons yang matang & strategis. DC profesional akan merespons positif."
    elif final_score >= 60:
        verdict = "Baik"
        verdict_color = "#84cc16"
        verdict_msg = "Respons Anda cukup baik. Beberapa area masih bisa diperbaiki."
    elif final_score >= 40:
        verdict = "Cukup"
        verdict_color = "#f59e0b"
        verdict_msg = "Anda bisa lebih baik lagi. Lihat tips di bawah untuk respons ideal."
    else:
        verdict = "Perlu Perbaikan"
        verdict_color = "#ef4444"
        verdict_msg = "Respons ini bisa jadi kontraproduktif. Pelajari skenario & coba lagi."

    return {
        "valid": True,
        "score": final_score,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_msg": verdict_msg,
        "criteria_scores": scores,
        "feedback": feedback_parts,
        "matched": "matched" if final_score >= 60 else "not-matched",
    }


def evaluate_dc_multi_turn(scenario: dict, turn_choices: list[dict]) -> dict:
    """Evaluate multi-turn DC conversation based on user's option choices.

    Args:
        scenario: dict with 'id', 'turns' (list of turns), 'evaluation_criteria'
        turn_choices: list of {turn_index, option_index} (one per turn)

    Returns:
        dict with:
            - score: 0-100 (average of option scores, weighted by criteria coverage)
            - verdict: 'Sangat Baik' | 'Baik' | 'Cukup' | 'Perlu Perbaikan'
            - verdict_color, verdict_msg
            - criteria_scores: {criterion: 0-25} aggregated
            - per_turn: list of {turn_idx, option_label, score, feedback}
            - feedback: list of general tips
            - matched: 'matched' | 'not-matched'
            - total_turns, completed_turns
    """
    turns = scenario.get("turns", [])
    criteria_keys = list(scenario.get("evaluation_criteria", {}).keys())
    if not turns or not criteria_keys:
        # Fallback to legacy
        return {"valid": False, "error": "Scenario tidak punya turns"}

    per_turn = []
    total_score = 0
    criteria_totals: dict[str, int] = {k: 0 for k in criteria_keys}
    all_feedback: list[str] = []
    completed = 0

    for choice in turn_choices:
        ti = choice.get("turn_index", -1)
        oi = choice.get("option_index", -1)
        if ti < 0 or ti >= len(turns):
            continue
        turn = turns[ti]
        opts = turn.get("options", [])
        if oi < 0 or oi >= len(opts):
            continue
        opt = opts[oi]
        score = opt.get("score", 0)
        feedback = opt.get("feedback", "")
        total_score += score
        completed += 1
        # Aggregate criteria
        for k, v in (opt.get("criteria") or {}).items():
            if k in criteria_totals:
                criteria_totals[k] += v
        per_turn.append({
            "turn_idx": ti,
            "dc_message": turn.get("dc_message", ""),
            "option_label": opt.get("label", ""),
            "score": score,
            "feedback": feedback,
        })
        if feedback:
            all_feedback.append(f"Turn {ti + 1}: {feedback}")

    if completed == 0:
        return {"valid": False, "error": "Tidak ada turn yang valid"}

    # Average score (0-100)
    final_score = round(total_score / completed)

    # Normalize criteria (max = 25 per criterion, assuming up to N turns)
    # Use total max per criterion = completed * 25
    for k in criteria_totals:
        criteria_totals[k] = round(criteria_totals[k] / completed)

    # Verdict
    if final_score >= 80:
        verdict, color, msg = "Sangat Baik", "#84cc16", "Anda menunjukkan respons yang matang & strategis. DC profesional akan merespons positif."
    elif final_score >= 60:
        verdict, color, msg = "Baik", "#84cc16", "Respons Anda cukup baik. Beberapa area masih bisa diperbaiki."
    elif final_score >= 40:
        verdict, color, msg = "Cukup", "#f59e0b", "Anda bisa lebih baik lagi. Lihat tips di bawah untuk respons ideal."
    else:
        verdict, color, msg = "Perlu Perbaikan", "#ef4444", "Respons ini bisa jadi kontraproduktif. Pelajari skenario & coba lagi."

    # General feedback (highlight weakest criteria)
    sorted_criteria = sorted(criteria_totals.items(), key=lambda x: x[1])
    weak = sorted_criteria[:2] if len(sorted_criteria) >= 2 else sorted_criteria
    general_feedback = []
    for k, v in weak:
        if v < 15:
            criterion_label = scenario["evaluation_criteria"].get(k, k)
            general_feedback.append(f"⚠️ {criterion_label}: skor rendah. Latih lagi aspek ini.")

    return {
        "valid": True,
        "score": final_score,
        "verdict": verdict,
        "verdict_color": color,
        "verdict_msg": msg,
        "criteria_scores": criteria_totals,
        "per_turn": per_turn,
        "feedback": all_feedback + general_feedback,
        "matched": "matched" if final_score >= 60 else "not-matched",
        "total_turns": len(turns),
        "completed_turns": completed,
    }
    text = user_response.lower().strip()
    if not text or len(text) < 10:
        return {
            "score": 0,
            "feedback": "Response terlalu pendek. Coba lebih detail & profesional.",
            "criteria_scores": {
                "length": 0,
            },
            "matched_keywords": [],
        }

    criteria = scenario.get("evaluation_criteria", {})
    scores: dict[str, int] = {}
    feedback_parts: list[str] = []

    # Check calm/cool (no all-caps screaming, no profanity)
    is_calm = (
        not any(w in text.upper() * 3 for w in text.split() if len(w) > 3)
        and not any(p in text for p in ["babi", "anjir banget", "bodoh", "tolol"])
    )
    if "calm" in criteria:
        scores["calm"] = 25 if is_calm else 10
        if not is_calm:
            feedback_parts.append("⚠️ Tetap tenang — DC sering provoke emosi. Jangan teriak balik.")

    # Check legal/verify (mention of identity, UU, OJK, Kominfo, etc.)
    has_legal = any(kw in text for kw in [
        "identitas", "kartu pengenal", "ktp", "kartu nama",
        "uu pdp", "uu ite", "ojk", "kominfo", "polisi", "polisi cyber",
        "bukti", "tagihan resmi", "surat",
    ])
    if "verify" in criteria or "legal" in criteria:
        key = "verify" if "verify" in criteria else "legal"
        scores[key] = 25 if has_legal else 5
        if not has_legal:
            feedback_parts.append("📋 Selalu minta bukti identitas & surat tagihan resmi. DC ilegal sering tanpa dokumen.")

    # Check negotiation (mention of restrukturisasi, cicilan, keringanan, jadwal)
    has_negotiate = any(kw in text for kw in [
        "restrukturisasi", "cicil", "cicilan", "keringanan", "jadwal",
        "bayar sebagian", "parsial", "分期", "bertahap", "30%", "50%",
        "restruk", "diskon",
    ])
    if "negotiate" in criteria or "cooperative" in criteria:
        key = "negotiate" if "negotiate" in criteria else "cooperative"
        scores[key] = 25 if has_negotiate else 8
        if not has_negotiate:
            feedback_parts.append("🤝 Tawarkan solusi konkret (restrukturisasi, cicilan, keringanan), bukan sekadar tolak atau iya.")

    # Check document (mention of screenshot, dokumentasi, save, rekam)
    has_doc = any(kw in text for kw in [
        "screenshot", "dokumentasi", "rekam", "bukti chat", "simpan",
        "record", "saya rekam",
    ])
    if "document" in criteria:
        scores["document"] = 25 if has_doc else 8
        if not has_doc:
            feedback_parts.append("📸 Dokumentasikan ancaman (screenshot) untuk bukti pelaporan.")

    # Check no payment under threat
    has_no_pay = not any(kw in text for kw in [
        "ok saya transfer", "ok saya bayar", "siap transfer", "transfer sekarang",
        "bayar sekarang juga",
    ])
    if "no_payment" in criteria:
        scores["no_payment"] = 25 if has_no_pay else 0
        if not has_no_pay:
            feedback_parts.append("🚨 Jangan bayar di bawah ancaman! Itu ilegal. Anda punya hak untuk negosiasi fair.")

    # Check honest / specific (mention of angka/income)
    has_specific = bool(re.search(r"\d+\s*(juta|ribu|rb|jt|k|%)", text)) or any(
        kw in text for kw in ["bulan ini", "akhir bulan", "tanggal", "minggu", "hari"]
    )
    if "honest" in criteria or "specific" in criteria:
        key = "honest" if "honest" in criteria else "specific"
        scores[key] = 25 if has_specific else 8
        if not has_specific:
            feedback_parts.append("🎯 Kasih angka & tanggal SPESIFIK (misal: 'Rp 300.000 tanggal 25'). Jangan vague.")

    # Polite check (mention of terima kasih, pak/bu, mohon)
    has_polite = any(kw in text for kw in [
        "pak", "bu", "mas", "mba", "terima kasih", "mohon", "maaf",
        "silakan", "tolong",
    ])
    if "polite" in criteria:
        scores["polite"] = 25 if has_polite else 8
        if not has_polite:
            feedback_parts.append("🙏 Tetap sopan. Pakai 'Pak/Bu', 'terima kasih', 'mohon' — DC lebih terbuka jika Anda sopan.")

    # No threat back
    no_threat_back = not any(kw in text for kw in [
        "saya akan bunuh", "saya lapor polisi", "saya sebar", "saya hajar",
    ])
    if "no_threat" in criteria:
        scores["no_threat"] = 25 if no_threat_back else 0
        if not no_threat_back:
            feedback_parts.append("⚠️ Jangan mengancam balik. Fokus pada solusi, bukan emosional.")

    # Check acknowledge (mentions keringanan / diskon / potong)
    has_ack = any(kw in text for kw in [
        "keringanan", "diskon", "potong", "thank you for", "terima kasih untuk",
        "saya hargai", "saya appreciate",
    ])
    if "acknowledge" in criteria:
        scores["acknowledge"] = 25 if has_ack else 5
        if not has_ack:
            feedback_parts.append("🙏 Acknowledge tawaran keringanan DC ('Terima kasih keringanannya...') — ini menunjukkan kooperatif.")

    # realistic check (no over-promise)
    over_promise = any(kw in text for kw in [
        "saya bayar lunas besok", "akan lunas minggu ini", "pokoknya saya bayar semua",
    ])
    if "realistic" in criteria:
        scores["realistic"] = 0 if over_promise else 25
        if over_promise:
            feedback_parts.append("⚠️ Jangan over-promise. Lebih baik realistis agar bisa ditepati.")

    total = sum(scores.values())
    max_possible = len(criteria) * 25
    if max_possible == 0:
        max_possible = 100

    final_score = round((total / max_possible) * 100)

    if final_score >= 80:
        verdict = "Sangat Baik"
        verdict_color = "#b8ff3c"
        verdict_msg = "Anda menunjukkan respons yang matang & strategis. DC profesional akan merespons positif."
    elif final_score >= 60:
        verdict = "Baik"
        verdict_color = "#84cc16"
        verdict_msg = "Respons Anda cukup baik. Beberapa area masih bisa diperbaiki."
    elif final_score >= 40:
        verdict = "Cukup"
        verdict_color = "#f59e0b"
        verdict_msg = "Anda bisa lebih baik lagi. Lihat tips di bawah untuk respons ideal."
    else:
        verdict = "Perlu Perbaikan"
        verdict_color = "#ef4444"
        verdict_msg = "Respons ini bisa jadi kontraproduktif. Pelajari skenario & coba lagi."

    return {
        "score": final_score,
        "verdict": verdict,
        "verdict_color": verdict_color,
        "verdict_msg": verdict_msg,
        "criteria_scores": scores,
        "feedback": feedback_parts,
        "matched": "matched" if final_score >= 60 else "not-matched",
    }


# =================================================================
# TOOLS: Emergency Runway Calculator
# =================================================================
def calculate_emergency_runway(
    cash_on_hand: float = 0,
    monthly_expenses: float = 0,
    monthly_income: float = 0,
    monthly_debt_payment: float = 0,
) -> dict:
    """Hitung berapa bulan kamu bisa bertahan kalau income berhenti hari ini.

    Args:
        cash_on_hand: tabungan + saldo (Rp)
        monthly_expenses: biaya hidup/bulan (Rp)
        monthly_income: income bulanan (Rp)
        monthly_debt_payment: cicilan hutang/bulan (Rp)

    Returns:
        dict dengan runway_months, status, recommendations
    """
    if monthly_expenses <= 0:
        return {
            "valid": False,
            "error": "Biaya hidup bulanan harus > 0",
        }

    total_burn = monthly_expenses + monthly_debt_payment
    runway_months = round(cash_on_hand / total_burn, 1) if total_burn > 0 else 0
    income_coverage = round((monthly_income / total_burn) * 100, 1) if total_burn > 0 else 0

    # Status
    if runway_months >= 6:
        status = "AMAN"
        status_color = "#84cc16"
        status_msg = "Runway ≥ 6 bulan. Ideal! Pertahankan."
    elif runway_months >= 3:
        status = "WASPADA"
        status_color = "#f59e0b"
        status_msg = "Runway 3-6 bulan. Mulai tambah dana darurat."
    elif runway_months >= 1:
        status = "BAHAYA"
        status_color = "#ef4444"
        status_msg = "Runway < 3 bulan. Prioritaskan tambah tabungan."
    else:
        status = "KRITIS"
        status_color = "#7f1d1d"
        status_msg = "Runway < 1 bulan. SEGERA ambil tindakan."

    # Recommendations
    recs: list[dict] = []
    if runway_months < 6:
        target_cash = total_burn * 6
        recs.append({
            "priority": "tinggi" if runway_months < 3 else "sedang",
            "title": f"Target dana darurat: Rp {target_cash:,.0f}",
            "action": f"Sisihkan minimal 10% income/bulan ke rekening terpisah (terpisah dari rekening utama).",
        })
    if income_coverage < 100:
        deficit = total_burn - monthly_income
        recs.append({
            "priority": "tinggi" if deficit > 0 else "sedang",
            "title": f"Defisit: Rp {deficit:,.0f}/bulan",
            "action": "Tambah income (side hustle) atau kurangi pengeluaran non-esensial.",
        })
    if monthly_debt_payment > monthly_income * 0.3:
        recs.append({
            "priority": "tinggi",
            "title": "Cicilan terlalu besar (>30% income)",
            "action": "Restrukturisasi utang, gabungkan (konsolidasi), atau negosiasi bunga lebih rendah.",
        })
    if monthly_expenses > 0 and cash_on_hand > 0:
        months_to_3x = max(0, round((3 * total_burn - cash_on_hand) / max(monthly_income * 0.1, 1), 1))
        if months_to_3x > 0 and months_to_3x < 36:
            recs.append({
                "priority": "sedang",
                "title": f"Capai 3x runway dalam {months_to_3x} bulan",
                "action": "Kurangi 1-2 pos pengeluaran non-esensial, alokasikan ke dana darurat.",
            })

    return {
        "valid": True,
        "runway_months": runway_months,
        "runway_label": f"{runway_months} bulan" if runway_months >= 1 else f"{int(runway_months * 30)} hari",
        "status": status,
        "status_color": status_color,
        "status_msg": status_msg,
        "total_burn": total_burn,
        "income_coverage": income_coverage,
        "recommendations": recs,
    }


# =================================================================
# TOOLS: 30-Day Personal Action Plan
# =================================================================
def generate_30_day_plan(
    cicilan_aktif: int = 0,
    checkout_impulse: int = 0,
    cicilan_0_persen: int = 0,
    reaksi_tagihan: int = 0,
    dc_pesan: int = 0,
    track_pengeluaran: int = 0,
) -> dict:
    """Generate 30-day personal action plan berdasarkan Galbay Score answers.

    Returns dict dengan:
    - score (0-100)
    - bucket (rendah/sedang/tinggi/kritis)
    - 30-day plan (week 1-4 actions)
    """
    # Same scoring as galbay_score route
    cicilan_score = max(0, 25 - cicilan_aktif * 5)
    impulse_score = min(25, checkout_impulse * 5)
    cicilan0_score = min(21, cicilan_0_persen * 7)
    tagihan_score = min(25, reaksi_tagihan * 8)
    dc_score = min(25, dc_pesan * 8)
    track_score = [0, 8, 16, 25][track_pengeluaran]
    raw = cicilan_score + impulse_score + cicilan0_score + tagihan_score + dc_score + track_score
    score = round((raw / 146) * 100)

    if score <= 30:
        bucket = "rendah"
        bucket_color = "#84cc16"
        bucket_msg = "Keuangan sehat. Pertahankan & naikkan level."
    elif score <= 55:
        bucket = "sedang"
        bucket_color = "#f59e0b"
        bucket_msg = "Ada risiko. Mulai kebiasaan sehat."
    elif score <= 75:
        bucket = "tinggi"
        bucket_color = "#ef4444"
        bucket_msg = "Risiko tinggi. Butuh perubahan perilaku."
    else:
        bucket = "kritis"
        bucket_color = "#7f1d1d"
        bucket_msg = "Sangat kritis. Butuh intervensi intensif."

    # Build 30-day plan (4 weeks)
    plan: list[dict] = []

    # Week 1: Audit & Awareness
    plan.append({
        "week": 1,
        "title": "Audit & Kesadaran",
        "emoji": "📋",
        "color": "#9b5de5",
        "actions": [
            "Catat SEMUA utang: nominal, bunga, tenor, jatuh tempo (gunakan spreadsheet/notes)",
            "Hitung total cash on-hand + income bulanan + expenses bulanan",
            "Download semua app pinjol/paylater, cek tagihan & tanggal jatuh tempo",
            "Cek skor kredit di SLIK OJK (gratis, 1× setahun)",
            "Identifikasi 3 'pemicu' belanja impulsif (misal: scroll TikTok malam, FOMO diskon)",
        ],
    })

    # Week 2: Stabilize (pay bills on time)
    if reaksi_tagihan >= 2 or dc_pesan >= 1:
        plan[0]["actions"].append("⚠️ PRIORITAS: Bayar tagihan yang akan jatuh tempo 7 hari ke depan")
    plan.append({
        "week": 2,
        "title": "Stabilkan Arus Kas",
        "emoji": "💰",
        "color": "#3b82f6",
        "actions": [
            "Aktifkan auto-debit untuk semua tagihan (cicilan, paylater, listrik, internet)",
            "Set reminder H-3 sebelum jatuh tempo (pakai Kalender/Notion)",
            "Mulai pisahkan rekening: 1 untuk bayar tagihan, 1 untuk kebutuhan sehari-hari",
            "Kurangi 1 pos pengeluaran non-esensial (kopi kekinian, langganan, dll)",
            "Mulai tracking pengeluaran harian (pakai app seperti Money Lover / Sheet)",
        ],
    })

    # Week 3: Negotiate & Restructure
    if cicilan_aktif >= 2 or dc_pesan >= 1:
        plan.append({
            "week": 3,
            "title": "Negosiasi & Restrukturisasi",
            "emoji": "🤝",
            "color": "#c026d3",
            "actions": [
                "Hubungi 1-2 creditor untuk negosiasi restrukturisasi (cicilan lebih panjang, bunga lebih rendah)",
                "Gunakan template chat di menu DC Survival Kit",
                "Jangan terima panggilan tanpa identitas & surat tagihan resmi",
                "Konsolidasi utang (gabungkan beberapa utang jadi 1 dengan bunga lebih rendah)",
                "Stop checkout impulse: terapkan 'tidur dulu 24 jam' sebelum bayar",
            ],
        })
    else:
        plan.append({
            "week": 3,
            "title": "Bangun Dana Darurat",
            "emoji": "🏦",
            "color": "#c026d3",
            "actions": [
                "Target: 3x pengeluaran bulanan sebagai dana darurat",
                "Otomatis transfer 10% income ke rekening terpisah tiap gaji",
                "Jangan sentuh dana darurat kecuali emergency (sakit, PHK, dll)",
                "Riset reksa dana pasar uang atau deposito untuk dana darurat (bunga > tabungan biasa)",
            ],
        })

    # Week 4: Build Habits
    plan.append({
        "week": 4,
        "title": "Bangun Kebiasaan Baru",
        "emoji": "🚀",
        "color": "#b8ff3c",
        "actions": [
            "Cek progress: total utang turun? Dana darurat naik? Tracking konsisten?",
            "Uninstall 1-2 app yang paling sering bikin impulse (TikTok, Shopee, Tokped)",
            "Coba 1 kegiatan gratis untuk ganti 'retail therapy' (jalan, baca, olahraga)",
            "Review & update plan 30 hari ke depan dengan target baru",
            "Share ke teman/keluarga: accountability partner untuk habit keuangan",
        ],
    })

    # Add bonus: 30-day milestones
    milestones = [
        {"day": 1, "icon": "🎯", "text": "Mulai! Catat semua utang hari ini."},
        {"day": 7, "icon": "📊", "text": "Review: 7 hari tracking pengeluaran. Apa pola terbesarmu?"},
        {"day": 14, "icon": "💸", "text": "Cek: ada tagihan yang sudah dibayar tepat waktu? Auto-debit aktif?"},
        {"day": 21, "icon": "🤝", "text": "Negosiasi: sudah hubungi 1 creditor untuk restrukturisasi?"},
        {"day": 30, "icon": "🏆", "text": "Selamat! Kamu sudah konsisten 30 hari. Hitung ulang Galbay Score."},
    ]

    return {
        "score": score,
        "bucket": bucket,
        "bucket_color": bucket_color,
        "bucket_msg": bucket_msg,
        "plan": plan,
        "milestones": milestones,
    }
