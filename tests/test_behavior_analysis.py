"""Unit tests untuk Area B — behavioral (galbay) signal analysis."""
import pandas as pd

from scripts.behavior_analysis import (
    count_categories,
    flag_distress,
    keyword_scan,
    score_severity,
)


def _df(rows):
    return pd.DataFrame(rows)


class TestCountCategories:
    def test_counts_each_category_once_per_review(self):
        df = _df([
            {"mc": "produk_fintech, bunga_dan_biaya"},
            {"mc": "produk_fintech"},
            {"mc": ""},
        ])
        result = {r["key"]: r["count"] for r in count_categories(df, mc_col="mc")}
        assert result["produk_fintech"] == 2
        assert result["bunga_dan_biaya"] == 1
        assert "" not in result

    def test_uses_human_readable_label(self):
        df = _df([{"mc": "distress_langsung"}])
        result = count_categories(df, mc_col="mc")
        assert result[0]["label"] == "Distress Finansial Langsung"

    def test_unknown_category_falls_back_to_raw_key(self):
        df = _df([{"mc": "kategori_baru_belum_terdaftar"}])
        result = count_categories(df, mc_col="mc")
        assert result[0]["label"] == "kategori_baru_belum_terdaftar"

    def test_sorted_most_common_first(self):
        df = _df([{"mc": "a"}, {"mc": "a"}, {"mc": "b"}])
        result = count_categories(df, mc_col="mc")
        assert [r["key"] for r in result] == ["a", "b"]


class TestFlagDistress:
    def test_flags_known_distress_tag(self):
        df = _df([{"mc": "distress_langsung"}, {"mc": "produk_fintech"}, {"mc": ""}])
        flags = flag_distress(df, mc_col="mc")
        assert list(flags) == [1, 0, 0]

    def test_flags_if_any_of_multiple_tags_is_distress(self):
        df = _df([{"mc": "produk_fintech, psikologi_avoidance"}])
        assert list(flag_distress(df, mc_col="mc")) == [1]


class TestKeywordScan:
    def test_counts_matching_reviews_not_occurrences(self):
        df = _df([{"content": "galbay galbay galbay"}, {"content": "aman terkendali"}])
        result = {r["label"]: r["count"] for r in keyword_scan(df, content_col="content")}
        assert result["gagal bayar/galbay"] == 1

    def test_pinjol_legal_keyword_has_word_boundaries(self):
        # regression: original regex `ilegal| legal|ojk` (no \b) matched
        # " legal" as a bare substring, so unrelated words like "legalisir"
        # (notarize a document) falsely counted as a legal/illegal mention.
        df = _df([{"content": "ada legalisir dokumen pinjaman yang diperlukan"}])
        result = {r["label"]: r["count"] for r in keyword_scan(df, content_col="content")}
        assert result["pinjol ilegal"] == 0

    def test_dc_keyword_uses_word_boundary(self):
        no_match = _df([{"content": "abdcef tidak relevan"}])
        match = _df([{"content": "tiap hari ditelpon dc terus"}])
        no_match_counts = {r["label"]: r["count"] for r in keyword_scan(no_match, content_col="content")}
        match_counts = {r["label"]: r["count"] for r in keyword_scan(match, content_col="content")}
        assert no_match_counts["debt collector/DC"] == 0
        assert match_counts["debt collector/DC"] == 1

    def test_sorted_descending_by_count(self):
        df = _df([{"content": "galbay galbay"}, {"content": "denda saja"}])
        result = keyword_scan(df, content_col="content")
        counts = [r["count"] for r in result]
        assert counts == sorted(counts, reverse=True)


class TestScoreSeverity:
    def test_zero_signal_is_zero_severity_low_bucket(self):
        df = _df([{"mc": "", "content": "biasa saja tidak ada masalah"}])
        result = score_severity(df, mc_col="mc", content_col="content")
        assert result.iloc[0]["severity"] == 0
        assert result.iloc[0]["severity_bucket"] == "rendah"

    def test_more_distress_categories_increase_severity(self):
        df = _df([
            {"mc": "distress_langsung", "content": "biasa saja"},
            {"mc": "distress_langsung, tagihan_dan_penagihan, psikologi_avoidance", "content": "biasa saja"},
        ])
        result = score_severity(df, mc_col="mc", content_col="content")
        assert result.iloc[1]["severity"] > result.iloc[0]["severity"]

    def test_more_keyword_hits_increase_severity(self):
        df = _df([
            {"mc": "", "content": "telat sedikit"},
            {"mc": "", "content": "telat bayar denda bunga tinggi sekali galbay parah"},
        ])
        result = score_severity(df, mc_col="mc", content_col="content")
        assert result.iloc[1]["severity"] > result.iloc[0]["severity"]

    def test_severity_capped_at_100(self):
        df = _df([{
            "mc": "distress_langsung, tagihan_dan_penagihan, psikologi_avoidance, psikologi_regret_stress",
            "content": "galbay nunggak denda bunga dc teror ilegal gali lubang tutup lubang bayar",
        }])
        result = score_severity(df, mc_col="mc", content_col="content")
        assert result.iloc[0]["severity"] == 100
        assert result.iloc[0]["severity_bucket"] == "tinggi"

    def test_bucket_boundaries(self):
        from scripts.behavior_analysis import _severity_bucket
        assert _severity_bucket(0) == "rendah"
        assert _severity_bucket(32.9) == "rendah"
        assert _severity_bucket(33) == "sedang"
        assert _severity_bucket(65.9) == "sedang"
        assert _severity_bucket(66) == "tinggi"
        assert _severity_bucket(100) == "tinggi"
