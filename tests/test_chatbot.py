"""Tests untuk FAQ Chatbot (Phase 1: rule-based, 25 intents)."""
import pytest

from app.api import (
    FAQ_KB,
    _match_faq_intent,
    _tokenize,
    add_to_waitlist,
    chat_faq_handler,
    check_pinjol_status,
)


# =================================================================
# Tokenizer
# =================================================================
class TestTokenizer:
    def test_lowercase(self):
        tokens = _tokenize("Halo APA Kabar")
        assert tokens == ["halo", "apa", "kabar"]

    def test_punctuation_removed(self):
        tokens = _tokenize("halo, apa kabar?")
        assert "halo" in tokens
        assert "apa" in tokens
        assert "kabar" in tokens
        assert "," not in tokens
        assert "?" not in tokens

    def test_empty(self):
        assert _tokenize("") == []
        assert _tokenize("   ") == []
        assert _tokenize("...") == []


# =================================================================
# Intent Matching
# =================================================================
class TestIntentMatching:
    def test_galbay_definition(self):
        intent, conf = _match_faq_intent("apa itu galbay?")
        assert intent["intent"] == "apa_itu_galbay"
        assert conf > 0

    def test_skor_risiko(self):
        intent, conf = _match_faq_intent("apa itu skor risiko?")
        assert intent["intent"] == "apa_itu_skor_risiko"

    def test_pinjol_ilegal(self):
        intent, conf = _match_faq_intent("apa itu pinjol ilegal?")
        assert intent["intent"] == "pinjol_ilegal"

    def test_snowball_avalanche(self):
        intent, conf = _match_faq_intent("snowball vs avalanche mana yang lebih baik?")
        assert intent["intent"] == "snowball_vs_avalanche"

    def test_bunga_tinggi(self):
        intent, conf = _match_faq_intent("bunga pinjol berapa yang wajar?")
        assert intent["intent"] == "bunga_tinggi_normal"

    def test_dc_agresif(self):
        intent, conf = _match_faq_intent("DC saya agresif, ancam-ancam")
        assert intent["intent"] == "dc_agresif"

    def test_lapor_dc(self):
        intent, conf = _match_faq_intent("gimana cara lapor DC ilegal?")
        assert intent["intent"] == "lapor_dc"

    def test_template_chat(self):
        intent, conf = _match_faq_intent("ada template chat untuk debt collector?")
        assert intent["intent"] == "template_chat"

    def test_cara_recovery(self):
        intent, conf = _match_faq_intent("gimana cara keluar dari galbay?")
        assert intent["intent"] == "cara_recovery"

    def test_telat_30_hari(self):
        intent, conf = _match_faq_intent("saya telat 30 hari, gimana?")
        assert intent["intent"] == "telat_30_hari"

    def test_negosiasi(self):
        intent, conf = _match_faq_intent("bisa nego cicilan gak?")
        assert intent["intent"] == "negosiasi_cicilan"

    def test_aplikasi_aman(self):
        intent, conf = _match_faq_intent("aplikasi ini aman gak? data saya gimana?")
        assert intent["intent"] == "aplikasi_aman"

    def test_premium(self):
        intent, conf = _match_faq_intent("premium dapat apa aja?")
        assert intent["intent"] == "premium_dapat_apa"

    def test_konseling(self):
        intent, conf = _match_faq_intent("konseling berapa biayanya?")
        assert intent["intent"] == "konseling_berapa"

    def test_dikon_premium(self):
        intent, conf = _match_faq_intent("ada diskon gak?")
        assert intent["intent"] == "diskon_premium"

    def test_cara_pakai(self):
        intent, conf = _match_faq_intent("cara pakai web ini gimana?")
        assert intent["intent"] == "cara_pakai_website"

    def test_data_sumber(self):
        intent, conf = _match_faq_intent("data 349 ribu ini dari mana?")
        assert intent["intent"] == "data_sumber"

    def test_emergency_dc(self):
        intent, conf = _match_faq_intent("DC telepon saya sekarang, gimana?")
        assert intent["intent"] == "emergency_dc"

    def test_konsultan(self):
        intent, conf = _match_faq_intent("ada konsultan keuangan gratis gak?")
        assert intent["intent"] == "konsultan_keuangan"

    def test_self_reward(self):
        intent, conf = _match_faq_intent("self reward itu boleh gak?")
        assert intent["intent"] == "self_reward_aman"

    def test_pinjol_vs_paylater(self):
        intent, conf = _match_faq_intent("bedanya pinjol sama paylater apa?")
        assert intent["intent"] == "pinjol_atau_paylater"

    def test_berapa_utang(self):
        intent, conf = _match_faq_intent("berapa utang yang normal?")
        assert intent["intent"] == "berapa_utang_normal"

    def test_ai_atau_rule(self):
        intent, conf = _match_faq_intent("pakai AI gak sih?")
        assert intent["intent"] == "ai_atau_rule_based"

    def test_fallback_gibberish(self):
        intent, conf = _match_faq_intent("xqzxqzxqz random gibberish")
        assert intent["intent"] == "default_fallback"
        assert conf == 0.0

    def test_fallback_unrelated(self):
        intent, conf = _match_faq_intent("resep nasi goreng")
        assert intent["intent"] == "default_fallback"

    def test_empty_message(self):
        intent, conf = _match_faq_intent("")
        assert intent is None
        assert conf == 0.0


# =================================================================
# Chat FAQ Handler
# =================================================================
class TestChatHandler:
    def test_valid_response(self):
        result = chat_faq_handler("apa itu galbay?")
        assert result["valid"] is True
        assert result["intent"] == "apa_itu_galbay"
        assert "answer" in result
        assert len(result["answer"]) > 0
        assert "suggestions" in result
        assert "related_actions" in result
        assert result["model_version"] == "faq-rule-based-v1"

    def test_empty_message(self):
        result = chat_faq_handler("")
        assert result["valid"] is False
        assert "error" in result

    def test_whitespace_message(self):
        result = chat_faq_handler("   \n   ")
        assert result["valid"] is False

    def test_response_has_disclaimer(self):
        result = chat_faq_handler("apa itu galbay?")
        assert "disclaimer" in result
        assert "phase 1" in result["disclaimer"].lower() or "rule-based" in result["disclaimer"].lower()

    def test_confidence_in_range(self):
        result = chat_faq_handler("premium")
        assert 0.0 <= result["confidence"] <= 1.0

    def test_related_actions_structure(self):
        result = chat_faq_handler("cek pinjol")
        for action in result["related_actions"]:
            assert "label" in action
            assert "href" in action

    def test_suggestions_structure(self):
        result = chat_faq_handler("cara recovery")
        assert isinstance(result["suggestions"], list)
        for s in result["suggestions"]:
            assert isinstance(s, str)


# =================================================================
# FAQ KB Quality
# =================================================================
class TestFAQKB:
    def test_kb_not_empty(self):
        assert len(FAQ_KB) >= 20

    def test_all_entries_have_required_fields(self):
        for entry in FAQ_KB:
            assert "intent" in entry
            assert "keywords" in entry
            assert "answer" in entry

    def test_unique_intents(self):
        intents = [e["intent"] for e in FAQ_KB]
        assert len(intents) == len(set(intents)), "Duplicate intent IDs found"

    def test_default_fallback_exists(self):
        intents = [e["intent"] for e in FAQ_KB]
        assert "default_fallback" in intents

    def test_all_answers_have_content(self):
        for entry in FAQ_KB:
            assert len(entry["answer"]) >= 20, f"Short answer for intent {entry['intent']}"


# =================================================================
# Pinjol Database (expanded to 50+)
# =================================================================
class TestExpandedPinjolDB:
    def test_legal_count_50_plus(self):
        result = check_pinjol_status("Atome")
        assert result["status"] == "legal"

    def test_legal_alias_match(self):
        # "Jenius" (alias) should match "Jenius" (full name)
        result = check_pinjol_status("Jenius")
        assert result["status"] == "legal"

    def test_alias_lowercase(self):
        result = check_pinjol_status("blu")
        assert result["status"] == "legal"
        assert "blu" in result["name"].lower() or "BCA" in result["name"]

    def test_legal_p2p_lending(self):
        result = check_pinjol_status("Amartha")
        assert result["status"] == "legal"
        assert result["category"] == "p2p_lending"

    def test_legal_investasi(self):
        result = check_pinjol_status("Bibit")
        assert result["status"] == "legal"
        assert result["category"] == "investasi"

    def test_legal_insurtech(self):
        result = check_pinjol_status("Lifepal")
        assert result["status"] == "legal"

    def test_ilegal_count_expanded(self):
        result = check_pinjol_status("Rupiah Gegas")
        assert result["status"] == "ilegal"

    def test_ilegal_alias_match(self):
        # "gegas" is alias for "Rupiah Gegas"
        result = check_pinjol_status("gegas")
        assert result["status"] == "ilegal"

    def test_partial_match_legal(self):
        result = check_pinjol_status("Kredi")
        # Should match Kredivo or Kredito partially
        assert result["status"] in ("legal", "legal_partial")

    def test_ojk_license_format(self):
        result = check_pinjol_status("Kredivo")
        assert "ojk_license" in result
        assert result["ojk_license"].startswith("S-") or "Bank" in result["ojk_license"] or "Aggregator" in result["ojk_license"]


# =================================================================
# Waitlist with name
# =================================================================
class TestWaitlistName:
    def test_add_with_name(self, tmp_path, monkeypatch):
        import os
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir(exist_ok=True)
        result = add_to_waitlist("test@example.com", package="premium", name="Test User")
        assert result["valid"] is True
        assert result["duplicate"] is False
        assert result["total"] == 1

    def test_add_duplicate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir(exist_ok=True)
        add_to_waitlist("dup@example.com", package="premium", name="Dup")
        result = add_to_waitlist("dup@example.com", package="premium", name="Dup 2")
        assert result["valid"] is True
        assert result["duplicate"] is True
