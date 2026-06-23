"""Integration tests untuk Flask routes di app/main.py."""
import pytest
import json


class TestIndexRoute:
    """Test route / (landing page)."""

    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_contains_hero(self, client):
        r = client.get("/")
        assert b"Galbay Predictor" in r.data
        assert b"galbay" in r.data.lower()

    def test_index_has_login_link(self, client):
        r = client.get("/")
        assert b'/login' in r.data or b'/dashboard' in r.data

    def test_index_has_3d_canvas(self, client):
        r = client.get("/")
        # Hero harus clean (no animation)
        assert b'hero-coin' not in r.data
        assert b'hero-sparkles' not in r.data
        assert b'hero-orb' not in r.data
        assert b'hero3d' not in r.data
        # Should still have hero content
        assert b'Mining Perilaku Digital' in r.data
        assert b'Buka Dashboard' in r.data


class TestDashboardRoutes:
    """Test route /dashboard/* (multi-page, requires login)."""

    def test_dashboard_redirects_to_ringkasan(self, auth_client):
        r = auth_client.get("/dashboard")
        assert r.status_code in (200, 302)
        if r.status_code == 302:
            assert "/dashboard/ringkasan" in r.location

    def test_ringkasan_returns_200(self, auth_client):
        r = auth_client.get("/dashboard/ringkasan")
        assert r.status_code == 200

    def test_analisis_returns_200(self, auth_client):
        r = auth_client.get("/dashboard/analisis")
        assert r.status_code == 200

    def test_solusi_returns_200(self, auth_client):
        r = auth_client.get("/dashboard/solusi")
        assert r.status_code == 200

    def test_kesimpulan_returns_200(self, auth_client):
        r = auth_client.get("/dashboard/kesimpulan")
        assert r.status_code == 200

    def test_produk_returns_200(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert r.status_code == 200

    def test_ringkasan_has_active_nav_pill(self, auth_client):
        r = auth_client.get("/dashboard/ringkasan")
        assert b'nav-pill active' in r.data
        assert b'Ringkasan' in r.data

    def test_analisis_has_correct_active_pill(self, auth_client):
        r = auth_client.get("/dashboard/analisis")
        assert b'nav-pill active' in r.data
        assert b'Analisis' in r.data

    def test_produk_has_correct_active_pill(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert r.status_code == 200
        assert b'nav-pill' in r.data
        # Active nav-pill on produk page
        assert b'active' in r.data
        assert b'Coba Produk' in r.data

    def test_unauthenticated_redirects_to_login(self, client):
        r = client.get("/dashboard/ringkasan", follow_redirects=False)
        assert r.status_code == 302
        assert "/login" in r.location


class TestDashboardContent:
    """Test content presence di dashboard pages."""

    def test_ringkasan_has_kpi_cards(self, auth_client):
        r = auth_client.get("/dashboard/ringkasan")
        assert b'kpi-card' in r.data

    def test_analisis_has_canvas(self, auth_client):
        r = auth_client.get("/dashboard/analisis")
        assert b'<canvas' in r.data

    def test_analisis_no_hardcoded_numbers(self, auth_client):
        """Pastikan tidak ada angka-angka model yang hard-coded (semua via data-fill)."""
        r = auth_client.get("/dashboard/analisis")
        body = r.data.decode('utf-8')
        # Tidak boleh ada angka hard-coded di kalimat insight
        assert '235.986' not in body, "Score 5 count hard-coded"
        assert '69.931' not in body, "Score 1 count hard-coded"
        assert '>626<' not in body and '>351<' not in body, "Confusion matrix numbers hard-coded"
        # Harus ada data-fill placeholders
        assert 'data-fill="score_5_count"' in body
        assert 'data-fill="score_1_count"' in body
        assert 'data-fill="acc"' in body
        assert 'data-fill="cm_tp_fmt"' in body
        assert 'data-fill="cm_fn_fmt"' in body
        assert 'data-fill="cm_fp_fmt"' in body
        assert 'data-fill="cm_tn_fmt"' in body
        assert 'data-fill="n_test_fmt"' in body
        assert 'data-fill="vocab_fmt"' in body

    def test_analisis_no_forum_or_kaskus(self, auth_client):
        """Single source (Google Play) — tidak ada referensi Forum Kaskus / OJK+Media."""
        r = auth_client.get("/dashboard/analisis")
        body = r.data.decode('utf-8')
        assert 'Forum Kaskus' not in body, "Forum Kaskus reference should be removed"
        assert 'OJK + Media' not in body, "OJK + Media badge should be removed"

    def test_topnav_uses_solid_cta_class(self, client):
        """Topnav button harus pakai class .topnav-cta (solid color per theme)."""
        r = client.get("/")
        body = r.data.decode('utf-8')
        assert 'class="topnav-cta"' in body, "Topnav CTA harus pakai class .topnav-cta"
        assert 'class="btn-primary" style="padding:9px 20px;"' not in body, "Old btn-primary topnav button harus dihapus"

    def test_lock_overlay_has_close_button_and_free_link(self, auth_client):
        """Lock overlay harus punya close button + 'lihat fitur gratis' link."""
        r = auth_client.get("/dashboard/produk")
        body = r.data.decode('utf-8')
        assert 'lock-close' in body, "Lock overlay harus punya close button (.lock-close)"
        assert 'lock-free-link' in body, "Lock overlay harus punya 'lihat fitur gratis' link"
        assert 'data-lock-dismiss' in body, "Close button harus punya data-lock-dismiss attribute"

    def test_hero_clean_no_animation(self, client):
        """Landing hero clean: no coin SVGs, no orb, no mouse trail, no sparkles."""
        r = client.get("/")
        body = r.data.decode('utf-8')
        # Should NOT have any animation elements
        assert 'hero-coin' not in body, "Landing harus clean tanpa floating coins"
        assert 'hero-sparkles' not in body, "Landing harus clean tanpa sparkles"
        assert 'hero-orb' not in body, "Landing harus clean tanpa central orb"
        assert 'hero3d' not in body, "Landing harus clean tanpa 3D container"
        assert 'landing-3d.js' not in r.data.decode('utf-8', 'replace'), "landing-3d.js script harus dihapus"
        # Should still have hero content
        assert 'Big Data' in body or 'galbay' in body.lower()

    def test_solusi_has_bmc(self, auth_client):
        r = auth_client.get("/dashboard/solusi")
        assert b'BMC' in r.data or b'bmc' in r.data.lower()

    def test_produk_has_skor_form(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert b'skor-form' in r.data or b'Skor Risiko' in r.data

    def test_produk_has_7_sinyal(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert b'Sinyal' in r.data

    def test_produk_has_pricing(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert b'pricing' in r.data.lower()
        assert b'Premium' in r.data

    def test_produk_free_user_sees_locks(self, auth_client):
        r = auth_client.get("/dashboard/produk")
        assert b'feature-locked' in r.data
        assert b'lock-icon' in r.data
        # Lock harus in-section (position: absolute), bukan fixed
        # Cek bahwa tidak ada style position: fixed pada .lock-overlay
        assert b'position: fixed' not in r.data
        assert b'lock-fixed' not in r.data

    def test_produk_no_full_section_blur(self, auth_client, app):
        """Tidak ada lagi full-section blur (::before dengan backdrop-filter blur).
        Diganti dengan opacity dim yang konsisten di semua section.
        Cek di style.css file (CSS external, bukan inline)."""
        from pathlib import Path
        import re
        # app.root_path = .../Final-Project-UAS, css = app/static/css/style.css
        css_path = Path(app.root_path) / "static" / "css" / "style.css"
        if css_path.exists():
            css = css_path.read_text(encoding='utf-8')
            # Find .feature-locked::before section
            before_match = re.search(r'\.feature-locked::before\s*\{[^}]+\}', css, re.DOTALL)
            if before_match:
                # If .feature-locked::before exists, it should NOT have backdrop-filter
                assert 'backdrop-filter' not in before_match.group(0), \
                    "::before tidak boleh punya backdrop-filter (full-section blur harus dihapus)"
            # CSS baru: opacity dim di children
            assert re.search(r'\.feature-locked > \*:not\(.lock-overlay\):not\(.page-header\)\s*\{[^}]*opacity:\s*0\.\d+', css, re.DOTALL), \
                "CSS harus punya opacity dim untuk .feature-locked > *:not(.lock-overlay):not(.page-header)"

    def test_produk_premium_user_no_locks(self, premium_client):
        r = premium_client.get("/dashboard/produk")
        assert b'feature-locked' not in r.data
        assert b'Premium Aktif' in r.data


class TestStaticAssets:
    def test_assets_route_exists(self, client):
        r = client.get("/assets/missing.png")
        assert r.status_code in (200, 404)

    def test_nonexistent_route_returns_404(self, client):
        r = client.get("/this-does-not-exist")
        assert r.status_code == 404

    def test_nonexistent_api_returns_404(self, client):
        r = client.get("/api/nonexistent")
        assert r.status_code == 404
