"""Blueprint utama: landing, dashboard multi-page, API, dan aset proyek."""
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from app.api import (
    add_to_waitlist,
    calculate_debt_planner,
    calculate_score,
    calculate_simulation,
    chat_faq_handler,
    check_pinjol_status,
    generate_recovery_roadmap,
)
from app.auth import (
    create_user,
    find_user_by_email,
    get_current_user,
    init_oauth,
    is_oauth_configured,
    login_required,
    login_user,
    logout_user,
    update_user_package,
    verify_password,
)

main_bp = Blueprint("main", __name__)


# =================================================================
# LANDING
# =================================================================
@main_bp.route("/")
def index():
    return render_template("index.html")


# =================================================================
# AUTH: Login, Logout, OAuth
# =================================================================
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login page: Google OAuth + demo login (for UAS demo)."""
    from app.auth import seed_demo_users
    seed_demo_users()

    if get_current_user() is not None:
        return redirect(url_for("main.dashboard"))

    next_url = request.args.get("next") or request.form.get("next") or url_for("main.dashboard")

    if request.method == "POST":
        action = request.form.get("action", "")

        if action == "demo":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            user = find_user_by_email(email)
            if user and user.source == "demo" and verify_password(user, password):
                login_user(user)
                flash(f"Login berhasil! Welcome back, {user.name}.", "success")
                return redirect(next_url)
            flash("Email atau password salah. Coba lagi.", "error")
            return render_template("login.html", oauth_enabled=is_oauth_configured(),
                                   next=next_url, oauth_error=False)

        elif action == "register":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            if not (name and email and password and "@" in email and len(password) >= 6):
                flash("Lengkapi semua field. Password minimal 6 karakter.", "error")
                return render_template("login.html", oauth_enabled=is_oauth_configured(),
                                       next=next_url, oauth_error=False)
            if find_user_by_email(email):
                flash("Email sudah terdaftar. Silakan login.", "error")
                return render_template("login.html", oauth_enabled=is_oauth_configured(),
                                       next=next_url, oauth_error=False)
            from werkzeug.security import generate_password_hash
            user = create_user(
                email=email, name=name, package="free", source="register",
                password_hash=generate_password_hash(password),
            )
            login_user(user)
            flash(f"Akun berhasil dibuat! Welcome, {user.name}.", "success")
            return redirect(next_url)

    return render_template("login.html", oauth_enabled=is_oauth_configured(),
                           next=next_url, oauth_error=False)


@main_bp.route("/auth/google")
def auth_google():
    """Initiate Google OAuth flow."""
    if not is_oauth_configured():
        flash("Google OAuth belum di-setup. Gunakan demo login.", "error")
        return redirect(url_for("main.login"))
    oauth = current_app.extensions.get("oauth")
    if not oauth or "google" not in {p.name for p in []}:
        flash("OAuth client tidak ditemukan.", "error")
        return redirect(url_for("main.login"))
    redirect_uri = current_app.config["GOOGLE_REDIRECT_URI"]
    session["oauth_next"] = request.args.get("next") or url_for("main.dashboard")
    return oauth.google.authorize_redirect(redirect_uri)


@main_bp.route("/auth/google/callback")
def auth_google_callback():
    """Handle Google OAuth callback."""
    if not is_oauth_configured():
        flash("Google OAuth belum di-setup.", "error")
        return redirect(url_for("main.login"))
    oauth = current_app.extensions.get("oauth")
    try:
        token = oauth.google.authorize_access_token()
        userinfo = token.get("userinfo") or oauth.google.parse_id_token(token, nonce=None)
        email = userinfo.get("email", "")
        name = userinfo.get("name", email.split("@")[0])
        avatar = userinfo.get("picture", "")
        if not email:
            flash("Google tidak mengembalikan email.", "error")
            return redirect(url_for("main.login"))
        user = find_user_by_email(email)
        if user is None:
            user = create_user(
                email=email, name=name, package="free", source="google",
                avatar_url=avatar,
            )
        login_user(user)
        flash(f"Login dengan Google berhasil! Welcome, {user.name}.", "success")
        next_url = session.pop("oauth_next", url_for("main.dashboard"))
        return redirect(next_url)
    except Exception as e:
        current_app.logger.warning("OAuth callback error: %s", e)
        flash("Login Google gagal. Coba lagi atau gunakan demo login.", "error")
        return redirect(url_for("main.login"))


@main_bp.route("/logout")
def logout():
    logout_user()
    flash("Berhasil logout.", "success")
    return redirect(url_for("main.index"))


@main_bp.route("/upgrade", methods=["POST"])
@login_required
def upgrade_to_premium():
    """Demo-only: upgrade user to premium (no payment gateway for UAS)."""
    user = get_current_user()
    if user and not user.is_premium:
        updated = update_user_package(user.id, "premium")
        if updated:
            # Refresh session: re-login to pick up new package
            login_user(updated)
            flash("Selamat! Anda sekarang Premium. Nikmati semua fitur.", "success")
    return redirect(url_for("main.produk", anchor="pricing"))


# =================================================================
# DASHBOARD (semua protected)
# =================================================================
@main_bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("main.ringkasan"))


@main_bp.route("/dashboard/ringkasan")
@login_required
def ringkasan():
    return render_template("dashboard/ringkasan.html", active_page="ringkasan")


@main_bp.route("/dashboard/analisis")
@login_required
def analisis():
    return render_template("dashboard/analisis.html", active_page="analisis")


@main_bp.route("/dashboard/solusi")
@login_required
def solusi():
    return render_template("dashboard/solusi.html", active_page="solusi")


@main_bp.route("/dashboard/kesimpulan")
@login_required
def kesimpulan():
    return render_template("dashboard/kesimpulan.html", active_page="kesimpulan")


@main_bp.route("/dashboard/produk")
@login_required
def produk():
    return render_template("dashboard/produk.html", active_page="produk")


@main_bp.route("/galbay-score", methods=["GET", "POST"])
def galbay_score():
    """Galbay Score Quiz — personal behavioral risk 0-100.

    Public endpoint (no login required) — high-conversion funnel untuk
    subscription. 6 pertanyaan interaktif, hasil personal + recommendation.
    """
    if request.method == "POST":
        # Collect 6 answers
        answers = {
            "cicilan_aktif": int(request.form.get("cicilan_aktif", 0)),
            "checkout_impulse": int(request.form.get("checkout_impulse", 0)),
            "cicilan_0_persen": int(request.form.get("cicilan_0_persen", 0)),
            "reaksi_tagihan": int(request.form.get("reaksi_tagihan", 0)),
            "dc_pesan": int(request.form.get("dc_pesan", 0)),
            "track_pengeluaran": int(request.form.get("track_pengeluaran", 0)),
        }

        # Score each dimension (0-100)
        # Weight per question (max possible per question)
        # q1 cicilan_aktif: 0=none → 25 pts, 1-2 → 18, 3 → 12, 4+ → 5 (more cicilan = higher risk)
        cicilan_score = max(0, 25 - answers["cicilan_aktif"] * 5)
        # q2 checkout_impulse: 0 → 0, 1-2 → 8, 3-5 → 16, 5+ → 25
        impulse_score = min(25, answers["checkout_impulse"] * 5)
        # q3 cicilan_0_persen: 0 → 0, 1 → 7, 2 → 14, 3 → 21 (scaled 0-3)
        cicilan0_score = min(21, answers["cicilan_0_persen"] * 7)
        # q4 reaksi_tagihan: 0=bayar→0, 1=telat 1-7→8, 2=telat >7→16, 3=ignore→25
        tagihan_score = min(25, answers["reaksi_tagihan"] * 8)
        # q5 dc_pesan: 0=tidak→0, 1=sekali→10, 2=beberapa→18, 3=sering→25
        dc_score = min(25, answers["dc_pesan"] * 8)
        # q6 track_pengeluaran: 0=harian→0(inverse), 1=mingguan→6, 2=bulanan→12, 3=tidak→25
        track_score = min(25, answers["track_pengeluaran"] * 6 + (3 - answers["track_pengeluaran"]) * 0)
        # Better: invert
        track_score = [0, 8, 16, 25][answers["track_pengeluaran"]]

        # Total score (out of 100 max = 25+25+21+25+25+25 → but normalize)
        raw_total = cicilan_score + impulse_score + cicilan0_score + tagihan_score + dc_score + track_score
        max_possible = 146  # 25+25+21+25+25+25
        # Normalize to 0-100
        final_score = round((raw_total / max_possible) * 100)

        # Bucket
        if final_score <= 30:
            bucket = "rendah"
            bucket_label = "Risiko Rendah"
            bucket_color = "green"
        elif final_score <= 55:
            bucket = "sedang"
            bucket_label = "Risiko Sedang"
            bucket_color = "yellow"
        elif final_score <= 75:
            bucket = "tinggi"
            bucket_label = "Risiko Tinggi"
            bucket_color = "orange"
        else:
            bucket = "kritis"
            bucket_label = "Risiko Kritis"
            bucket_color = "red"

        # Personalized recommendations
        recommendations = []
        if answers["cicilan_aktif"] >= 3:
            recommendations.append({
                "priority": "high",
                "title": "Konsolidasi Utang",
                "desc": "Dengan 3+ cicilan aktif, pertimbangkan konsolidasi ke 1 pinjaman dengan bunga lebih rendah.",
                "action": "/dashboard/produk#debt-planner",
                "action_label": "Coba Debt Planner",
            })
        if answers["checkout_impulse"] >= 2:
            recommendations.append({
                "priority": "high",
                "title": "Pending 24 Jam Rule",
                "desc": "Setiap冲动 checkout, tunggu 24 jam. 70% keinginan membeli akan hilang (data behavior).",
                "action": "/dashboard/produk#recovery",
                "action_label": "Recovery Plan",
            })
        if answers["reaksi_tagihan"] >= 2:
            recommendations.append({
                "priority": "high",
                "title": "Auto-Debet Tagihan",
                "desc": "Telat bayar = skor kredit turun. Setup auto-debet dari gaji.",
                "action": "/dashboard/produk#simulasi",
                "action_label": "Lihat Simulasi",
            })
        if answers["dc_pesan"] >= 1:
            recommendations.append({
                "priority": "urgent",
                "title": "Jangan Abaikan DC",
                "desc": "Debt collector ilegal bisa di-lapor ke OJK 157. Cek legalitas di Pinjol Checker.",
                "action": "/dashboard/produk#pinjol-checker",
                "action_label": "Cek Pinjol",
            })
        if answers["track_pengeluaran"] >= 2:
            recommendations.append({
                "priority": "medium",
                "title": "Mulai Tracking",
                "desc": "Catat pengeluaran harian 5 menit. Apps gratis: Money Lover, Catatan Keuangan.",
                "action": "/dashboard/produk",
                "action_label": "Lihat Tools",
            })
        if answers["cicilan_0_persen"] >= 2:
            recommendations.append({
                "priority": "medium",
                "title": "Waspada 'Cicilan 0%'",
                "desc": "Bunga 0% sering disertai biaya admin tersembunyi atau merchant markup 10-20%.",
                "action": "/dashboard/produk#simulasi",
                "action_label": "Hitung Biaya Tersembunyi",
            })

        # Behavioral profile tags (from data 602K)
        profile_tags = []
        if cicilan_score >= 15:
            profile_tags.append({"tag": "Multi-Cicilan", "color": "orange", "count": "21.802 review di dataset kami"})
        if impulse_score >= 16:
            profile_tags.append({"tag": "Impulse Spender", "color": "red", "count": "20.246 review 'Diskusi Produk Fintech'"})
        if tagihan_score >= 16:
            profile_tags.append({"tag": "Late Payer Risk", "color": "red", "count": "13.827 review distress signal"})
        if dc_score >= 10:
            profile_tags.append({"tag": "DC-Targeted", "color": "red", "count": "4.809 review 'Tagihan & Penagihan'"})
        if cicilan0_score >= 14:
            profile_tags.append({"tag": "Marketing-Susceptible", "color": "yellow", "count": "12.445 review 'Bunga & Biaya'"})
        if track_score >= 16:
            profile_tags.append({"tag": "Blind Spender", "color": "yellow", "count": "7.104 review severity sedang"})

        # Stats from real data
        percentile = None
        if final_score >= 75:
            percentile = "8.2% reviewer dataset kami"
        elif final_score >= 55:
            percentile = "23.5% reviewer dataset kami"
        elif final_score >= 30:
            percentile = "44.1% reviewer dataset kami"
        else:
            percentile = "24.2% reviewer dataset kami"

        return render_template(
            "galbay_score_result.html",
            score=final_score,
            bucket=bucket,
            bucket_label=bucket_label,
            bucket_color=bucket_color,
            recommendations=recommendations,
            profile_tags=profile_tags,
            percentile=percentile,
            answers=answers,
            dimension_scores={
                "cicilan": cicilan_score,
                "impulse": impulse_score,
                "cicilan0": cicilan0_score,
                "tagihan": tagihan_score,
                "dc": dc_score,
                "track": track_score,
            },
        )

    return render_template("galbay_score.html")


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
      "apps": ["pinjol", "paylater"],
      "utang": "5to20",
      "selfreward": 7,
      "telat": "1",
      "dc": "1",
      "feeling": "2"
    }
    """
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
    """Hitung Simulasi Cicilan."""
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
    """Tambah email ke waitlist."""
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "email": request.form.get("email", ""),
            "name": request.form.get("name", ""),
            "package": request.form.get("package", "general"),
        }
    result = add_to_waitlist(
        email=data.get("email", ""),
        package=data.get("package", "general"),
        name=data.get("name", ""),
    )
    return jsonify(result)


# =================================================================
# Pinjol Blacklist Checker
# =================================================================
@main_bp.route("/api/check-pinjol", methods=["POST"])
def api_check_pinjol():
    """Cek status OJK pinjol (legal / ilegal / tidak ditemukan)."""
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
    """Hitung strategi bayar utang Snowball vs Avalanche."""
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
# Galbay Recovery Roadmap
# =================================================================
@main_bp.route("/api/recovery-roadmap", methods=["POST"])
def api_recovery_roadmap():
    """Generate roadmap 30/60/90 hari keluar dari galbay."""
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


# =================================================================
# FAQ Chatbot (Phase 2: NLP-like, 38 intents, 8 modules)
# =================================================================
@main_bp.route("/api/chat", methods=["POST"])
def api_chat():
    """Chatbot FAQ (phase 2: synonym, typo tolerance, sentiment, context-aware)."""
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = {
            "message": request.form.get("message", ""),
            "page_context": request.form.get("page_context", ""),
        }

    user = get_current_user()
    user_name = (user.name if user else None) or session.get("user_name")

    result = chat_faq_handler(
        message=data.get("message", ""),
        user_name=user_name,
        page_context=data.get("page_context") or None,
    )
    return jsonify(result)
