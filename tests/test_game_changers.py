"""Tests untuk 4 fitur game-changer: Pinjol Checker, Debt Planner, DC Kit, Recovery Roadmap."""
import pytest
from app.api import (
    check_pinjol_status,
    calculate_debt_planner,
    get_dc_templates,
    get_dc_template,
    generate_recovery_roadmap,
    DC_TEMPLATES,
)


# =================================================================
# Pinjol Blacklist Checker
# =================================================================
class TestCheckPinjolStatus:
    """Test untuk cek status OJK pinjol."""

    def test_empty_name_invalid(self):
        r = check_pinjol_status("")
        assert r["valid"] is False
        assert "error" in r

    def test_whitespace_name_invalid(self):
        r = check_pinjol_status("   ")
        assert r["valid"] is False

    def test_legal_exact_match(self):
        """Cek app yang ada di database legal (exact match)."""
        r = check_pinjol_status("Kredivo")
        assert r["valid"] is True
        assert r["found"] is True
        assert r["status"] == "legal"
        assert r["status_label"] == "TERDAFTAR OJK"
        assert "OJK" in r["message"] or "legal" in r["message"].lower()
        assert isinstance(r["recommendations"], list)
        assert len(r["recommendations"]) >= 1

    def test_legal_case_insensitive(self):
        """Case-insensitive search."""
        r1 = check_pinjol_status("kredivo")
        r2 = check_pinjol_status("KREDIVO")
        r3 = check_pinjol_status("Kredivo")
        for r in [r1, r2, r3]:
            assert r["found"] is True
            assert r["status"] == "legal"

    def test_legal_partial_match(self):
        """Partial match untuk nama mirip."""
        r = check_pinjol_status("blu")
        # "blu by BCA Digital" — should partial match
        assert r["valid"] is True
        assert r["found"] is True
        assert r["status"] in ("legal_partial", "legal")
        if r["status"] == "legal_partial":
            assert "Mungkin" in r["message"] or "Periksa" in r["message"]

    def test_ilegal_sample(self):
        """Cek app di sample ilegal."""
        r = check_pinjol_status("Pinjol Ilegal A")
        assert r["valid"] is True
        assert r["found"] is True
        assert r["status"] == "ilegal"
        assert "JANGAN" in r["recommendations"][0] or "tidak" in r["message"].lower()

    def test_unknown_app(self):
        """App yang tidak ada di database."""
        r = check_pinjol_status("AppTidakAdaXYZ123")
        assert r["valid"] is True
        assert r["found"] is False
        assert r["status"] == "unknown"
        assert "tidak ditemukan" in r["message"].lower() or "tidak dikenal" in r["status_label"].lower()

    def test_returns_recommendations_for_legal(self):
        r = check_pinjol_status("OVO")
        assert isinstance(r["recommendations"], list)
        assert all(isinstance(rec, str) for rec in r["recommendations"])

    def test_returns_ojk_license(self):
        """Legal app harus return ojk_license."""
        r = check_pinjol_status("DANA")
        assert "ojk_license" in r
        assert r["ojk_license"] != ""

    def test_disclaimer_present(self):
        """Semua response harus ada disclaimer."""
        for query in ["Kredivo", "AppTidakAda", "Pinjol Ilegal A"]:
            r = check_pinjol_status(query)
            assert "disclaimer" in r


# =================================================================
# Debt Snowball / Avalanche Planner
# =================================================================
class TestCalculateDebtPlanner:
    """Test untuk Debt Snowball/Avalanche Planner."""

    def test_empty_debts_invalid(self):
        r = calculate_debt_planner([])
        assert r["valid"] is False
        assert "error" in r

    def test_basic_simulation(self):
        debts = [
            {"name": "Pinjol A", "balance": 1_000_000, "bunga_pct": 10, "min_payment": 100_000},
            {"name": "Pinjol B", "balance": 3_000_000, "bunga_pct": 5, "min_payment": 300_000},
        ]
        r = calculate_debt_planner(debts, extra_payment=200_000)
        assert r["valid"] is True
        assert "snowball" in r
        assert "avalanche" in r
        assert r["total_debt"] == 4_000_000
        assert r["snowball"]["months_to_debt_free"] > 0
        assert r["avalanche"]["months_to_debt_free"] > 0

    def test_snowball_orders_by_smallest_first(self):
        debts = [
            {"name": "Big", "balance": 5_000_000, "bunga_pct": 5, "min_payment": 500_000},
            {"name": "Small", "balance": 1_000_000, "bunga_pct": 5, "min_payment": 100_000},
            {"name": "Medium", "balance": 3_000_000, "bunga_pct": 5, "min_payment": 300_000},
        ]
        r = calculate_debt_planner(debts)
        # Snowball: Small → Medium → Big
        assert r["snowball"]["order"] == ["Small", "Medium", "Big"]

    def test_avalanche_orders_by_highest_rate_first(self):
        debts = [
            {"name": "Low Rate", "balance": 1_000_000, "bunga_pct": 3, "min_payment": 100_000},
            {"name": "High Rate", "balance": 2_000_000, "bunga_pct": 15, "min_payment": 200_000},
            {"name": "Medium Rate", "balance": 3_000_000, "bunga_pct": 8, "min_payment": 300_000},
        ]
        r = calculate_debt_planner(debts)
        # Avalanche: High Rate → Medium Rate → Low Rate
        assert r["avalanche"]["order"][0] == "High Rate"
        assert r["avalanche"]["order"][1] == "Medium Rate"
        assert r["avalanche"]["order"][2] == "Low Rate"

    def test_avalanche_saves_more_interest(self):
        """Avalanche biasanya lebih hemat bunga (pada rate beda)."""
        debts = [
            {"name": "Low", "balance": 2_000_000, "bunga_pct": 2, "min_payment": 200_000},
            {"name": "High", "balance": 2_000_000, "bunga_pct": 20, "min_payment": 200_000},
        ]
        r = calculate_debt_planner(debts, extra_payment=500_000)
        # Avalanche hemat bunga (bayar high rate dulu)
        assert r["avalanche"]["total_interest_paid"] < r["snowball"]["total_interest_paid"]
        assert r["recommendation"] == "avalanche"

    def test_extra_payment_accelerates_payoff(self):
        debts = [
            {"name": "A", "balance": 2_000_000, "bunga_pct": 10, "min_payment": 100_000},
        ]
        r1 = calculate_debt_planner(debts, extra_payment=0)
        r2 = calculate_debt_planner(debts, extra_payment=500_000)
        # Extra payment harus percepat pelunasan
        assert r2["snowball"]["months_to_debt_free"] < r1["snowball"]["months_to_debt_free"]

    def test_invalid_format_filtered(self):
        """Invalid data di-debuang, tidak crash."""
        debts = [
            {"name": "Valid", "balance": 1000, "bunga_pct": 5, "min_payment": 100},
            {"name": "Invalid", "balance": "abc", "bunga_pct": 5, "min_payment": 100},
        ]
        r = calculate_debt_planner(debts)
        assert r["valid"] is True
        # Hanya 1 utang valid
        assert len(r["debts_input"]) == 1

    def test_comparison_contains_both_strategies(self):
        debts = [{"name": "A", "balance": 1_000_000, "bunga_pct": 5, "min_payment": 100_000}]
        r = calculate_debt_planner(debts)
        assert r["valid"] is True
        assert r["snowball"]["strategy_label"]
        assert r["avalanche"]["strategy_label"]
        assert "Snowball" in r["snowball"]["strategy_label"]
        assert "Avalanche" in r["avalanche"]["strategy_label"]

    def test_paid_off_schedule_has_all_debts(self):
        debts = [
            {"name": "A", "balance": 1_000_000, "bunga_pct": 5, "min_payment": 100_000},
            {"name": "B", "balance": 2_000_000, "bunga_pct": 5, "min_payment": 200_000},
        ]
        r = calculate_debt_planner(debts, extra_payment=500_000)
        for strategy in ["snowball", "avalanche"]:
            assert "A" in r[strategy]["paid_off_schedule"]
            assert "B" in r[strategy]["paid_off_schedule"]


# =================================================================
# DC Survival Kit
# =================================================================
class TestDCTemplates:
    """Test untuk DC Survival Kit."""

    def test_get_all_templates(self):
        r = get_dc_templates()
        assert r["valid"] is True
        assert "templates" in r
        assert len(r["templates"]) == 5
        assert "general_rights" in r
        assert "emergency_contacts" in r
        assert "disclaimer" in r

    def test_all_templates_have_required_fields(self):
        r = get_dc_templates()
        for t in r["templates"]:
            assert "id" in t
            assert "title" in t
            assert "scenario" in t
            assert "message" in t
            assert "hak_kamu" in t
            assert "landasan_hukum" in t
            assert isinstance(t["hak_kamu"], list)
            assert len(t["hak_kamu"]) >= 1

    def test_get_template_by_id(self):
        r = get_dc_template("tidak_bisa_hari_ini")
        assert r["valid"] is True
        assert r["template"]["id"] == "tidak_bisa_hari_ini"
        assert r["template"]["title"]

    def test_get_template_invalid_id(self):
        r = get_dc_template("nonexistent")
        assert r["valid"] is False
        assert "error" in r

    def test_templates_have_specific_ids(self):
        r = get_dc_templates()
        ids = [t["id"] for t in r["templates"]]
        assert "tidak_bisa_hari_ini" in ids
        assert "restrukturisasi" in ids
        assert "tolak_penagihan_agresif" in ids
        assert "lapor_dc_ilegal" in ids
        assert "konfirmasi_utang" in ids

    def test_messages_reference_legal_basis(self):
        """Setiap template harus ada landasan hukum (UU/POJK/Permenkominfo)."""
        r = get_dc_templates()
        for t in r["templates"]:
            assert t["landasan_hukum"], f"Template {t['id']} missing landasan_hukum"

    def test_emergency_contacts_include_ojk(self):
        r = get_dc_templates()
        contact_names = [c["name"] for c in r["emergency_contacts"]]
        assert any("OJK" in name for name in contact_names)

    def test_general_rights_list_nonempty(self):
        r = get_dc_templates()
        assert len(r["general_rights"]) >= 5


# =================================================================
# Galbay Recovery Roadmap
# =================================================================
class TestRecoveryRoadmap:
    """Test untuk Galbay Recovery Roadmap."""

    def test_basic_input(self):
        r = generate_recovery_roadmap({
            "total_utang": 5_000_000,
            "income_bulanan": 3_000_000,
            "sudah_dc": False,
            "hari_telat": 0,
        })
        assert r["valid"] is True
        assert r["severity"] in ("sedang", "tinggi", "kritis")
        assert "roadmap" in r
        assert "minggu_1_2" in r["roadmap"]
        assert "minggu_3_4" in r["roadmap"]
        assert "bulan_3" in r["roadmap"]

    def test_critical_severity(self):
        """Telat > 30 hari ATAU debt-to-income > 3 → kritis."""
        r = generate_recovery_roadmap({
            "total_utang": 50_000_000,
            "income_bulanan": 3_000_000,  # debt/income = 16.67 (very high)
            "sudah_dc": True,
            "hari_telat": 60,
        })
        assert r["valid"] is True
        assert r["severity"] == "kritis"
        assert r["severity_label"] == "KRITIS"
        # Critical roadmap harus lebih panjang (15+ items minggu 1-2)
        assert len(r["roadmap"]["minggu_1_2"]) >= 10

    def test_high_severity(self):
        """Telat 7-30 hari ATAU debt-to-income 1.5-3 → tinggi."""
        r = generate_recovery_roadmap({
            "total_utang": 8_000_000,
            "income_bulanan": 4_000_000,  # debt/income = 2.0
            "sudah_dc": False,
            "hari_telat": 15,
        })
        assert r["valid"] is True
        assert r["severity"] == "tinggi"

    def test_moderate_severity(self):
        """Telat < 7 hari, debt-to-income < 1.5 → sedang."""
        r = generate_recovery_roadmap({
            "total_utang": 2_000_000,
            "income_bulanan": 3_000_000,  # debt/income = 0.67
            "sudah_dc": False,
            "hari_telat": 0,
        })
        assert r["valid"] is True
        assert r["severity"] == "sedang"

    def test_invalid_income(self):
        r = generate_recovery_roadmap({"total_utang": 1000, "income_bulanan": 0})
        assert r["valid"] is False

    def test_invalid_total_utang(self):
        r = generate_recovery_roadmap({"total_utang": -100, "income_bulanan": 3000})
        assert r["valid"] is False

    def test_string_input_converted(self):
        """String 'true'/'false' untuk sudah_dc dikonversi ke bool."""
        r = generate_recovery_roadmap({
            "total_utang": "5000000",
            "income_bulanan": "3000000",
            "sudah_dc": "true",
            "hari_telat": "15",
        })
        assert r["valid"] is True

    def test_roadmap_includes_success_metrics(self):
        r = generate_recovery_roadmap({
            "total_utang": 3_000_000, "income_bulanan": 3_000_000,
            "sudah_dc": False, "hari_telat": 5
        })
        assert "success_metrics" in r
        assert "target_bulan_1" in r["success_metrics"]
        assert "target_bulan_2" in r["success_metrics"]
        assert "target_bulan_3" in r["success_metrics"]

    def test_every_roadmap_has_disclaimer(self):
        r = generate_recovery_roadmap({
            "total_utang": 3_000_000, "income_bulanan": 3_000_000,
            "sudah_dc": False, "hari_telat": 5
        })
        assert "disclaimer" in r

    def test_conditions_echoed_back(self):
        r = generate_recovery_roadmap({
            "total_utang": 5_000_000, "income_bulanan": 3_000_000,
            "sudah_dc": True, "hari_telat": 10
        })
        assert r["conditions"]["total_utang"] == 5_000_000
        assert r["conditions"]["income_bulanan"] == 3_000_000
        assert r["conditions"]["sudah_dc"] is True
        assert r["conditions"]["hari_telat"] == 10
        assert "debt_to_income_ratio" in r["conditions"]


# =================================================================
# API Integration untuk 4 fitur baru
# =================================================================
class TestGameChangerAPIIntegration:
    """Integration tests untuk 4 endpoint API baru."""

    def test_api_check_pinjol(self, client):
        r = client.post("/api/check-pinjol", json={"app_name": "Kredivo"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is True
        assert data["status"] == "legal"

    def test_api_check_pinjol_unknown(self, client):
        r = client.post("/api/check-pinjol", json={"app_name": "AppTidakAda"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["found"] is False

    def test_api_debt_planner(self, client):
        r = client.post("/api/debt-planner", json={
            "debts": [
                {"name": "A", "balance": 1000000, "bunga_pct": 10, "min_payment": 100000},
                {"name": "B", "balance": 2000000, "bunga_pct": 5, "min_payment": 200000},
            ],
            "extra_payment": 200000
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True
        assert "snowball" in data
        assert "avalanche" in data

    def test_api_debt_planner_empty(self, client):
        r = client.post("/api/debt-planner", json={"debts": []})
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is False

    def test_api_dc_templates(self, client):
        r = client.get("/api/dc-templates")
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True
        assert len(data["templates"]) == 5

    def test_api_dc_template_by_id(self, client):
        r = client.get("/api/dc-templates/tidak_bisa_hari_ini")
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True
        assert data["template"]["id"] == "tidak_bisa_hari_ini"

    def test_api_dc_template_invalid(self, client):
        r = client.get("/api/dc-templates/nonexistent")
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is False

    def test_api_recovery_roadmap(self, client):
        r = client.post("/api/recovery-roadmap", json={
            "total_utang": 5000000,
            "income_bulanan": 3000000,
            "sudah_dc": False,
            "hari_telat": 5
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["valid"] is True
        assert "roadmap" in data

    def test_api_recovery_roadmap_critical(self, client):
        r = client.post("/api/recovery-roadmap", json={
            "total_utang": 50000000,
            "income_bulanan": 3000000,
            "sudah_dc": True,
            "hari_telat": 60
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["severity"] == "kritis"
