"""Blueprint utama: landing, dashboard multi-page, API, dan aset proyek."""
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, url_for

from app.api import add_to_waitlist, calculate_score, calculate_simulation

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
# Aset statis
# =================================================================
@main_bp.route("/assets/<path:filename>")
def asset_file(filename: str):
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root / "assets", filename)
