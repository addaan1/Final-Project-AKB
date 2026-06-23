"""Unit tests detail untuk Simulasi Cicilan — edge cases & math correctness."""
import math
import pytest

from app.api import calculate_simulation


class TestSimulasiMathCorrectness:
    """Test kebenaran rumus matematika."""

    def test_total_bunga_formula(self):
        """total_bunga = nominal × (bunga_pct/100) × tenor."""
        cases = [
            (1_000_000, 10, 6, 600_000),    # 1jt × 10% × 6
            (5_000_000, 5, 12, 3_000_000),   # 5jt × 5% × 12
            (500_000, 2, 3, 30_000),         # 500rb × 2% × 3
            (10_000_000, 1.5, 24, 3_600_000),  # 10jt × 1.5% × 24
        ]
        for nominal, bunga, tenor, expected in cases:
            r = calculate_simulation(nominal, bunga, tenor, 0)
            assert r["total_bunga"] == expected, f"Failed for {nominal}@{bunga}%x{tenor}"

    def test_cicilan_is_total_bayar_divided_by_tenor(self):
        """cicilan = total_bayar / tenor."""
        r = calculate_simulation(1_200_000, 5, 12, 0)
        expected_cicilan = r["total_bayar"] / 12
        assert abs(r["cicilan"] - expected_cicilan) < 1  # rounding tolerance

    def test_total_bayar_is_nominal_plus_bunga_plus_admin(self):
        """total_bayar = nominal + total_bunga + admin."""
        r = calculate_simulation(2_000_000, 10, 6, 100_000)
        expected = 2_000_000 + r["total_bunga"] + 100_000
        assert r["total_bayar"] == expected

    def test_bunga_efektif_calculation(self):
        """bunga_efektif = (total_bunga / nominal) × (12/tenor) × 100."""
        cases = [
            (1_000_000, 10, 12, 120.0),   # 100% effective
            (1_000_000, 5, 12, 60.0),     # 60%
            (1_000_000, 2, 6, 24.0),      # 24%
            (1_000_000, 1, 12, 12.0),     # 12%
        ]
        for nominal, bunga, tenor, expected in cases:
            r = calculate_simulation(nominal, bunga, tenor, 0)
            assert abs(r["bunga_efektif_tahunan"] - expected) < 0.1, \
                f"Failed for {nominal}@{bunga}%x{tenor}"


class TestSimulasiEdgeCases:
    """Test edge cases."""

    def test_zero_nominal_no_error(self):
        r = calculate_simulation(0, 10, 6, 0)
        assert r["valid"] is True
        assert r["cicilan"] == 0
        assert r["total_bunga"] == 0
        assert r["bunga_efektif_tahunan"] == 0

    def test_zero_bunga(self):
        r = calculate_simulation(1_000_000, 0, 12, 0)
        assert r["valid"] is True
        assert r["total_bunga"] == 0
        # 1.000.000 / 12 = 83.333,33 → rounded = 83.333
        assert r["cicilan"] == 83_333
        assert r["bunga_efektif_tahunan"] == 0
        assert r["warning"] is None

    def test_zero_admin(self):
        r = calculate_simulation(1_000_000, 5, 12, 0)
        assert r["total_bayar"] == r["total_bunga"] + 1_000_000

    def test_one_month_tenor(self):
        r = calculate_simulation(1_000_000, 5, 1, 0)
        assert r["cicilan"] == r["total_bayar"]  # single payment
        assert r["total_bunga"] == 50_000

    def test_very_large_nominal(self):
        """Test nominal besar (100jt)."""
        r = calculate_simulation(100_000_000, 5, 24, 500_000)
        assert r["valid"] is True
        assert r["cicilan"] > 0
        assert r["total_bayar"] > 100_000_000

    def test_very_small_bunga(self):
        """Bunga 0.1% (minimum slider)."""
        r = calculate_simulation(1_000_000, 0.1, 12, 0)
        assert r["valid"] is True
        assert r["total_bunga"] == 12_000  # 1jt × 0.1% × 12
        assert r["bunga_efektif_tahunan"] < 2  # ~1.2%

    def test_decimal_bunga(self):
        """Bunga desimal 2.5%."""
        r = calculate_simulation(1_000_000, 2.5, 12, 0)
        assert r["total_bunga"] == 300_000  # 1jt × 2.5% × 12


class TestSimulasiWarnings:
    """Test warning tiers."""

    def test_warning_at_120_percent(self):
        """Bunga efektif 120% → warning predatory."""
        r = calculate_simulation(1_000_000, 10, 12, 0)
        # bunga_efektif = (1.2jt / 1jt) × 1 × 100 = 120%
        assert r["bunga_efektif_tahunan"] == 120.0
        assert r["warning"] is not None
        assert "120" in r["warning"]
        assert "predatory" in r["tip"].lower() or "100" in r["tip"]

    def test_warning_at_240_percent(self):
        """Bunga efektif 240% → strong warning."""
        r = calculate_simulation(1_000_000, 20, 12, 0)
        assert r["bunga_efektif_tahunan"] == 240.0
        assert r["warning"] is not None
        assert "20" in r["warning"]  # 20x lipat

    def test_no_warning_at_15_percent(self):
        """Bunga efektif 15% → no warning."""
        # bunga_pct × tenor = 15 → effective 15% (tenor 12)
        # 15/12 × 12 = 15, wait: (bunga × tenor / nominal) × (12/tenor) × 100
        # = (bunga/100) × 12 × 100 = bunga × 12
        # Hmm, that means for tenor 12, effective = bunga × 12
        # So bunga 1.5% → effective 18%
        # Bunga 1.25% → effective 15%
        r = calculate_simulation(1_000_000, 1.25, 12, 0)
        assert r["bunga_efektif_tahunan"] == 15.0
        assert r["warning"] is None  # 15% is below 18% threshold

    def test_warning_threshold_36_percent(self):
        """Boundary: 37% → warning, 35% → no warning (threshold is > 36 strict)."""
        r_37 = calculate_simulation(1_000_000, 3.083, 12, 0)  # ~37%
        r_35 = calculate_simulation(1_000_000, 2.916, 12, 0)  # ~35%
        assert r_37["bunga_efektif_tahunan"] > 36
        assert r_37["warning"] is not None
        assert r_35["bunga_efektif_tahunan"] < 36
        assert r_35["warning"] is None


class TestSimulasiInputValidation:
    """Test validasi input."""

    def test_negative_nominal_rejected(self):
        r = calculate_simulation(-100, 10, 6, 0)
        assert r["valid"] is False
        assert any("nominal" in e for e in r["errors"])

    def test_negative_bunga_rejected(self):
        r = calculate_simulation(1_000_000, -5, 6, 0)
        assert r["valid"] is False

    def test_zero_tenor_rejected(self):
        r = calculate_simulation(1_000_000, 10, 0, 0)
        assert r["valid"] is False
        assert any("tenor" in e for e in r["errors"])

    def test_negative_admin_rejected(self):
        r = calculate_simulation(1_000_000, 10, 6, -50_000)
        assert r["valid"] is False

    def test_none_values_rejected(self):
        r = calculate_simulation(None, 10, 6, 0)
        assert r["valid"] is False

    def test_valid_response_has_no_errors_key(self):
        r = calculate_simulation(1_000_000, 10, 6, 0)
        assert r["valid"] is True
        assert "errors" not in r
