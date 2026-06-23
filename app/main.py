"""Blueprint utama: landing, dashboard, dan aset proyek."""
from pathlib import Path

from flask import Blueprint, current_app, render_template, send_from_directory

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/health")
def health():
    return {"status": "ok", "service": "galbay-predictor"}


@main_bp.route("/assets/<path:filename>")
def asset_file(filename: str):
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root / "assets", filename)
