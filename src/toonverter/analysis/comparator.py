"""Multi-format token comparison."""

from typing import Any

from toonverter.core.exceptions import FormatNotSupportedError
from toonverter.core.registry import registry
from toonverter.core.types import ComparisonReport, EncodeOptions, TokenAnalysis

from .analyzer import TiktokenCounter


class FormatComparator:
    """Compare token usage across multiple formats."""

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize comparator.

        Args:
            model: Model name for token counting
        """
        self.counter = TiktokenCounter(model)
        self.model = model

    def compare_formats(
        self,
        data: Any,
        formats: list[str],
        encode_options: dict[str, EncodeOptions] | None = None,
    ) -> ComparisonReport:
        """Compare token usage across formats.

        Args:
            data: Data to encode and analyze
            formats: List of format names to compare
            encode_options: Optional format-specific encoding options

        Returns:
            ComparisonReport with analysis for each format

        Raises:
            FormatNotSupportedError: If a format is not supported
        """
        encode_options = encode_options or {}
        analyses: list[TokenAnalysis] = []

        for format_name in formats:
            if not registry.is_supported(format_name):
                msg = f"Format '{format_name}' is not supported"
                raise FormatNotSupportedError(msg)

            adapter = registry.get(format_name)
            options = encode_options.get(format_name)

            # Encode data to format
            encoded_text = adapter.encode(data, options)

            # Analyze token usage
            analysis = self.counter.analyze(encoded_text, format_name)
            analyses.append(analysis)

        # Find best and worst formats
        best_format = min(analyses, key=lambda a: a.token_count).format
        worst_format = max(analyses, key=lambda a: a.token_count).format

        # Generate recommendations
        recommendations = self._generate_recommendations(analyses)

        return ComparisonReport(
            analyses=analyses,
            best_format=best_format,
            worst_format=worst_format,
            recommendations=recommendations,
        )

    def _generate_recommendations(self, analyses: list[TokenAnalysis]) -> list[str]:
        """Generate optimization recommendations.

        Args:
            analyses: List of token analyses

        Returns:
            List of recommendation strings
        """
        if not analyses:
            return []

        recommendations = []
        best = min(analyses, key=lambda a: a.token_count)
        worst = max(analyses, key=lambda a: a.token_count)

        savings = ((worst.token_count - best.token_count) / worst.token_count) * 100

        recommendations.append(
            f"Use '{best.format}' format for optimal token efficiency ({best.token_count} tokens)"
        )

        if savings > 20:
            recommendations.append(
                f"Switching from '{worst.format}' to '{best.format}' saves {savings:.1f}% tokens"
            )

        # Check for TOON format
        toon_analysis = next((a for a in analyses if a.format == "toon"), None)
        if toon_analysis and toon_analysis.token_count == best.token_count:
            recommendations.append("TOON format provides optimal token efficiency for this data")

        # Check for tabular data opportunity
        json_analysis = next((a for a in analyses if a.format == "json"), None)
        if json_analysis and toon_analysis:
            if toon_analysis.token_count < json_analysis.token_count * 0.7:
                recommendations.append(
                    "This data appears to be tabular - TOON format is highly efficient"
                )

        return recommendations


def compare(
    data: Any,
    formats: list[str],
    model: str = "gpt-4",
    encode_options: dict[str, EncodeOptions] | None = None,
) -> ComparisonReport:
    """Convenience function to compare formats.

    Args:
        data: Data to analyze
        formats: List of format names
        model: Model name for token counting
        encode_options: Format-specific encoding options

    Returns:
        ComparisonReport with comparison results

    Examples:
        >>> data = {"name": "Alice", "age": 30}
        >>> report = compare(data, ["json", "yaml", "toon"])
        >>> print(f"Best format: {report.best_format}")
        Best format: toon
    """
    comparator = FormatComparator(model)
    return comparator.compare_formats(data, formats, encode_options)
