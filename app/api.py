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

import json
import os
from pathlib import Path
from datetime import datetime

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
        extra_payment: extra payment per bulan (untuk加速 lunas)

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
# 3. DC SURVIVAL KIT — Template chat untuk negosiasi debt collector
# =================================================================
DC_TEMPLATES = [
    {
        "id": "tidak_bisa_hari_ini",
        "title": "Tidak Bisa Bayar Hari Ini",
        "scenario": "DC menagih, kamu belum punya uang sama sekali",
        "tone": "sopan tapi tegas",
        "message": (
            "Selamat [pagi/siang/sore] Bapak/Ibu. Saya [nama] dari [pinjol]. "
            "Saya mengakui punya tanggungan cicilan. Saat ini saya belum bisa memenuhi pembayaran tepat waktu karena [alasan: kehilangan pekerjaan / biaya mendadak / dll]. "
            "Saya berkomitmen untuk melunasi seluruh tanggungan saya. Mohon waktu [X hari/minggu] untuk menyusun rencana pembayaran. "
            "Saya bisa dihubungi di [nomor HP] untuk konfirmasi. Terima kasih."
        ),
        "hak_kamu": [
            "DC TIDAK boleh mengancam kekerasan fisik",
            "DC TIDAK boleh menghubungi keluarga/teman kantor tanpa izin",
            "DC TIDAK boleh menghubungi di atas jam 20.00 atau sebelum jam 08.00",
            "DC TIDAK boleh mempublikasikan data pribadi",
        ],
        "landasan_hukum": "Permenkominfo No. 6/2016 tentang Penyiaran; UU ITE Pasal 26; UU PDP Pasal 5",
    },
    {
        "id": "restrukturisasi",
        "title": "Minta Restrukturisasi",
        "scenario": "Kamu tidak bisa bayar penuh, mau nego perpanjangan tenor",
        "tone": "negosiatif, kooperatif",
        "message": (
            "Selamat [pagi/siang] Bapak/Ibu. Saya [nama] dari [pinjol], No. Pinjaman [XXX]. "
            "Saat ini saya mengalami kesulitan keuangan dan tidak bisa membayar cicilan penuh. "
            "Saya ingin mengusulkan restrukturisasi: perpanjangan tenor dari [X bulan] menjadi [Y bulan], "
            "dengan cicilan Rp [nominal] per bulan. "
            "Saya bersedia membayar tepat waktu sesuai jadwal baru. Mohon dipertimbangkan. "
            "Terima kasih, Bapak/Ibu. Saya bisa dihubungi di [nomor HP]."
        ),
        "hak_kamu": [
            "Kamu BERHAK minta restrukturisasi (UU No. 4/2023 tentang P2SK)",
            "DC TIDAK boleh menolak tanpa alasan",
            "Dokumentasikan semua komunikasi",
        ],
        "landasan_hukum": "UU No. 4/2023 tentang Pengembangan dan Penguatan Sistem Keuangan (P2SK) Pasal 236",
    },
    {
        "id": "tolak_penagihan_agresif",
        "title": "Tolak Penagihan Agresif",
        "scenario": "DC meneror, mengancam, atau menyebar data ke keluarga",
        "tone": "tegas, formal",
        "message": (
            "Bapak/Ibu, Saya [nama] dari [pinjol]. "
            "Saya tidak bisa menerima tindakan penagihan berupa [ancaman / peneroran / penyebaran data ke keluarga]. "
            "Perbuatan ini melanggar UU ITE Pasal 27 ayat (4) tentang pengancaman dan/atau pencemaran nama baik. "
            "Saya minta dihentikan. Jika tidak, saya akan: "
            "(1) melapor ke OJK di 157, "
            "(2) melapor ke Polisi via aplikasi POLISI 110, "
            "(3) mengajukan gugatan perdata. "
            "Bukti komunikasi ini saya simpan. Terima kasih."
        ),
        "hak_kamu": [
            "Kamu BERHAK menolak ancaman, intimidasi, dan kekerasan",
            "Lapor ke OJK: 157 (hotline) atau ojk.go.id",
            "Lapor ke Polisi: 110 atau aplikasi POLISI 110",
            "Screenshot semua bukti untuk proses hukum",
        ],
        "landasan_hukum": "UU ITE Pasal 27, 29, 45; KUHP Pasal 369 (pemerasan); UU Perlindungan Konsumen",
    },
    {
        "id": "lapor_dc_ilegal",
        "title": "Laporkan DC Ilegal",
        "scenario": "DC dari pinjol ilegal (tidak terdaftar OJK), atau DC yang mengakses data pribadi tanpa izin",
        "tone": "lapor, formal",
        "message": (
            "Kepada Yth. OJK / Kominfo, "
            "Saya [nama], No. KTP [XXX], ingin melaporkan aplikasi pinjol ilegal bernama [nama app]. "
            "Aplikasi ini tidak terdaftar di OJK dan DC-nya melakukan: "
            "[akses kontak tanpa izin / ancaman kekerasan / pencemaran nama baik]. "
            "Bukti terlampir: screenshot chat DC, tangkapan layar transfer ke rekening DC, dll. "
            "Mohon untuk ditindaklanjuti. Terima kasih."
        ),
        "hak_kamu": [
            "Lapor OJK: 157 atau ojk.go.id (menu 'Pengaduan Konsumen')",
            "Lapor Kominfo: aduankonten.id (untuk app ilegal di Play Store)",
            "Lapor POLISI 110 jika ada ancaman/kekerasan",
        ],
        "landasan_hukum": "UU PDP Pasal 5, 13; UU ITE Pasal 27, 29; Permenkominfo 6/2016",
    },
    {
        "id": "konfirmasi_utang",
        "title": "Konfirmasi Saldo Utang",
        "scenario": "DC menagih jumlah yang tidak sesuai dengan yang kamu pinjam",
        "tone": "verifikasi, sopan",
        "message": (
            "Selamat [pagi/siang] Bapak/Ibu. Saya [nama] dari [pinjol]. "
            "Saya ingin konfirmasi saldo utang saya saat ini. "
            "Berdasarkan catatan saya: pokok pinjaman Rp [X], sudah dibayar Rp [Y], sisa Rp [Z]. "
            "Namun saya menerima tagihan Rp [nominal lain] dari Bapak/Ibu. "
            "Mohon diberikan rincian: sisa pokok, total bunga, denda (jika ada), dan tanggal jatuh tempo. "
            "Saya akan membayar setelah verifikasi. Terima kasih."
        ),
        "hak_kamu": [
            "BERHAK mendapat rincian utang (poin-poin biaya)",
            "DC TIDAK boleh menambahkan biaya tanpa pemberitahuan tertulis",
            "Hitung manual: sisa pokok × (1 + bunga% × tenor) — cocokkan dengan tagihan",
        ],
        "landasan_hukum": "UU Perlindungan Konsumen Pasal 7 (hak informasi); POJK tentang transparansi fintech",
    },
]


def get_dc_templates() -> dict:
    """Return semua DC templates."""
    return {
        "valid": True,
        "templates": DC_TEMPLATES,
        "general_rights": [
            "Kamu BERHAK minta identitas lengkap DC (nama, ID, perusahaan)",
            "DC TIDAK BOLEH menyebar data pribadi ke orang lain",
            "DC TIDAK BOLEH mengancam kekerasan fisik/verbal",
            "DC TIDAK BOLEH menghubungi di luar jam kerja (08.00-20.00)",
            "DC TIDAK BOLEH menagih utang yang tidak kamu kenal",
            "Seluruh komunikasi harus bisa kamu dokumentasikan",
        ],
        "emergency_contacts": [
            {"name": "Hotline OJK", "number": "157", "web": "ojk.go.id"},
            {"name": "Hotline Kominfo (app ilegal)", "number": "aduankonten.id"},
            {"name": "POLISI", "number": "110", "web": "POLISI 110 app"},
            {"name": "YLBHI (bantuan hukum gratis)", "number": "(021) 319 025 35"},
        ],
        "disclaimer": "Template ini bersifat panduan umum. Untuk kasus spesifik, konsultasi dengan pengacara atau LBH.",
    }


def get_dc_template(template_id: str) -> dict:
    """Return 1 DC template by id."""
    for t in DC_TEMPLATES:
        if t["id"] == template_id:
            return {"valid": True, "template": t}
    return {"valid": False, "error": f"Template '{template_id}' tidak ditemukan"}


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
            "MINGGU 7-8: Negosiasi ulang ke DC yang agresif (pakai template DC Kit)",
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
# 5. FAQ CHATBOT (Phase 1: rule-based, keyword matching)
# =================================================================
# Knowledge base untuk chatbot. Phase 2 nanti: RAG over 349K reviews
# dengan embedding-based semantic search.

FAQ_KB = [
    {
        "intent": "apa_itu_galbay",
        "keywords": ["apa itu galbay", "galbay itu apa", "definisi galbay", "arti galbay", "gagal bayar artinya"],
        "answer": (
            "**Galbay** = **Gagal Bayar**. Istilah Gen Z untuk kondisi ketika kamu tidak bisa membayar cicilan tepat waktu. "
            "Bisa bertahap: telat 1 hari → 7 hari → 30 hari → masuk daftar hitam. "
            "Tapi bukan akhir dunia — bisa di-recovery dengan rencana yang tepat."
        ),
        "suggestions": ["Skor Risiko", "Recovery Roadmap", "DC Kit"],
        "related_actions": [
            {"label": "Cek Skor Risiko Kamu", "href": "/dashboard/produk#skor-form"},
            {"label": "Lihat Recovery Roadmap", "href": "/dashboard/produk#recovery-roadmap"},
        ],
    },
    {
        "intent": "apa_itu_skor_risiko",
        "keywords": ["skor risiko", "skor galbay", "skor itu apa", "cara hitung skor", "score risk", "skor 75", "skor saya"],
        "answer": (
            "**Skor Risiko Galbay** adalah angka 0-100 yang mengukur kemungkinan kamu gagal bayar. "
            "Dihitung dari 6 faktor: jenis app yang dipakai, total utang, frekuensi self-reward, "
            "keterlambatan, pernah ditagih DC, dan feeling kamu. Skor 0-30 = Aman, 31-60 = Waspada, 61+ = Bahaya. "
            "Saat ini masih **rule-based** — nanti di-swap ke model ML setelah tim modeling selesai."
        ),
        "suggestions": ["Cek Skor Kamu", "Simulasi Cicilan"],
        "related_actions": [
            {"label": "Hitung Skor Kamu", "href": "/dashboard/produk#skor-form"},
        ],
    },
    {
        "intent": "pinjol_ilegal",
        "keywords": ["pinjol ilegal", "pinjol haram", "pinjol bodong", "pinjol tidak terdaftar", "aplikasi pinjol abal", "cek pinjol", "apakah pinjol aman"],
        "answer": (
            "**Pinjol ilegal** = aplikasi pinjam online yang **tidak terdaftar di OJK** dan sering kali melakukan: "
            "(1) akses kontak/galeri tanpa izin, (2) bunga di atas 30%/bulan, (3) DC agresif yang sebar data ke keluarga. "
            "Cara cek: gunakan **Pinjol Checker** di atas, atau langsung ke website OJK di ojk.go.id → Fintech → Daftar Fintech Terdaftar."
        ),
        "suggestions": ["Cek Pinjol", "Lapor Pinjol Ilegal"],
        "related_actions": [
            {"label": "Cek Status Pinjol", "href": "/dashboard/produk#pinjol-checker"},
        ],
    },
    {
        "intent": "snowball_vs_avalanche",
        "keywords": ["snowball", "avalanche", "strategi bayar utang", "mana yang lebih baik", "bunga tertinggi", "utang terkecil"],
        "answer": (
            "**Snowball**: bayar utang **terkecil** dulu (biar cepat lunas 1-2 utang = motivasi psikologis). "
            "**Avalanche**: bayar utang **bunga tertinggi** dulu (hemat total bunga). "
            "Rekomendasi: Avalanche kalau kamu disiplin, Snowball kalau butuh quick win motivasi. "
            "Tools kami bisa hitung keduanya — coba di **Debt Planner**."
        ),
        "suggestions": ["Debt Planner", "Bandingkan"],
        "related_actions": [
            {"label": "Hitung Strategi Bayar", "href": "/dashboard/produk#debt-planner"},
        ],
    },
    {
        "intent": "bunga_tinggi_normal",
        "keywords": ["bunga normal", "bunga wajar", "berapa bunga pinjol", "bunga tinggi", "bunga efektif tahunan", "bunga 10", "bunga kta bank"],
        "answer": (
            "Benchmark bunga di Indonesia: "
            "**KTA bank** 12-18%/tahun = wajar. "
            "**Paylater legal** 24-36%/tahun = batas atas. "
            "**Pinjol ilegal** 200-400%+/tahun = predator. "
            "Gunakan **Simulasi Cicilan** untuk hitung bunga efektif tahunan sebelum deal."
        ),
        "suggestions": ["Simulasi Cicilan", "Cek Pinjol"],
        "related_actions": [
            {"label": "Hitung Bunga", "href": "/dashboard/produk#simulasi"},
        ],
    },
    {
        "intent": "lama_lunas",
        "keywords": ["berapa lama lunas", "lunas berapa bulan", "kapan utang kelar", "timeline lunas", "berapa bulan"],
        "answer": (
            "Tergantung total utang + cicilan bulanan. Aturan umum: kalau cicilan bulan = 10% dari total utang → lunas dalam ~12 bulan. "
            "Kalau cuma bayar minimum 5%/bulan → bisa 24-36 bulan. "
            "Gunakan **Debt Planner** untuk hitung persisnya, atau **Recovery Roadmap** untuk rencana 90 hari."
        ),
        "suggestions": ["Debt Planner", "Recovery Roadmap"],
        "related_actions": [
            {"label": "Hitung Timeline", "href": "/dashboard/produk#debt-planner"},
        ],
    },
    {
        "intent": "dc_agresif",
        "keywords": ["dc agresif", "dc ngotot", "dc teroris", "dc sebarkan data", "dc ancam", "penagihan kasar", "debt collector", "dc agresif", "agresif", "ngotot", "ancaman", "sebar data", "intimidasi"],
        "answer": (
            "**Hak kamu saat menghadapi DC agresif**: "
            "(1) minta identitas lengkap DC, (2) DC TIDAK BOLEH ancam/sebar data, "
            "(3) hanya boleh kontak 08.00-20.00, (4) kamu boleh dokumentasi. "
            "**Lapor**: OJK 157, Polisi 110. "
            "Gunakan **DC Kit** untuk 5 template chat negosiasi siap pakai."
        ),
        "suggestions": ["DC Kit", "Lapor DC"],
        "related_actions": [
            {"label": "Lihat DC Kit", "href": "/dashboard/produk#dc-kit"},
        ],
    },
    {
        "intent": "lapor_dc",
        "keywords": ["lapor dc", "lapor debt collector", "lapor pinjol ilegal", "aduan", "kominfo", "ojk 157"],
        "answer": (
            "Tiga jalur pelaporan: "
            "**OJK** 157 atau ojk.go.id (pengaduan fintech ilegal/penagihan tak wajar). "
            "**Kominfo** aduankonten.id (app ilegal di Play Store). "
            "**Polisi** 110 (jika ada ancaman/kekerasan). "
            "Siapkan: screenshot chat DC, bukti transfer, nama app + tanggal."
        ),
        "suggestions": ["DC Kit", "Cek Pinjol"],
        "related_actions": [
            {"label": "Template Lapor", "href": "/dashboard/produk#dc-kit"},
        ],
    },
    {
        "intent": "template_chat",
        "keywords": ["template chat", "contoh chat", "chat dc", "pesan untuk dc", "script negosiasi", "whatsapp template"],
        "answer": (
            "Ada 5 template siap pakai: "
            "(1) Tidak Bisa Bayar Hari Ini, (2) Minta Restrukturisasi, (3) Tolak Penagihan Agresif, "
            "(4) Laporkan DC Ilegal, (5) Konfirmasi Saldo Utang. "
            "Tinggal copy, edit nama/nominal, kirim via WhatsApp. Lihat di **DC Kit**."
        ),
        "suggestions": ["Buka DC Kit"],
        "related_actions": [
            {"label": "Lihat Template", "href": "/dashboard/produk#dc-kit"},
        ],
    },
    {
        "intent": "cara_recovery",
        "keywords": ["cara recovery", "cara keluar galbay", "gimana kalau sudah galbay", "sudah telat", "sudah gagal bayar", "jalan keluar"],
        "answer": (
            "Langkah recovery: "
            "(1) **Stop pinjam baru** — hapus app pinjol dari HP. "
            "(2) **Audit semua utang** — catat di spreadsheet. "
            "(3) **Setel auto-debit** minimum payment 1 hari sebelum jatuh tempo. "
            "(4) **Pilih strategi** — Snowball (motivasi) atau Avalanche (hemat). "
            "(5) **Naikkan income** — kerja sampingan, jual aset tak terpakai. "
            "Gunakan **Recovery Roadmap** untuk rencana 90 hari otomatis."
        ),
        "suggestions": ["Recovery Roadmap", "Debt Planner"],
        "related_actions": [
            {"label": "Generate Roadmap", "href": "/dashboard/produk#recovery-roadmap"},
        ],
    },
    {
        "intent": "telat_30_hari",
        "keywords": ["telat 30", "telat sebulan", "nunggak sebulan", "lewat 30 hari", "kritis", "sudah di blacklist"],
        "answer": (
            "Telat 30+ hari = **kritis**. Langkah darurat: "
            "(1) Cek **SLIK di bank** (gratis, butuh e-KTP) untuk tahu status kredit. "
            "(2) **Negosiasi restrukturisasi** ke pinjol (mulai dari bunga tertinggi). "
            "(3) **Hapus app pinjol** untukurangi godaan. "
            "(4) **Cari konselor** (OJK 157 atau YLBHI). "
            "Gunakan **Recovery Roadmap** dan pilih kondisi 'telat >30 hari' untuk dapat roadmap krisis."
        ),
        "suggestions": ["Recovery Roadmap", "DC Kit"],
        "related_actions": [
            {"label": "Generate Roadmap Kritis", "href": "/dashboard/produk#recovery-roadmap"},
        ],
    },
    {
        "intent": "negosiasi_cicilan",
        "keywords": ["negosiasi cicilan", "minta keringanan", "restrukturisasi", "bisa nego", "cicilan dipanjang"],
        "answer": (
            "Bisa! Berdasarkan **UU No. 4/2023 (P2SK) Pasal 236**, kamu berhak minta restrukturisasi. "
            "Template: *'Saya ingin mengusulkan perpanjangan tenor dari X menjadi Y bulan, dengan cicilan Rp Z/bulan. "
            "Saya bersedia bayar tepat waktu sesuai jadwal baru.'* "
            "Lihat **DC Kit** untuk template lengkap. Biasanya disetujui kalau kamu punya itikad baik."
        ),
        "suggestions": ["DC Kit Template", "Recovery Roadmap"],
        "related_actions": [
            {"label": "Template Negosiasi", "href": "/dashboard/produk#dc-kit"},
        ],
    },
    {
        "intent": "aplikasi_aman",
        "keywords": ["aplikasi ini aman", "data saya disimpan", "privasi", "data tidak aman", "apakah scam", "trusted"],
        "answer": (
            "**Ya, aman**. Data kamu **tidak disimpan** — semua skor & simulasi dihitung lokal/server, "
            "tidak ada tracking, tidak butuh login. "
            "Source data: 349.200 ulasan publik Google Play Store (bukan data pribadi). "
            "Disclaimer: ini **demo prototype** dengan rule-based scoring — model ML menyusul."
        ),
        "suggestions": ["Tentang Kami", "Privacy"],
        "related_actions": [],
    },
    {
        "intent": "premium_dapat_apa",
        "keywords": ["premium dapat apa", "fitur premium", "premium ada apa", "mau premium", "premium worth it"],
        "answer": (
            "**Premium** (Rp 49K/bulan) dapat: "
            "(1) **AI Coach 24/7** (chat untuk tanya & recovery guidance), "
            "(2) **Nudge pre-checkout** real-time (peringatkan sebelum checkout impulsif), "
            "(3) **Laporan bulanan** personal, (4) **Save unlimited** debt plans, "
            "(5) **Priority DC template updates**. "
            "Klik **Coba Premium** di Pricing section — ada diskon 50% untuk 100 user pertama."
        ),
        "suggestions": ["Lihat Pricing", "Coba Premium"],
        "related_actions": [
            {"label": "Lihat Pricing", "href": "/dashboard/produk#pricing"},
        ],
    },
    {
        "intent": "konseling_berapa",
        "keywords": ["konseling berapa", "harga konseling", "konsultasi psikolog", "sesi berapa", "konseling mahal"],
        "answer": (
            "**Konseling** Rp 150K/sesi (60 menit) — 1-on-1 dengan psikolog spesialis financial stress. "
            "Confidential & aman. Termasuk akses penuh ke semua fitur Premium. "
            "Klik **Booking Sesi** di Pricing section untuk masuk waitlist."
        ),
        "suggestions": ["Lihat Pricing", "Booking Sesi"],
        "related_actions": [
            {"label": "Lihat Pricing", "href": "/dashboard/produk#pricing"},
        ],
    },
    {
        "intent": "diskon_premium",
        "keywords": ["diskon", "promo", "diskon 50", "berapa diskon", "potongan harga"],
        "answer": (
            "**Hanya 100 user pertama** dapat diskon 50% Premium (jadi Rp 24.5K/bulan). "
            "Setelah lewat 100 user, kembali ke Rp 49K/bulan. "
            "Klik **Coba Premium** sekarang untuk klaim."
        ),
        "suggestions": ["Coba Premium"],
        "related_actions": [
            {"label": "Coba Premium", "href": "/dashboard/produk#pricing"},
        ],
    },
    {
        "intent": "cara_pakai_website",
        "keywords": ["cara pakai", "gimana pakenya", "mulai dari mana", "langkah pertama", "tutorial"],
        "answer": (
            "Mulai dari 4 fitur utama: "
            "(1) **Cek Pinjol** — ketik nama app, dapat status OJK. "
            "(2) **Debt Planner** — input utang, bandingkan strategi. "
            "(3) **DC Kit** — copy template chat. "
            "(4) **Recovery Roadmap** — masukkan kondisi, dapat roadmap 90 hari. "
            "Atau coba **Skor Risiko** untuk tahu posisi kamu."
        ),
        "suggestions": ["Cek Pinjol", "Skor Risiko"],
        "related_actions": [
            {"label": "Mulai", "href": "/dashboard/produk"},
        ],
    },
    {
        "intent": "data_sumber",
        "keywords": ["data dari mana", "sumber data", "349 ribu", "ulasan", "google play", "dataset"],
        "answer": (
            "Data: **349.200 ulasan publik** dari Google Play Store, di-scrape dari 44 aplikasi fintech Indonesia. "
            "Dilakukan Q1-Q2 2025. Bukan data pribadi — semua review yang dipakai sudah publik. "
            "Lihat detail di **Dashboard → Analisis**."
        ),
        "suggestions": ["Lihat Dashboard"],
        "related_actions": [
            {"label": "Lihat Analisis", "href": "/dashboard/analisis"},
        ],
    },
    {
        "intent": "emergency_dc",
        "keywords": ["darurat dc", "dc sekarang", "dc datang", "dc telepon", "dc whatsapp", "bantuan sekarang"],
        "answer": (
            "**Darurat DC?** Tetap tenang. Tindakan cepat: "
            "(1) **Jangan bayar apa-apa** dulu, jangan transfer ke nomor aneh. "
            "(2) **Screenshot semua chat** DC untuk bukti. "
            "(3) **Minta identitas DC** (nama, perusahaan, ID). "
            "(4) **Lapor OJK 157** atau **Polisi 110** jika mengancam. "
            "Lihat **DC Kit** untuk template chat & kontak darurat."
        ),
        "suggestions": ["DC Kit", "Kontak Darurat"],
        "related_actions": [
            {"label": "DC Kit", "href": "/dashboard/produk#dc-kit"},
        ],
    },
    {
        "intent": "konsultan_keuangan",
        "keywords": ["konsultan", "konselor keuangan", "financial advisor", "tanya ahli", "konsultasi gratis"],
        "answer": (
            "Konsultasi gratis: "
            "**OJK** 157 (informasi & pengaduan). "
            "**YLBHI** (021) 319 025 35 (bantuan hukum finansial). "
            "**Peer support** di komunitas seperti @duithape (Twitter/X). "
            "Atau booking **Konseling** di app kami (Rp 150K/sesi, 60 menit, 1-on-1 psikolog)."
        ),
        "suggestions": ["Booking Konseling"],
        "related_actions": [
            {"label": "Lihat Konseling", "href": "/dashboard/produk#pricing"},
        ],
    },
    {
        "intent": "self_reward_aman",
        "keywords": ["self reward", "belanja self reward", "boleh belanja", "shopping therapy aman", "kapan boleh belanja"],
        "answer": (
            "Self-reward boleh, asal: "
            "(1) **Maks 10% income bulanan** untuk non-esensial. "
            "(2) **Tunda 24 jam** sebelum checkout (cek apakah masih mau besok). "
            "(3) **Bayar cash, bukan paylater** — supaya tidak numpuk utang. "
            "(4) **Pakai Simulasi Cicilan** dulu kalau mau pakai paylater — lihat total bayar."
        ),
        "suggestions": ["Simulasi Cicilan", "Skor Risiko"],
        "related_actions": [
            {"label": "Hitung Simulasi", "href": "/dashboard/produk#simulasi"},
        ],
    },
    {
        "intent": "pinjol_atau_paylater",
        "keywords": ["bedanya pinjol paylater", "mana yang lebih aman", "pinjol atau paylater"],
        "answer": (
            "**Paylater** = cicilan 0% (biasanya 1-3 bulan) dari platform e-commerce. "
            "**Pinjol** = uang tunai yang dipinjam, bunga 8-30%/bulan. "
            "**Paylater lebih aman** karena limited ke merchant. Tapi kalau telat bayar, dendanya besar. "
            "Keduanya tetap harus hati-hati — cek legalitas di **Pinjol Checker**."
        ),
        "suggestions": ["Cek Pinjol", "Simulasi Cicilan"],
        "related_actions": [
            {"label": "Cek Pinjol", "href": "/dashboard/produk#pinjol-checker"},
        ],
    },
    {
        "intent": "berapa_utang_normal",
        "keywords": ["berapa utang normal", "utang berapa wajar", "batas utang", "utang ideal"],
        "answer": (
            "**Rule of thumb**: total utang ideal **<30% income tahunan**. "
            "Misal gaji Rp 5 juta/bulan (Rp 60 juta/tahun) → total utang idealnya <Rp 18 juta. "
            "Lewat dari 3x income = kritis. Cek kondisi kamu di **Recovery Roadmap**."
        ),
        "suggestions": ["Recovery Roadmap", "Skor Risiko"],
        "related_actions": [
            {"label": "Cek Roadmap", "href": "/dashboard/produk#recovery-roadmap"},
        ],
    },
    {
        "intent": "ai_atau_rule_based",
        "keywords": ["pakai ai", "pakai ml", "model ai", "machine learning", "akurasi"],
        "answer": (
            "Saat ini scoring masih **rule-based** (berdasarkan bobot dari analisis 349K ulasan). "
            "Tim modeling sedang develop **model ML asli** yang akan swap in di Phase 2. "
            "Rule-based sudah cukup akurat untuk demo, hasil konsisten dan deterministic."
        ),
        "suggestions": ["Tentang Model", "Skor Risiko"],
        "related_actions": [
            {"label": "Cek Skor", "href": "/dashboard/produk#skor-form"},
        ],
    },
    {
        "intent": "default_fallback",
        "keywords": [],
        "answer": (
            "Maaf, saya belum paham pertanyaan itu. "
            "Saya bisa bantu topik: **skor risiko**, **pinjol ilegal**, **snowball vs avalanche**, "
            "**bunga wajar**, **DC agresif**, **cara recovery**, **telat 30 hari**, **negosiasi cicilan**, "
            "**premium**, **konseling**, **data sumber**, atau **darurat DC**. "
            "Atau klik salah satu modul di halaman ini."
        ),
        "suggestions": ["Skor Risiko", "Cek Pinjol", "DC Kit", "Recovery Roadmap"],
        "related_actions": [
            {"label": "Lihat Semua Fitur", "href": "/dashboard/produk"},
        ],
    },
]


def _tokenize(text: str) -> list:
    """Lowercase + remove punctuation + tokenize."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if t]


def _match_faq_intent(message: str) -> tuple:
    """Match user message to FAQ intent via keyword scoring.

    Returns: (best_intent_entry, confidence_score)
    """
    if not message or not message.strip():
        return None, 0.0

    msg_tokens = _tokenize(message)
    if not msg_tokens:
        return None, 0.0

    best_intent = None
    best_score = 0.0

    for entry in FAQ_KB:
        if entry["intent"] == "default_fallback":
            continue
        keywords = entry.get("keywords", [])
        if not keywords:
            continue

        score = 0.0
        matched = []
        for kw in keywords:
            kw_tokens = _tokenize(kw)
            if not kw_tokens:
                continue
            # Full phrase match (bonus)
            if kw.lower() in message.lower():
                score += 2.0
                matched.append(kw)
            # Token-level match
            elif all(t in msg_tokens for t in kw_tokens):
                score += 1.0
                matched.append(kw)
            # Substring match on individual token
            elif any(t in msg_tokens and len(t) >= 4 for t in kw_tokens):
                score += 0.3
                matched.append(kw)

        # Normalize by keyword count
        normalized = score / max(len(keywords), 1)
        if normalized > best_score:
            best_score = normalized
            best_intent = entry

    # Threshold: kalau score < 0.3 → fallback
    if best_score < 0.3 or best_intent is None:
        return FAQ_KB[-1], 0.0  # default_fallback

    return best_intent, min(best_score, 1.0)


def chat_faq_handler(message: str) -> dict:
    """Handle user message via FAQ keyword matching (Phase 1).

    Args:
        message: pesan user (string)

    Returns:
        dict: {valid, intent, confidence, answer, suggestions, related_actions, model_version, disclaimer}
    """
    if not message or not message.strip():
        return {
            "valid": False,
            "error": "Pesan kosong. Ketik pertanyaan kamu.",
            "model_version": "faq-rule-based-v1",
        }

    intent_entry, confidence = _match_faq_intent(message)
    return {
        "valid": True,
        "intent": intent_entry["intent"],
        "confidence": round(confidence, 2),
        "answer": intent_entry["answer"],
        "suggestions": intent_entry.get("suggestions", []),
        "related_actions": intent_entry.get("related_actions", []),
        "model_version": "faq-rule-based-v1",
        "disclaimer": "Chatbot phase 1: rule-based FAQ. Phase 2 nanti pakai ML/RAG. Untuk kasus spesifik, konsultasi profesional.",
    }
