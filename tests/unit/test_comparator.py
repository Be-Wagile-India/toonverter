"""Tests for format comparator."""

from unittest import mock

import pytest

from toonverter.analysis.comparator import FormatComparator, compare
from toonverter.core.exceptions import FormatNotSupportedError, TokenCountError
from toonverter.core.registry import registry
from toonverter.core.types import EncodeOptions, TokenAnalysis
from toonverter.formats.json_format import JsonFormatAdapter
from toonverter.formats.toon_format import ToonFormatAdapter
from toonverter.formats.yaml_format import YamlFormatAdapter


class TestFormatComparator:
    """Test FormatComparator functionality."""

    def setup_method(self):
        """Set up comparator and register formats."""
        self.comparator = FormatComparator(model="gpt-4")

        # Clear and register necessary formats
        registry.clear()
        registry.register("json", JsonFormatAdapter())
        registry.register("yaml", YamlFormatAdapter())
        registry.register("toon", ToonFormatAdapter())

    def teardown_method(self):
        """Clean up registry."""
        registry.clear()

    def test_init_sets_model(self):
        """Test initialization sets model name."""
        comparator = FormatComparator(model="gpt-3.5-turbo")
        assert comparator.model == "gpt-3.5-turbo"

    def test_compare_formats_returns_report(self):
        """Test compare_formats returns ComparisonReport."""
        data = {"name": "Alice", "age": 30}
        report = self.comparator.compare_formats(data, ["json", "yaml"])

        assert report is not None
        assert len(report.analyses) == 2
        assert report.best_format in ["json", "yaml"]
        assert report.worst_format in ["json", "yaml"]

    def test_compare_formats_with_unsupported_format(self):
        """Test compare_formats raises error for unsupported format."""
        data = {"test": "value"}

        with pytest.raises(FormatNotSupportedError, match="not supported"):
            self.comparator.compare_formats(data, ["nonexistent"])

    def test_compare_formats_identifies_best_format(self):
        """Test compare_formats correctly identifies best format."""
        data = {"name": "Alice", "age": 30}
        report = self.comparator.compare_formats(data, ["json", "yaml", "toon"])

        # Best format should have the minimum token count
        best_analysis = next(a for a in report.analyses if a.format == report.best_format)
        for analysis in report.analyses:
            assert best_analysis.token_count <= analysis.token_count

    def test_compare_formats_identifies_worst_format(self):
        """Test compare_formats correctly identifies worst format."""
        data = {"name": "Alice", "age": 30}
        report = self.comparator.compare_formats(data, ["json", "yaml", "toon"])

        # Worst format should have the maximum token count
        worst_analysis = next(a for a in report.analyses if a.format == report.worst_format)
        for analysis in report.analyses:
            assert worst_analysis.token_count >= analysis.token_count

    def test_compare_formats_empty_formats_list(self):
        """Test compare_formats with an empty list of formats."""
        data = {"name": "Alice"}
        report = self.comparator.compare_formats(data, [])
        assert report is not None
        assert len(report.analyses) == 0
        assert report.best_format == ""
        assert report.worst_format == ""
        assert report.recommendations == []

    def test_compare_formats_propagates_token_count_error(self):
        """Test compare_formats propagates TokenCountError from TiktokenCounter.analyze."""
        data = {"name": "Alice"}
        formats = ["json"]
        with mock.patch.object(self.comparator.counter, "analyze") as mock_analyze:
            mock_analyze.side_effect = TokenCountError("Test token counting error")
            with pytest.raises(TokenCountError, match="Test token counting error"):
                self.comparator.compare_formats(data, formats)

    def test_compare_formats_with_encode_options(self):
        """Test compare_formats with encoding options."""
        data = {"key": "value"}
        options = {"json": EncodeOptions(indent=2), "yaml": EncodeOptions(compact=True)}

        report = self.comparator.compare_formats(data, ["json", "yaml"], options)
        assert len(report.analyses) == 2

    def test_generate_recommendations_returns_list(self):
        """Test _generate_recommendations returns list."""
        from toonverter.core.types import TokenAnalysis

        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=50),
        ]

        recommendations = self.comparator._generate_recommendations(analyses)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_generate_recommendations_empty_list(self):
        """Test _generate_recommendations with empty analyses."""
        recommendations = self.comparator._generate_recommendations([])
        assert recommendations == []

    def test_recommendations_suggest_best_format(self):
        """Test recommendations suggest the best format."""
        from toonverter.core.types import TokenAnalysis

        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=50),
        ]

        recommendations = self.comparator._generate_recommendations(analyses)
        assert any("toon" in rec.lower() for rec in recommendations)

    def test_recommendations_include_savings_for_large_difference(self):
        """Test recommendations include savings percentage for >20% difference."""
        from toonverter.core.types import TokenAnalysis

        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=50),
        ]

        recommendations = self.comparator._generate_recommendations(analyses)
        # Should include savings message since difference is 50%
        assert any("saves" in rec.lower() for rec in recommendations)

    def test_recommendations_no_savings_for_small_difference(self):
        """Test no savings recommendation for <20% difference."""
        from toonverter.core.types import TokenAnalysis

        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="yaml", token_count=90),
        ]

        recommendations = self.comparator._generate_recommendations(analyses)
        # Should not include savings message since difference is only 10%
        savings_recs = [r for r in recommendations if "saves" in r.lower()]
        assert len(savings_recs) == 0

    def test_recommendations_highlight_toon_optimal(self):
        """Test recommendations highlight when TOON is optimal."""
        from toonverter.core.types import TokenAnalysis

        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=50),
        ]

        recommendations = self.comparator._generate_recommendations(analyses)
        # Should include TOON-specific recommendation
        assert any("TOON format provides optimal" in rec for rec in recommendations)

    def test_recommendations_no_toon_analysis(self):
        """Test recommendations when TOON analysis is not present."""
        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="yaml", token_count=80),
        ]
        recommendations = self.comparator._generate_recommendations(analyses)
        assert "TOON format provides optimal" not in "".join(recommendations)
        assert "tabular" not in "".join(recommendations)

    def test_recommendations_no_json_analysis(self):
        """Test recommendations when JSON analysis is not present."""
        analyses = [
            TokenAnalysis(format="toon", token_count=50),
            TokenAnalysis(format="yaml", token_count=80),
        ]
        recommendations = self.comparator._generate_recommendations(analyses)
        assert "tabular" not in "".join(recommendations)

    def test_recommendations_tabular_data_detection_boundary(self):
        """Test recommendations detect tabular data at the 0.7 threshold."""
        analyses = [
            TokenAnalysis(format="json", token_count=100),
            TokenAnalysis(format="toon", token_count=70),  # Exactly 70% of JSON
        ]
        recommendations = self.comparator._generate_recommendations(analyses)
        assert any("tabular" in rec.lower() for rec in recommendations)

    def test_recommendations_worst_token_count_zero(self):
        """Test recommendations when worst_token_count is zero (edge case)."""
        analyses = [
            TokenAnalysis(format="json", token_count=0),
            TokenAnalysis(format="toon", token_count=0),
        ]
        recommendations = self.comparator._generate_recommendations(analyses)
        # Should not raise ZeroDivisionError and still provide recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_recommendations_single_format(self):
        """Test recommendations with only one format in analyses."""
        analyses = [
            TokenAnalysis(format="json", token_count=100),
        ]
        recommendations = self.comparator._generate_recommendations(analyses)
        assert "Use 'json' format for optimal token efficiency (100 tokens)" in recommendations
        assert not any("saves" in rec for rec in recommendations)


class TestCompareFunction:
    """Test convenience compare() function."""

    def setup_method(self):
        """Register formats."""
        registry.clear()
        registry.register("json", JsonFormatAdapter())
        registry.register("yaml", YamlFormatAdapter())
        registry.register("toon", ToonFormatAdapter())

    def teardown_method(self):
        """Clean up registry."""
        registry.clear()

    def test_compare_returns_report(self):
        """Test compare function returns ComparisonReport."""
        data = {"name": "Alice", "age": 30}
        report = compare(data, ["json", "yaml"])

        assert report is not None
        assert len(report.analyses) == 2

    def test_compare_with_custom_model(self):
        """Test compare function with custom model."""
        data = {"test": "value"}
        report = compare(data, ["json"], model="gpt-3.5-turbo")

        assert report is not None

    def test_compare_with_encode_options(self):
        """Test compare function with encoding options."""
        data = {"key": "value"}
        options = {"json": EncodeOptions(indent=4)}

        report = compare(data, ["json"], encode_options=options)
        assert report is not None

    def test_compare_propagates_token_count_error(self):
        """Test compare function propagates TokenCountError from FormatComparator initialization."""
        with mock.patch("toonverter.analysis.comparator.FormatComparator") as mock_comparator:
            mock_comparator.side_effect = TokenCountError("Comparator init error")
            with pytest.raises(TokenCountError, match="Comparator init error"):
                compare({"test": "data"}, ["json"])
