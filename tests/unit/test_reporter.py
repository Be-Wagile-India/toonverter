"""Comprehensive tests for report formatter."""

import pytest
import json
from toonverter.analysis.reporter import ReportFormatter, format_report
from toonverter.core.types import TokenAnalysis, ComparisonReport


class TestFormatAnalysis:
    """Test formatting single token analysis."""

    def test_format_analysis_basic(self):
        """Test formatting basic token analysis."""
        analysis = TokenAnalysis(
            format="json",
            token_count=100,
            model="gpt-4",
            encoding="cl100k_base"
        )

        result = ReportFormatter.format_analysis(analysis)

        assert "Format: json" in result
        assert "Tokens: 100" in result
        assert "Model: gpt-4" in result
        assert "Encoding: cl100k_base" in result

    def test_format_analysis_with_metadata(self):
        """Test formatting analysis with metadata."""
        analysis = TokenAnalysis(
            format="toon",
            token_count=50,
            model="gpt-4",
            encoding="cl100k_base",
            metadata={"text_length": 200, "compression_ratio": 4.0}
        )

        result = ReportFormatter.format_analysis(analysis)

        assert "Metadata:" in result
        assert "text_length: 200" in result
        assert "compression_ratio: 4.0" in result

    def test_format_analysis_without_metadata(self):
        """Test formatting analysis without metadata."""
        analysis = TokenAnalysis(
            format="yaml",
            token_count=75,
            model="gpt-3.5-turbo",
            encoding="cl100k_base"
        )

        result = ReportFormatter.format_analysis(analysis)

        assert "Metadata:" not in result


class TestFormatComparison:
    """Test formatting comparison reports."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyses = [
            TokenAnalysis(format="json", token_count=100, model="gpt-4", encoding="cl100k_base"),
            TokenAnalysis(format="toon", token_count=60, model="gpt-4", encoding="cl100k_base"),
            TokenAnalysis(format="yaml", token_count=80, model="gpt-4", encoding="cl100k_base"),
        ]

        self.report = ComparisonReport(
            analyses=self.analyses,
            best_format="toon",
            worst_format="json",
            recommendations=[
                "Use TOON format for optimal token efficiency",
                "TOON saves 40% tokens compared to JSON"
            ]
        )

    def test_format_comparison_header(self):
        """Test comparison report includes header."""
        result = ReportFormatter.format_comparison(self.report)

        assert "Token Usage Comparison" in result
        assert "=" * 50 in result

    def test_format_comparison_table(self):
        """Test comparison report includes summary table."""
        result = ReportFormatter.format_comparison(self.report)

        assert "Format" in result
        assert "Tokens" in result
        assert "Savings" in result

    def test_format_comparison_all_formats(self):
        """Test all formats appear in comparison."""
        result = ReportFormatter.format_comparison(self.report)

        assert "json" in result
        assert "toon" in result
        assert "yaml" in result

    def test_format_comparison_best_marker(self):
        """Test best format is marked."""
        result = ReportFormatter.format_comparison(self.report)

        assert "← Best" in result

    def test_format_comparison_summary(self):
        """Test comparison includes summary section."""
        result = ReportFormatter.format_comparison(self.report)

        assert "Best format: toon" in result
        assert "Worst format: json" in result
        assert "Maximum savings: 40.0%" in result

    def test_format_comparison_recommendations(self):
        """Test recommendations are included."""
        result = ReportFormatter.format_comparison(self.report)

        assert "Recommendations:" in result
        assert "Use TOON format" in result
        assert "saves 40%" in result

    def test_format_comparison_no_recommendations(self):
        """Test report without recommendations."""
        report = ComparisonReport(
            analyses=self.analyses,
            best_format="toon",
            worst_format="json",
            recommendations=[]
        )

        result = ReportFormatter.format_comparison(report)

        # Recommendations section should not appear
        assert "Recommendations:" not in result

    def test_format_comparison_sorted_by_tokens(self):
        """Test formats are sorted by token count."""
        result = ReportFormatter.format_comparison(self.report)

        # Find positions of format names
        lines = result.split("\n")
        format_lines = [l for l in lines if any(fmt in l for fmt in ["json", "toon", "yaml"])]

        # TOON (60) should come before YAML (80) which comes before JSON (100)
        toon_idx = next(i for i, l in enumerate(format_lines) if "toon" in l)
        yaml_idx = next(i for i, l in enumerate(format_lines) if "yaml" in l)
        json_idx = next(i for i, l in enumerate(format_lines) if "json" in l)

        assert toon_idx < yaml_idx < json_idx

    def test_format_comparison_detailed(self):
        """Test detailed comparison report."""
        result = ReportFormatter.format_comparison(self.report, detailed=True)

        assert "Detailed Analysis" in result
        # Should include detailed analysis for each format
        assert result.count("Format: ") >= 3  # Once in each detailed section

    def test_format_comparison_not_detailed(self):
        """Test non-detailed comparison report."""
        result = ReportFormatter.format_comparison(self.report, detailed=False)

        assert "Detailed Analysis" not in result


class TestFormatJSON:
    """Test JSON formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyses = [
            TokenAnalysis(
                format="json",
                token_count=100,
                model="gpt-4",
                encoding="cl100k_base",
                metadata={"length": 500}
            ),
            TokenAnalysis(
                format="toon",
                token_count=60,
                model="gpt-4",
                encoding="cl100k_base"
            ),
        ]

        self.report = ComparisonReport(
            analyses=self.analyses,
            best_format="toon",
            worst_format="json",
            recommendations=["Use TOON"]
        )

    def test_format_json_returns_dict(self):
        """Test JSON formatting returns dict."""
        result = ReportFormatter.format_json(self.report)

        assert isinstance(result, dict)

    def test_format_json_includes_analyses(self):
        """Test JSON includes analyses."""
        result = ReportFormatter.format_json(self.report)

        assert "analyses" in result
        assert len(result["analyses"]) == 2

    def test_format_json_analysis_structure(self):
        """Test JSON analysis structure."""
        result = ReportFormatter.format_json(self.report)

        analysis = result["analyses"][0]
        assert "format" in analysis
        assert "token_count" in analysis
        assert "model" in analysis
        assert "encoding" in analysis
        assert "metadata" in analysis

    def test_format_json_includes_summary(self):
        """Test JSON includes summary fields."""
        result = ReportFormatter.format_json(self.report)

        assert result["best_format"] == "toon"
        assert result["worst_format"] == "json"
        assert result["max_savings_percentage"] == 40.0

    def test_format_json_includes_recommendations(self):
        """Test JSON includes recommendations."""
        result = ReportFormatter.format_json(self.report)

        assert "recommendations" in result
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0] == "Use TOON"

    def test_format_json_preserves_metadata(self):
        """Test JSON preserves metadata."""
        result = ReportFormatter.format_json(self.report)

        # First analysis has metadata
        assert result["analyses"][0]["metadata"] == {"length": 500}
        # Second analysis has empty metadata dict
        assert result["analyses"][1]["metadata"] == {}


class TestFormatReportFunction:
    """Test format_report convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyses = [
            TokenAnalysis(format="json", token_count=100, model="gpt-4", encoding="cl100k_base"),
            TokenAnalysis(format="toon", token_count=60, model="gpt-4", encoding="cl100k_base"),
        ]

        self.report = ComparisonReport(
            analyses=self.analyses,
            best_format="toon",
            worst_format="json",
            recommendations=["Use TOON"]
        )

    def test_format_report_default_text(self):
        """Test default format is text."""
        result = format_report(self.report)

        assert isinstance(result, str)
        assert "Token Usage Comparison" in result

    def test_format_report_text_format(self):
        """Test explicit text format."""
        result = format_report(self.report, format="text")

        assert "Token Usage Comparison" in result

    def test_format_report_json_format(self):
        """Test JSON format."""
        result = format_report(self.report, format="json")

        # Should be valid JSON
        parsed = json.loads(result)
        assert "best_format" in parsed
        assert parsed["best_format"] == "toon"

    def test_format_report_detailed(self):
        """Test detailed flag."""
        result = format_report(self.report, format="text", detailed=True)

        assert "Detailed Analysis" in result

    def test_format_report_not_detailed(self):
        """Test non-detailed flag."""
        result = format_report(self.report, format="text", detailed=False)

        assert "Detailed Analysis" not in result


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_format_analysis_empty_metadata(self):
        """Test formatting with empty metadata dict."""
        analysis = TokenAnalysis(
            format="json",
            token_count=100,
            model="gpt-4",
            encoding="cl100k_base",
            metadata={}
        )

        result = ReportFormatter.format_analysis(analysis)

        # Empty metadata dict should not show Metadata section (no items to display)
        assert "Metadata:" not in result

    def test_format_comparison_single_format(self):
        """Test comparison with single format."""
        analyses = [
            TokenAnalysis(format="json", token_count=100, model="gpt-4", encoding="cl100k_base")
        ]

        report = ComparisonReport(
            analyses=analyses,
            best_format="json",
            worst_format="json",
            recommendations=[]
        )

        result = ReportFormatter.format_comparison(report)

        assert "json" in result
        assert "100" in result

    def test_format_comparison_identical_counts(self):
        """Test comparison with identical token counts."""
        analyses = [
            TokenAnalysis(format="json", token_count=100, model="gpt-4", encoding="cl100k_base"),
            TokenAnalysis(format="yaml", token_count=100, model="gpt-4", encoding="cl100k_base"),
        ]

        report = ComparisonReport(
            analyses=analyses,
            best_format="json",
            worst_format="yaml",
            recommendations=[]
        )

        result = ReportFormatter.format_comparison(report)

        # Savings should be 0.0%
        assert "0.0%" in result
