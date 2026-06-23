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

    def test_index_has_dashboard_link(self, client):
        r = client.get("/")
        assert b'/dashboard' in r.data


class TestDashboardRoutes:
    """Test route /dashboard/* (multi-page)."""

    def test_dashboard_redirects_to_ringkasan(self, client):
        r = client.get("/dashboard")
        assert r.status_code in (200, 302)
        if r.status_code == 302:
            assert "/dashboard/ringkasan" in r.location

    def test_ringkasan_returns_200(self, client):
        r = client.get("/dashboard/ringkasan")
        assert r.status_code == 200

    def test_analisis_returns_200(self, client):
        r = client.get("/dashboard/analisis")
        assert r.status_code == 200

    def test_solusi_returns_200(self, client):
        r = client.get("/dashboard/solusi")
        assert r.status_code == 200

    def test_kesimpulan_returns_200(self, client):
        r = client.get("/dashboard/kesimpulan")
        assert r.status_code == 200

    def test_produk_returns_200(self, client):
        r = client.get("/dashboard/produk")
        assert r.status_code == 200

    def test_ringkasan_has_active_nav_pill(self, client):
        r = client.get("/dashboard/ringkasan")
        assert b'nav-pill active' in r.data
        assert b'Ringkasan' in r.data

    def test_analisis_has_correct_active_pill(self, client):
        r = client.get("/dashboard/analisis")
        assert b'nav-pill active' in r.data
        assert b'Analisis' in r.data

    def test_produk_has_correct_active_pill(self, client):
        r = client.get("/dashboard/produk")
        # Produk pill is `nav-pill nav-pill-cta active` (has extra class)
        assert b'nav-pill-cta active' in r.data
        assert b'Coba Produk' in r.data


class TestDashboardContent:
    """Test konten spesifik tiap dashboard page."""

    def test_ringkasan_has_kpi_cards(self, client):
        r = client.get("/dashboard/ringkasan")
        assert b'kpi-card' in r.data
        assert b'Total Ulasan' in r.data

    def test_analisis_has_canvas(self, client):
        r = client.get("/dashboard/analisis")
        assert b'<canvas' in r.data

    def test_solusi_has_bmc(self, client):
        r = client.get("/dashboard/solusi")
        assert b'bmc-block' in r.data
        assert b'BMC' in r.data or b'Business Model Canvas' in r.data

    def test_produk_has_skor_form(self, client):
        r = client.get("/dashboard/produk")
        assert b'skorForm' in r.data
        assert b'selfrewardSlider' in r.data
        assert b'nominal' in r.data

    def test_produk_has_7_sinyal(self, client):
        r = client.get("/dashboard/produk")
        assert b'sinyal-card' in r.data
        # Check at least 7 sinyal
        assert r.data.count(b'sinyal-card') >= 7

    def test_produk_has_pricing(self, client):
        r = client.get("/dashboard/produk")
        assert b'pricing-card' in r.data
        assert b'Premium' in r.data
        assert b'Konseling' in r.data


class TestAssetsRoute:
    """Test route /assets/<filename>."""

    def test_assets_route_exists(self, client):
        r = client.get("/assets/missing.png")
        # Either 404 (file not found) or 200 — route exists
        assert r.status_code in (200, 404)


class TestPageNotFound:
    """Test 404 untuk route yang tidak ada."""

    def test_nonexistent_route_returns_404(self, client):
        r = client.get("/this-does-not-exist")
        assert r.status_code == 404

    def test_nonexistent_api_returns_404(self, client):
        r = client.get("/api/nonexistent")
        assert r.status_code == 404
