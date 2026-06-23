"""Blueprint utama: landing, dashboard multi-page, API, dan aset proyek."""
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for

from app.api import (
    add_to_waitlist,
    calculate_debt_planner,
    calculate_score,
    calculate_simulation,
    check_pinjol_status,
    generate_recovery_roadmap,
    get_dc_template,
    get_dc_templates,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
def dashboard():
    return redirect(url_for("main.ringkasan"))


@main_bp.route("/dashboard/ringkasan")
def ringkasan():
    return render_template("dashboard/ringkasan.html", active_page="ringkasan")


@main_bp.route("/dashboard/analisis")
def analisis():
    return render_template("dashboard/analisis.html", active_page="analisis")


@main_bp.route("/dashboard/solusi")
def solusi():
    return render_template("dashboard/solusi.html", active_page="solusi")


@main_bp.route("/dashboard/kesimpulan")
def kesimpulan():
    return render_template("dashboard/kesimpulan.html", active_page="kesimpulan")


@main_bp.route("/dashboard/produk")
def produk():
    return render_template("dashboard/produk.html", active_page="produk")


@main_bp.route("/health")
def health():
    return {"status": "ok", "service": "galbay-predictor"}


# =================================================================
# API Endpoints (siap untuk swap ke ML model)
# =================================================================
@main_bp.route("/api/health")
def api_health():
    """Health check untuk API."""
    from app.api import MODEL_VERSION
    return jsonify({
        "status": "ok",
        "service": "galbay-predictor-api",
        "model_version": MODEL_VERSION,
    })


@main_bp.route("/api/score", methods=["POST"])
def api_score():
    """Hitung Skor Risiko Galbay.

    Request JSON (form-encoded juga didukung):
    {
      "apps": ["pinjol", "paylater"],  // list of: pinjol, paylater, ewallet, bank
      "utang": "5to20",                  // str: 0, lt5, 5to20, gt20
      "selfreward": 7,                   // int: 1-10
      "telat": "1",                      // str: 0, 1, 2
      "dc": "1",                         // str: 0, 1
      "feeling": "2"                     // str: 0, 1, 2
    }
    """
    # Terima JSON atau form-encoded
    if request.is_json:
        data = request.get_json() or {}
    else:
        apps = request.form.getlist("apps")
        data = {
            "apps": apps,
            "utang": request.form.get("utang", "0"),
            "selfreward": int(request.form.get("selfreward", 3)),
            "telat": request.form.get("telat", "0"),
            "dc": request.form.get("dc", "0"),
            "feeling": request.form.get("feeling", "0"),
        }
    result = calculate_score(data)
    return jsonify(result)


@main_bp.route("/api/simulate", methods=["POST"])
def api_simulate():
    """Hitung Simulasi Cicilan.

    Request JSON (form-encoded juga didukung):
    {
      "nominal": 2000000,    // int/float
      "bunga_pct": 10,       // float: 0-100
      "tenor": 6,            // int: 1-12
      "admin": 50000         // int/float
    }
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "nominal": float(request.form.get("nominal", 0)),
            "bunga_pct": float(request.form.get("bunga_pct", 0)),
            "tenor": int(request.form.get("tenor", 1)),
            "admin": float(request.form.get("admin", 0)),
        }
    result = calculate_simulation(
        nominal=data.get("nominal", 0),
        bunga_pct=data.get("bunga_pct", 0),
        tenor=data.get("tenor", 1),
        admin=data.get("admin", 0),
    )
    return jsonify(result)


@main_bp.route("/api/waitlist", methods=["POST"])
def api_waitlist():
    """Tambah email ke waitlist.

    Request JSON atau form-encoded:
    {
      "email": "user@example.com",
      "package": "premium"  // optional
    }
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "email": request.form.get("email", ""),
            "package": request.form.get("package", "general"),
        }
    result = add_to_waitlist(data.get("email", ""), data.get("package", "general"))
    return jsonify(result)


# =================================================================
# Pinjol Blacklist Checker
# =================================================================
@main_bp.route("/api/check-pinjol", methods=["POST"])
def api_check_pinjol():
    """Cek status OJK pinjol (legal / ilegal / tidak ditemukan).

    Request JSON atau form-encoded:
    {
      "app_name": "Kredivo"  // case-insensitive, partial match
    }
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {"app_name": request.form.get("app_name", "")}
    result = check_pinjol_status(data.get("app_name", ""))
    return jsonify(result)


# =================================================================
# Debt Snowball / Avalanche Planner
# =================================================================
@main_bp.route("/api/debt-planner", methods=["POST"])
def api_debt_planner():
    """Hitung strategi bayar utang Snowball vs Avalanche.

    Request JSON atau form-encoded:
    {
      "debts": [
        {"name": "Kredivo", "balance": 2000000, "bunga_pct": 8, "min_payment": 200000},
        ...
      ],
      "extra_payment": 200000  // optional, default 0
    }
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "debts": [],
            "extra_payment": float(request.form.get("extra_payment", 0)),
        }
    result = calculate_debt_planner(
        debts=data.get("debts", []),
        extra_payment=data.get("extra_payment", 0),
    )
    return jsonify(result)


# =================================================================
# DC Survival Kit
# =================================================================
@main_bp.route("/api/dc-templates", methods=["GET"])
def api_dc_templates():
    """Return semua template chat untuk negosiasi debt collector."""
    return jsonify(get_dc_templates())


@main_bp.route("/api/dc-templates/<template_id>", methods=["GET"])
def api_dc_template(template_id: str):
    """Return 1 DC template by id."""
    return jsonify(get_dc_template(template_id))


# =================================================================
# Galbay Recovery Roadmap
# =================================================================
@main_bp.route("/api/recovery-roadmap", methods=["POST"])
def api_recovery_roadmap():
    """Generate roadmap 30/60/90 hari keluar dari galbay.

    Request JSON atau form-encoded:
    {
      "total_utang": 5000000,
      "income_bulanan": 3000000,
      "sudah_dc": true,  // sudah pernah ditagih DC?
      "hari_telat": 15    // berapa hari telat
    }
    """
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "total_utang": float(request.form.get("total_utang", 0)),
            "income_bulanan": float(request.form.get("income_bulanan", 0)),
            "sudah_dc": request.form.get("sudah_dc", "false").lower() == "true",
            "hari_telat": int(request.form.get("hari_telat", 0)),
        }
    result = generate_recovery_roadmap(data)
    return jsonify(result)


# =================================================================
# Aset statis
# =================================================================
@main_bp.route("/assets/<path:filename>")
def asset_file(filename: str):
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root / "assets", filename)
