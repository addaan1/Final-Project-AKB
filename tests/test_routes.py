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
        # CSS-animated hero with sparkles + coins
        assert b'hero3d' in r.data
        assert b'hero-sparkles' in r.data
        assert b'hero-coins' in r.data


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
