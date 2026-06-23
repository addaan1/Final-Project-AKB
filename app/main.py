"""Blueprint utama: landing, dashboard multi-page, dan aset proyek."""
from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, send_from_directory, url_for

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


@main_bp.route("/health")
def health():
    return {"status": "ok", "service": "galbay-predictor"}


@main_bp.route("/assets/<path:filename>")
def asset_file(filename: str):
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root / "assets", filename)
