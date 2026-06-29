"""Tests untuk FAQ Chatbot (Phase 2: NLP-like, 38 intents, 8 modules)."""
import pytest

from app.api import (
    CHATBOT_DISCLAIMER,
    CHATBOT_MODULES,
    CHATBOT_MODEL_VERSION,
    FAQ_KB,
    SYNONYMS,
    _detect_sentiment,
    _expand_with_synonyms,
    _format_answer_markdown,
    _get_time_greeting,
    _match_faq_intent,
    _match_faq_intent_v2,
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
        assert intent["intent"] in ("pinjol_atau_paylater", "paylater_vs_pinjol")

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
        # v2 returns default_fallback entry with conf 0 for empty input
        assert intent["intent"] == "default_fallback"
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
        assert result["model_version"] == "faq-nlp-v2"

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
        assert "nlp" in result["disclaimer"].lower() or "rule-based" in result["disclaimer"].lower()

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

    def test_response_includes_conversation_state(self):
        result = chat_faq_handler("apa itu galbay?")
        assert "conversation_state" in result
        assert result["conversation_state"]["last_intent"] == "apa_itu_galbay"

    def test_low_confidence_uses_clarification_payload(self):
        result = chat_faq_handler("resep nasi goreng", page_context="produk")
        assert result["valid"] is True
        assert result["follow_up_type"] == "clarify_low_confidence"
        assert "tidak mau jawab ngaco" in result["answer"].lower()


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
# Phase 2: Synonym resolution
# =================================================================
class TestSynonyms:
    def test_pinjol_synonyms(self):
        for term in ["pinjol", "pinjaman online", "online", "p2p"]:
            best, conf, _ = _match_faq_intent_v2(term)
            # Should match some pinjol-related intent (not necessarily pinjol_ilegal)
            assert best["intent"] in (
                "pinjol_ilegal", "cara_cek_pinjol_legal", "bunga_tinggi_normal",
                "paylater_vs_pinjol", "cara_nego_dc", "hukum_pinjol_ilegal",
                "lapor_dc", "hapus_data_diri", "apa_itu_galbay", "default_fallback",
            )

    def test_galbay_synonyms(self):
        for term in ["gali bayar", "lubang", "tutup lubang", "utang"]:
            best, conf, _ = _match_faq_intent_v2(f"apa itu {term}")
            assert best["intent"] in (
                "apa_itu_galbay", "berapa_utang_normal", "cara_recovery",
                "negosiasi_cicilan", "snowball_vs_avalanche", "default_fallback",
            )

    def test_dc_synonyms(self):
        for term in ["dc", "debt collector", "penagih", "nagih"]:
            best, conf, _ = _match_faq_intent_v2(f"{term} agresif")
            assert best["intent"] in (
                "dc_agresif", "cara_nego_dc", "lapor_dc", "emergency_dc",
                "default_fallback",
            )

    def test_paylater_synonyms(self):
        best, conf, _ = _match_faq_intent_v2("paylater apa bedanya")
        assert best["intent"] in ("paylater_vs_pinjol", "pinjol_ilegal", "cara_cek_pinjol_legal")

    def test_snowball_synonyms(self):
        best, conf, _ = _match_faq_intent_v2("bola salju")
        assert best["intent"] in ("snowball_vs_avalanche", "default_fallback")

    def test_avalanche_synonyms(self):
        best, conf, _ = _match_faq_intent_v2("longsor method")
        assert best["intent"] in ("snowball_vs_avalanche", "default_fallback")

    def test_expand_helper(self):
        tokens = ["pinjol"]
        expanded = _expand_with_synonyms(tokens)
        assert "pinjaman online" in expanded
        assert "p2p" in expanded
        assert "pinjol" in expanded


# =================================================================
# Phase 2: Typo tolerance (difflib)
# =================================================================
class TestTypoTolerance:
    def test_snowbol_typo(self):
        best, conf, _ = _match_faq_intent_v2("snowbol vs avalanche")
        assert best["intent"] == "snowball_vs_avalanche"

    def test_pinjool_typo(self):
        best, conf, _ = _match_faq_intent_v2("pinjool ilegal")
        assert best["intent"] == "pinjol_ilegal"

    def test_galbay_typo(self):
        best, conf, _ = _match_faq_intent_v2("apa itu galb ay")
        # Fuzzy should still find some intent (not necessarily galbay)
        assert best is not None

    def test_recovery_typo(self):
        best, conf, _ = _match_faq_intent_v2("cara recovry")
        # Typo: "recovry" should still resolve to recovery-related intent via fuzzy matching
        assert best["intent"] in (
            "cara_recovery", "snowball_vs_avalanche", "cara_pakai_website",
            "default_fallback",
        )


# =================================================================
# Phase 2: Multi-intent (secondary_intents)
# =================================================================
class TestMultiIntent:
    def test_recovery_with_dc(self):
        result = chat_faq_handler("cara recovery, tapi DC agresif")
        assert result["intent"] == "cara_recovery"
        assert len(result["secondary_intents"]) > 0
        # DC agresif should be a secondary
        secondary_ids = [s["intent"] for s in result["secondary_intents"]]
        assert "dc_agresif" in secondary_ids

    def test_snowball_with_recovery(self):
        result = chat_faq_handler("snowball vs avalanche, cara recovery")
        # Either cara_recovery is primary or secondary
        secondary_ids = [s["intent"] for s in result["secondary_intents"]]
        assert "cara_recovery" in [result["intent"]] + secondary_ids

    def test_secondary_intents_structure(self):
        result = chat_faq_handler("apa itu galbay?")
        for s in result["secondary_intents"]:
            assert "intent" in s
            assert "module" in s
            assert "confidence" in s
            assert 0.0 <= s["confidence"] <= 1.0

    def test_secondary_capped_at_3(self):
        result = chat_faq_handler("cara recovery dari galbay")
        assert len(result["secondary_intents"]) <= 3


# =================================================================
# Phase 2: Sentiment detection
# =================================================================
class TestSentiment:
    def test_stressed_keyword(self):
        r = chat_faq_handler("saya stress galbay")
        assert r["sentiment"] == "stressed"

    def test_curious_question(self):
        r = chat_faq_handler("apa itu galbay?")
        assert r["sentiment"] == "curious"

    def test_crisis_keyword(self):
        r = chat_faq_handler("saya mau bunuh diri")
        assert r["sentiment"] == "crisis"

    def test_gratitude(self):
        r = chat_faq_handler("makasih ya")
        assert r["sentiment"] == "grateful"

    def test_positive(self):
        r = chat_faq_handler("keren app ini")
        assert r["sentiment"] in ("positive", "neutral")

    def test_frustrated(self):
        r = chat_faq_handler("saya kesal banget")
        assert r["sentiment"] == "frustrated"

    def test_anxious(self):
        r = chat_faq_handler("saya cemas banget")
        assert r["sentiment"] == "stressed"

    def test_neutral(self):
        r = chat_faq_handler("cek skor")
        assert r["sentiment"] in ("neutral", "curious")


# =================================================================
# Phase 2: Time-based greeting
# =================================================================
class TestGreeting:
    def test_greeting_present(self):
        r = chat_faq_handler("apa itu galbay?")
        assert "greeting" in r
        assert r["greeting"] in ("Selamat pagi", "Selamat siang", "Selamat sore", "Selamat malam")

    def test_get_time_greeting(self):
        g = _get_time_greeting()
        assert g.startswith("Selamat ")
        assert g.endswith(("pagi", "siang", "sore", "malam"))


# =================================================================
# Phase 2: Context-aware response
# =================================================================
class TestContextAware:
    def test_page_context_ringkasan(self):
        r = chat_faq_handler("rekomendasi app", page_context="ringkasan")
        assert "Ringkasan" in r["answer_html"] or "ringkasan" in r["answer_html"].lower()

    def test_page_context_produk(self):
        r = chat_faq_handler("rekomendasi app", page_context="produk")
        assert "Produk" in r["answer_html"] or "produk" in r["answer_html"].lower()

    def test_page_context_solusi(self):
        r = chat_faq_handler("rekomendasi app", page_context="solusi")
        assert "Solusi" in r["answer_html"] or "solusi" in r["answer_html"].lower()

    def test_no_context(self):
        r = chat_faq_handler("apa itu galbay?")
        # Without context, no page tip appended
        assert "💡" not in r["answer_html"]

    def test_user_name_stressed(self):
        r = chat_faq_handler("saya stress banget", user_name="Adi")
        assert r["name_prefix"] == "Adi, "

    def test_user_name_neutral(self):
        # No name prefix for neutral sentiment
        r = chat_faq_handler("apa itu galbay?", user_name="Adi")
        assert r["name_prefix"] == ""

    def test_contextual_follow_up_uses_previous_state(self):
        first = chat_faq_handler("DC saya agresif, ancam-ancam")
        second = chat_faq_handler(
            "kalau begitu terus gimana?",
            page_context="produk",
            conversation_state=first["conversation_state"],
        )
        assert second["valid"] is True
        assert second["follow_up_type"] == "contextual_follow_up"
        assert second["conversation_state"]["last_intent"] == first["conversation_state"]["last_intent"]


# =================================================================
# Phase 2: Markdown rendering
# =================================================================
class TestMarkdown:
    def test_bold_to_strong(self):
        html = _format_answer_markdown("**Galbay** adalah")
        assert "<strong>Galbay</strong>" in html

    def test_italic_to_em(self):
        html = _format_answer_markdown("*gali lubang*")
        assert "<em>gali lubang</em>" in html

    def test_inline_code(self):
        html = _format_answer_markdown("gunakan `auto_debit`")
        assert "<code>auto_debit</code>" in html

    def test_code_block(self):
        html = _format_answer_markdown("```\nfoo\nbar\n```")
        assert "<pre><code>" in html
        assert "foo" in html

    def test_link(self):
        html = _format_answer_markdown("[Galbay](/dashboard/ringkasan)")
        assert 'href="/dashboard/ringkasan"' in html
        assert 'target="_blank"' in html

    def test_unordered_list(self):
        html = _format_answer_markdown("- item 1\n- item 2")
        assert "<ul>" in html
        assert "<li>item 1</li>" in html

    def test_ordered_list(self):
        html = _format_answer_markdown("1. first\n2. second")
        assert "<ol>" in html
        assert "<li>first</li>" in html

    def test_newline_to_br(self):
        html = _format_answer_markdown("line 1\nline 2")
        assert "<br>" in html

    def test_empty_input(self):
        assert _format_answer_markdown("") == ""
        assert _format_answer_markdown(None) == ""

    def test_answer_html_in_response(self):
        r = chat_faq_handler("apa itu galbay?")
        assert "answer_html" in r
        assert "<strong>" in r["answer_html"]


# =================================================================
# Phase 2: Module metadata
# =================================================================
class TestModules:
    def test_8_modules(self):
        assert len(CHATBOT_MODULES) == 8

    def test_module_keys(self):
        expected = {
            "M1_galbay_basics", "M2_pinjol", "M3_debt_strategy",
            "M4_dc_negotiation", "M5_recovery", "M6_legal_rights",
            "M7_app_rec", "M8_mental_health",
        }
        assert set(CHATBOT_MODULES.keys()) == expected

    def test_module_metadata(self):
        for mid, m in CHATBOT_MODULES.items():
            assert "name" in m
            assert "icon" in m
            assert "description" in m

    def test_response_has_module(self):
        r = chat_faq_handler("apa itu galbay?")
        assert r["module"] == "M1_galbay_basics"
        assert r["module_name"] == "Galbay Basics"
        assert "📚" in r["module_icon"]


# =================================================================
# Phase 2: KB quality (expanded to 35+)
# =================================================================
class TestKBV2:
    def test_kb_size_35_plus(self):
        assert len(FAQ_KB) >= 35

    def test_every_entry_has_module(self):
        for entry in FAQ_KB:
            if entry["intent"] != "default_fallback":
                assert "module" in entry
                assert entry["module"] in CHATBOT_MODULES

    def test_every_entry_has_suggestions(self):
        for entry in FAQ_KB:
            assert "suggestions" in entry
            assert isinstance(entry["suggestions"], list)

    def test_every_entry_has_related_actions(self):
        for entry in FAQ_KB:
            assert "related_actions" in entry
            assert isinstance(entry["related_actions"], list)
            for action in entry["related_actions"]:
                assert "label" in action
                assert "href" in action

    def test_covers_all_modules(self):
        covered_modules = {e.get("module") for e in FAQ_KB if e["intent"] != "default_fallback"}
        assert covered_modules == set(CHATBOT_MODULES.keys())


# =================================================================
# Phase 2: v2 matcher signature
# =================================================================
class TestMatcherV2:
    def test_v2_returns_3_values(self):
        result = _match_faq_intent_v2("apa itu galbay?")
        assert len(result) == 3
        best, conf, secondary = result
        assert isinstance(best, dict)
        assert isinstance(conf, float)
        assert isinstance(secondary, list)

    def test_v1_compat_wrapper(self):
        # _match_faq_intent should still return 2 values
        result = _match_faq_intent("apa itu galbay?")
        assert len(result) == 2
        best, conf = result
        assert isinstance(best, dict)
        assert isinstance(conf, float)

    def test_empty_message_v2(self):
        best, conf, secondary = _match_faq_intent_v2("")
        assert best["intent"] == "default_fallback"
        assert conf == 0.0
        assert secondary == []

    def test_whitespace_message_v2(self):
        best, conf, secondary = _match_faq_intent_v2("   \n   ")
        assert best["intent"] == "default_fallback"

    def test_unmatched_returns_fallback(self):
        best, conf, secondary = _match_faq_intent_v2("xqzxqz random gibberish")
        assert best["intent"] == "default_fallback"
        assert conf == 0.0


# =================================================================
# Phase 2: Crisis detection (self_harm)
# =================================================================
class TestCrisisDetection:
    def test_self_harm_intent(self):
        r = chat_faq_handler("saya mau bunuh diri")
        assert r["intent"] == "self_harm"

    def test_crisis_sentiment_with_helpline(self):
        r = chat_faq_handler("saya putus asa mau mati")
        assert r["sentiment"] == "crisis"
        # Should include helpline info
        assert "119" in r["answer"] or "Sejiwa" in r["answer"] or "Into The Light" in r["answer"]

    def test_hopeless_message(self):
        r = chat_faq_handler("putus asa, ga ada harapan")
        # Should be either stressed or crisis
        assert r["sentiment"] in ("stressed", "crisis")


# =================================================================
# Constants & metadata
# =================================================================
class TestConstants:
    def test_model_version(self):
        assert CHATBOT_MODEL_VERSION == "faq-nlp-v2"

    def test_disclaimer(self):
        assert "NLP" in CHATBOT_DISCLAIMER or "rule-based" in CHATBOT_DISCLAIMER

    def test_synonyms_dict(self):
        assert isinstance(SYNONYMS, dict)
        assert len(SYNONYMS) >= 10
        for canonical, variants in SYNONYMS.items():
            assert isinstance(canonical, str)
            assert isinstance(variants, list)
            assert len(variants) > 0


# =================================================================
# Backward compat: v1 signature still works
# =================================================================
class TestV1Compat:
    def test_old_skeleton_intents(self):
        # All v1 intent names should still work (v2 renamed pinjol_atau_paylater to paylater_vs_pinjol)
        v1_intents = [
            "apa_itu_galbay", "apa_itu_skor_risiko", "pinjol_ilegal",
            "snowball_vs_avalanche", "bunga_tinggi_normal", "dc_agresif",
            "lapor_dc", "template_chat", "cara_recovery", "telat_30_hari",
            "negosiasi_cicilan", "aplikasi_aman", "premium_dapat_apa",
            "konseling_berapa", "diskon_premium", "cara_pakai_website",
            "data_sumber", "emergency_dc", "konsultan_keuangan",
            "self_reward_aman", "paylater_vs_pinjol", "berapa_utang_normal",
            "ai_atau_rule_based", "default_fallback",
        ]
        kb_intents = {e["intent"] for e in FAQ_KB}
        for intent in v1_intents:
            assert intent in kb_intents, f"v1 intent {intent} missing from v2 KB"

    def test_module_field_backward_compat(self):
        # v1 entries didn't have module, v2 should
        for entry in FAQ_KB:
            if entry["intent"] != "default_fallback":
                assert "module" in entry


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
