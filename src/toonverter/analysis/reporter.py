"""Analysis report generation."""

from ..core.types import ComparisonReport, TokenAnalysis


class ReportFormatter:
    """Format analysis reports for display."""

    @staticmethod
    def format_analysis(analysis: TokenAnalysis) -> str:
        """Format single token analysis.

        Args:
            analysis: TokenAnalysis to format

        Returns:
            Formatted report string
        """
        lines = [
            f"Format: {analysis.format}",
            f"Tokens: {analysis.token_count}",
            f"Model: {analysis.model}",
            f"Encoding: {analysis.encoding}",
        ]

        if analysis.metadata:
            lines.append("Metadata:")
            for key, value in analysis.metadata.items():
                lines.append(f"  {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def format_comparison(report: ComparisonReport, detailed: bool = False) -> str:
        """Format comparison report.

        Args:
            report: ComparisonReport to format
            detailed: Include detailed analysis for each format

        Returns:
            Formatted report string
        """
        lines = ["Token Usage Comparison", "=" * 50, ""]

        # Summary table
        lines.append(f"{'Format':<15} {'Tokens':<10} {'Savings':>10}")
        lines.append("-" * 50)

        worst_count = max(a.token_count for a in report.analyses)

        for analysis in sorted(report.analyses, key=lambda a: a.token_count):
            savings = ((worst_count - analysis.token_count) / worst_count) * 100
            marker = " ← Best" if analysis.format == report.best_format else ""
            lines.append(
                f"{analysis.format:<15} {analysis.token_count:<10} "
                f"{savings:>9.1f}%{marker}"
            )

        lines.append("")
        lines.append(f"Best format: {report.best_format}")
        lines.append(f"Worst format: {report.worst_format}")
        lines.append(f"Maximum savings: {report.max_savings_percentage:.1f}%")

        # Recommendations
        if report.recommendations:
            lines.append("")
            lines.append("Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"  {i}. {rec}")

        # Detailed analysis
        if detailed:
            lines.append("")
            lines.append("Detailed Analysis")
            lines.append("=" * 50)
            for analysis in report.analyses:
                lines.append("")
                lines.append(ReportFormatter.format_analysis(analysis))

        return "\n".join(lines)

    @staticmethod
    def format_json(report: ComparisonReport) -> dict:
        """Format comparison report as JSON-serializable dict.

        Args:
            report: ComparisonReport to format

        Returns:
            Dictionary representation
        """
        return {
            "analyses": [
                {
                    "format": a.format,
                    "token_count": a.token_count,
                    "model": a.model,
                    "encoding": a.encoding,
                    "metadata": a.metadata,
                }
                for a in report.analyses
            ],
            "best_format": report.best_format,
            "worst_format": report.worst_format,
            "max_savings_percentage": report.max_savings_percentage,
            "recommendations": report.recommendations,
        }


def format_report(report: ComparisonReport, format: str = "text", detailed: bool = False) -> str:
    """Format comparison report.

    Args:
        report: ComparisonReport to format
        format: Output format ('text' or 'json')
        detailed: Include detailed analysis

    Returns:
        Formatted report string
    """
    formatter = ReportFormatter()

    if format == "json":
        import json

        return json.dumps(formatter.format_json(report), indent=2)
    else:
        return formatter.format_comparison(report, detailed)
