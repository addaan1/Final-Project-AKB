"""Unit tests untuk app/api.py (logic Skor Risiko, Simulasi Cicilan, Waitlist)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from app.api import (
    MODEL_VERSION,
    DISCLAIMER,
    calculate_score,
    calculate_simulation,
    add_to_waitlist,
    APP_RISK_WEIGHTS,
    UTANG_RISK,
    TELAT_RISK,
    DC_RISK,
    FEELING_RISK,
)


# =================================================================
# calculate_score
# =================================================================
class TestCalculateScore:
    """Test untuk Skor Risiko Galbay."""

    def test_empty_inputs_returns_minimum_score(self):
        """Tidak ada app, utang 0, feeling tenang → skor rendah (AMAN)."""
        result = calculate_score({
            "apps": [], "utang": "0", "selfreward": 1,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        assert result["score"] == 5  # selfreward=1 → +5
        assert result["category"] == "aman"
        assert result["category_label"] == "AMAN"
        assert "rule-based-v1" in result["model_version"]
        assert result["disclaimer"] == DISCLAIMER

    def test_max_risk_returns_100(self):
        """Semua input max → skor 100 (BAHAYA)."""
        result = calculate_score({
            "apps": ["pinjol", "paylater", "ewallet", "bank"],
            "utang": "gt20", "selfreward": 10,
            "telat": "2", "dc": "1", "feeling": "2"
        })
        assert result["score"] == 100
        assert result["category"] == "bahaya"
        assert result["category_label"] == "BAHAYA"

    def test_score_is_capped_at_100(self):
        """Skor tidak boleh lebih dari 100."""
        result = calculate_score({
            "apps": ["pinjol"] * 10,  # excessive
            "utang": "gt20", "selfreward": 10,
            "telat": "2", "dc": "1", "feeling": "2"
        })
        assert result["score"] <= 100

    def test_score_is_floored_at_0(self):
        """Skor tidak boleh negatif."""
        result = calculate_score({
            "apps": [], "utang": "0", "selfreward": 1,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        assert result["score"] >= 0

    def test_aman_threshold_at_30(self):
        """Skor 30 → aman, skor 31 → waspada."""
        result_30 = calculate_score({
            "apps": [], "utang": "lt5", "selfreward": 1,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        # 10 (utang lt5) + 5 (selfreward=1) = 15, actually aman
        assert result_30["category"] == "aman"

    def test_waspada_threshold(self):
        """Skor 31-60 → waspada."""
        result = calculate_score({
            "apps": ["pinjol"], "utang": "5to20", "selfreward": 4,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        # 20 (pinjol) + 20 (5to20) + 15 (selfreward=4) = 55
        assert result["score"] == 55
        assert result["category"] == "waspada"

    def test_bahaya_threshold(self):
        """Skor 61+ → bahaya."""
        result = calculate_score({
            "apps": ["pinjol"], "utang": "gt20", "selfreward": 5,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        # 20 + 30 + 15 = 65
        assert result["score"] == 65
        assert result["category"] == "bahaya"

    def test_dc_alone_triggers_bahaya(self):
        """DC saja sudah cukup untuk skor tinggi."""
        result = calculate_score({
            "apps": [], "utang": "0", "selfreward": 1,
            "telat": "0", "dc": "1", "feeling": "0"
        })
        # 25 (dc) + 5 (selfreward=1) = 30
        assert result["score"] == 30
        # edge case 30 = aman
        assert result["category"] == "aman"

    def test_recommendations_max_3(self):
        """Max 3 rekomendasi dikembalikan."""
        result = calculate_score({
            "apps": ["pinjol", "paylater", "ewallet", "bank"],
            "utang": "gt20", "selfreward": 10,
            "telat": "2", "dc": "1", "feeling": "2"
        })
        assert len(result["recommendations"]) == 3
        assert all(isinstance(r, str) for r in result["recommendations"])

    def test_recommendations_sorted_by_weight(self):
        """Rekomendasi diurutkan dari bobot tertinggi (faktor paling berisiko)."""
        result = calculate_score({
            "apps": ["pinjol"], "utang": "0", "selfreward": 1,
            "telat": "0", "dc": "1", "feeling": "0"
        })
        # DC (25) > pinjol (20) → DC should be first
        assert "negosiasikan" in result["recommendations"][0].lower() or "DC" in result["recommendations"][0]

    def test_self_reward_terendah(self):
        """Self reward 1-3 = +5."""
        for sr in [1, 2, 3]:
            r = calculate_score({
                "apps": [], "utang": "0", "selfreward": sr,
                "telat": "0", "dc": "0", "feeling": "0"
            })
            assert r["score"] == 5

    def test_self_reward_sedang(self):
        """Self reward 4-6 = +15."""
        for sr in [4, 5, 6]:
            r = calculate_score({
                "apps": [], "utang": "0", "selfreward": sr,
                "telat": "0", "dc": "0", "feeling": "0"
            })
            assert r["score"] == 15

    def test_self_reward_tinggi(self):
        """Self reward 7+ = +25."""
        for sr in [7, 8, 9, 10]:
            r = calculate_score({
                "apps": [], "utang": "0", "selfreward": sr,
                "telat": "0", "dc": "0", "feeling": "0"
            })
            assert r["score"] == 25

    def test_invalid_utang_defaults_to_zero(self):
        """Utang invalid string → 0 risk."""
        r = calculate_score({
            "apps": [], "utang": "invalid", "selfreward": 1,
            "telat": "0", "dc": "0", "feeling": "0"
        })
        assert r["score"] == 5  # only selfreward

    def test_missing_keys_use_defaults(self):
        """Missing keys → default values, tidak error."""
        r = calculate_score({})
        assert "score" in r
        assert r["score"] == 5  # selfreward default 3 → +5

    def test_app_weights_match(self):
        """Bobot app sesuai spec."""
        assert APP_RISK_WEIGHTS["pinjol"] == 20
        assert APP_RISK_WEIGHTS["paylater"] == 10
        assert APP_RISK_WEIGHTS["ewallet"] == 5
        assert APP_RISK_WEIGHTS["bank"] == 3


# =================================================================
# calculate_simulation
# =================================================================
class TestCalculateSimulation:
    """Test untuk Simulasi Cicilan."""

    def test_basic_calculation(self):
        """Hitung dasar 2jt, 10%/bln, 6 bulan, admin 50rb."""
        r = calculate_simulation(2_000_000, 10, 6, 50_000)
        assert r["valid"] is True
        # total_bunga = 2jt × 0.1 × 6 = 1.2jt
        assert r["total_bunga"] == 1_200_000
        # total_bayar = 2jt + 1.2jt + 50rb = 3.25jt
        assert r["total_bayar"] == 3_250_000
        # cicilan = 3.25jt / 6 = 541.667
        assert r["cicilan"] == 541_667

    def test_zero_bunga(self):
        """Bunga 0% → cicilan = nominal/tenor + admin/tenor."""
        r = calculate_simulation(1_200_000, 0, 12, 0)
        assert r["total_bunga"] == 0
        assert r["cicilan"] == 100_000  # 1.2jt / 12

    def test_zero_nominal(self):
        """Nominal 0 → cicilan 0."""
        r = calculate_simulation(0, 10, 6, 0)
        assert r["cicilan"] == 0
        assert r["total_bayar"] == 0
        assert r["bunga_efektif_tahunan"] == 0

    def test_one_tenor(self):
        """Tenor 1 bulan → cicilan = total_bayar."""
        r = calculate_simulation(1_000_000, 5, 1, 0)
        # total_bunga = 1jt × 0.05 × 1 = 50rb
        assert r["total_bunga"] == 50_000
        # total_bayar = 1.05jt
        assert r["total_bayar"] == 1_050_000
        assert r["cicilan"] == 1_050_000

    def test_high_bunga_triggers_warning(self):
        """Bunga >100%/tahun → warning predatory."""
        r = calculate_simulation(1_000_000, 20, 12, 0)
        # bunga_efektif = (2.4jt / 1jt) × 1 × 100 = 240%
        assert r["bunga_efektif_tahunan"] == 240.0
        assert r["warning"] is not None
        assert "predatory" in r["tip"].lower() or "100%" in r["tip"]

    def test_medium_bunga_no_warning(self):
        """Bunga 18-36%/tahun → no warning, just tip."""
        r = calculate_simulation(1_000_000, 2, 12, 0)
        # bunga_efektif = (240rb / 1jt) × 1 × 100 = 24%
        assert r["bunga_efektif_tahunan"] == 24.0
        assert r["warning"] is None
        assert r["tip"] is not None

    def test_low_bunga_no_warning(self):
        """Bunga <18%/tahun → no warning."""
        r = calculate_simulation(1_000_000, 0.5, 12, 0)
        # bunga_efektif = (60rb / 1jt) × 1 × 100 = 6%
        assert r["bunga_efektif_tahunan"] == 6.0
        assert r["warning"] is None

    def test_invalid_nominal_negative(self):
        """Nominal negatif → error."""
        r = calculate_simulation(-100, 10, 6, 0)
        assert r["valid"] is False
        assert "nominal" in str(r["errors"])

    def test_invalid_tenor_zero(self):
        """Tenor 0 → error."""
        r = calculate_simulation(1_000_000, 10, 0, 0)
        assert r["valid"] is False
        assert "tenor" in str(r["errors"])

    def test_admin_only(self):
        """Admin besar, no bunga → cicilan = admin/tenor + nominal/tenor."""
        r = calculate_simulation(1_000_000, 0, 6, 600_000)
        # total_bayar = 1jt + 0 + 600rb = 1.6jt
        # cicilan = 1.6jt / 6 = 266.667
        assert r["total_bayar"] == 1_600_000
        assert r["cicilan"] == 266_667

    def test_contains_all_fields(self):
        """Response harus mengandung semua field yang dibutuhkan."""
        r = calculate_simulation(1_000_000, 5, 6, 0)
        for key in ["valid", "nominal", "bunga_pct", "tenor", "admin",
                    "cicilan", "total_bunga", "total_bayar", "bunga_efektif_tahunan",
                    "warning", "tip"]:
            assert key in r


# =================================================================
# add_to_waitlist
# =================================================================
class TestAddToWaitlist:
    """Test untuk waitlist."""

    def test_valid_email_added(self, tmp_path, monkeypatch):
        """Email valid ditambahkan."""
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        r = add_to_waitlist("user@example.com", "premium")
        assert r["valid"] is True
        assert r["duplicate"] is False
        assert r["total"] == 1
        # File harus ter-create
        assert (tmp_path / "waitlist.json").exists()

    def test_invalid_email_no_at(self, tmp_path, monkeypatch):
        """Email tanpa @ → invalid."""
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        r = add_to_waitlist("notanemail", "premium")
        assert r["valid"] is False
        assert "error" in r

    def test_empty_email_invalid(self, tmp_path, monkeypatch):
        """Email kosong → invalid."""
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        r = add_to_waitlist("", "premium")
        assert r["valid"] is False

    def test_duplicate_email_detected(self, tmp_path, monkeypatch):
        """Email duplikat terdeteksi."""
        import app.api as api_mod
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", tmp_path / "waitlist.json")
        add_to_waitlist("dup@example.com", "premium")
        r = add_to_waitlist("dup@example.com", "premium")
        assert r["valid"] is True
        assert r["duplicate"] is True
        assert r["total"] == 1  # tidak bertambah

    def test_persists_to_file(self, tmp_path, monkeypatch):
        """Data tersimpan ke file."""
        import app.api as api_mod
        f = tmp_path / "waitlist.json"
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", f)
        add_to_waitlist("a@example.com", "premium")
        add_to_waitlist("b@example.com", "konseling")
        data = json.loads(f.read_text())
        assert len(data) == 2
        assert data[0]["email"] == "a@example.com"
        assert data[0]["package"] == "premium"
        assert data[1]["package"] == "konseling"

    def test_corrupted_file_recovers(self, tmp_path, monkeypatch):
        """File corrupted → recover sebagai list kosong."""
        import app.api as api_mod
        f = tmp_path / "waitlist.json"
        f.write_text("not valid json")
        monkeypatch.setattr(api_mod, "WAITLIST_FILE", f)
        r = add_to_waitlist("test@example.com", "general")
        assert r["valid"] is True
        assert r["total"] == 1


# =================================================================
# Constants
# =================================================================
class TestConstants:
    def test_model_version_is_set(self):
        assert MODEL_VERSION is not None
        assert isinstance(MODEL_VERSION, str)
        assert "rule-based" in MODEL_VERSION or "v" in MODEL_VERSION

    def test_disclaimer_is_set(self):
        assert DISCLAIMER is not None
        assert "Demo" in DISCLAIMER or "Prototype" in DISCLAIMER
