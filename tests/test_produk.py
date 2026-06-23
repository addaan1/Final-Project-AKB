"""Integration tests untuk page Produk — fokus pada Skor Risiko behavior."""
import json


class TestSkorFormRendering:
    """Test rendering form Skor Risiko."""

    def test_skor_form_has_all_inputs(self, client):
        r = client.get("/dashboard/produk")
        # 4 app checkboxes
        for app in [b"pinjol", b"paylater", b"ewallet", b"bank"]:
            assert app in r.data
        # Utang radios
        for val in [b'value="0"', b'value="lt5"', b'value="5to20"', b'value="gt20"']:
            assert val in r.data
        # Slider
        assert b'selfrewardSlider' in r.data
        # Submit button
        assert b'Hitung Skor' in r.data or b'HITUNG' in r.data.upper()

    def test_skor_form_has_tooltips(self, client):
        r = client.get("/dashboard/produk")
        assert b'form-tooltip' in r.data

    def test_skor_result_div_exists(self, client):
        r = client.get("/dashboard/produk")
        assert b'skorResult' in r.data
        assert b'skor-placeholder' in r.data


class TestSkorAPIIntegration:
    """Test integrasi form dengan API."""

    def test_post_score_aman(self, client):
        r = client.post("/api/score",
                        json={"apps": [], "utang": "0", "selfreward": 1,
                              "telat": "0", "dc": "0", "feeling": "0"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["category"] == "aman"
        assert data["score"] < 31

    def test_post_score_bahaya(self, client):
        r = client.post("/api/score",
                        json={"apps": ["pinjol", "paylater"], "utang": "gt20",
                              "selfreward": 8, "telat": "2", "dc": "1", "feeling": "2"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["category"] == "bahaya"
        assert data["score"] > 60

    def test_post_score_form_encoded(self, client):
        """Test form-encoded juga jalan."""
        r = client.post("/api/score",
                        data={"apps": ["pinjol"], "utang": "5to20", "selfreward": "5",
                              "telat": "1", "dc": "0", "feeling": "1"})
        assert r.status_code == 200
        data = r.get_json()
        assert "score" in data
        assert "recommendations" in data

    def test_post_score_response_has_required_fields(self, client):
        r = client.post("/api/score",
                        json={"apps": ["pinjol"], "utang": "5to20", "selfreward": 5,
                              "telat": "1", "dc": "0", "feeling": "1"})
        data = r.get_json()
        for field in ["score", "category", "category_label", "description",
                      "recommendations", "model_version", "disclaimer"]:
            assert field in data, f"Missing field: {field}"

    def test_post_score_recommendations_is_list(self, client):
        r = client.post("/api/score",
                        json={"apps": ["pinjol"], "utang": "gt20", "selfreward": 8,
                              "telat": "1", "dc": "1", "feeling": "2"})
        data = r.get_json()
        assert isinstance(data["recommendations"], list)
        assert 1 <= len(data["recommendations"]) <= 3


class TestSimulasiIntegration:
    """Test integrasi form Simulasi Cicilan."""

    def test_post_simulate_basic(self, client):
        r = client.post("/api/simulate",
                        json={"nominal": 2_000_000, "bunga_pct": 10, "tenor": 6, "admin": 50_000})
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True
        assert data["cicilan"] == 541_667

    def test_post_simulate_form_encoded(self, client):
        r = client.post("/api/simulate",
                        data={"nominal": "1000000", "bunga_pct": "5",
                              "tenor": "12", "admin": "0"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True

    def test_simulate_invalid_input(self, client):
        r = client.post("/api/simulate",
                        json={"nominal": -100, "bunga_pct": 10, "tenor": 6, "admin": 0})
        data = r.get_json()
        assert data["valid"] is False
        assert "errors" in data

    def test_simulate_response_has_all_fields(self, client):
        r = client.post("/api/simulate",
                        json={"nominal": 2_000_000, "bunga_pct": 10, "tenor": 6, "admin": 50_000})
        data = r.get_json()
        for field in ["valid", "cicilan", "total_bunga", "total_bayar",
                      "bunga_efektif_tahunan", "warning", "tip"]:
            assert field in data, f"Missing field: {field}"


class TestWaitlistIntegration:
    """Test integrasi form waitlist."""

    def test_waitlist_form_exists(self, client):
        r = client.get("/dashboard/produk")
        assert b'waitlistForm' in r.data
        assert b'waitlistEmail' in r.data

    def test_post_waitlist_valid(self, client, tmp_path, monkeypatch):
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        r = client.post("/api/waitlist",
                        json={"email": "newuser@example.com", "package": "premium"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True

    def test_post_waitlist_form_encoded(self, client, tmp_path, monkeypatch):
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        r = client.post("/api/waitlist",
                        data={"email": "formuser@example.com", "package": "konseling"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True

    def test_waitlist_invalid_email(self, client):
        r = client.post("/api/waitlist",
                        json={"email": "notanemail", "package": "premium"})
        data = r.get_json()
        assert data["valid"] is False
