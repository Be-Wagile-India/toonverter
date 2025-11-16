"""Type definitions and data classes for TOON Converter."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class EncodeOptions:
    """Configuration options for encoding data to TOON format.

    This class uses the Builder pattern to provide preset configurations
    and flexible customization.

    Attributes:
        indent: Number of spaces for indentation (default: 2)
        delimiter: Field delimiter for tabular data
        length_marker: Optional length prefix for strings
        compact: Use compact representation without whitespace
        sort_keys: Sort dictionary keys alphabetically
        ensure_ascii: Escape non-ASCII characters
        max_line_length: Maximum line length before wrapping
    """

    indent: int = 2
    delimiter: Literal[",", "\t", "|", ";"] = ","
    length_marker: str | None = None
    compact: bool = False
    sort_keys: bool = False
    ensure_ascii: bool = False
    max_line_length: int | None = None

    @classmethod
    def create_compact(cls) -> "EncodeOptions":
        """Create preset for compact encoding.

        Returns:
            EncodeOptions configured for minimal token usage
        """
        return cls(indent=0, compact=True, delimiter=",")

    @classmethod
    def readable(cls) -> "EncodeOptions":
        """Create preset for human-readable encoding.

        Returns:
            EncodeOptions configured for readability
        """
        return cls(indent=2, compact=False, delimiter=",", sort_keys=True)

    @classmethod
    def tabular(cls) -> "EncodeOptions":
        """Create preset for tabular data encoding.

        Returns:
            EncodeOptions optimized for DataFrame-like structures
        """
        return cls(indent=0, compact=True, delimiter=",")


@dataclass
class DecodeOptions:
    """Configuration options for decoding TOON format.

    Attributes:
        strict: Raise errors on malformed input
        type_inference: Automatically infer data types
        delimiter: Expected field delimiter
    """

    strict: bool = True
    type_inference: bool = True
    delimiter: Literal[",", "\t", "|", ";"] = ","


@dataclass
class ConversionResult:
    """Result of a format conversion operation.

    Attributes:
        success: Whether conversion succeeded
        source_format: Original format
        target_format: Target format
        source_tokens: Token count of source data
        target_tokens: Token count of target data
        savings_percentage: Percentage of tokens saved
        data: Converted data (if successful)
        error: Error message (if failed)
        metadata: Additional conversion metadata
    """

    success: bool
    source_format: str
    target_format: str
    source_tokens: int | None = None
    target_tokens: int | None = None
    savings_percentage: float | None = None
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Calculate savings percentage if token counts are available."""
        if (
            self.source_tokens is not None
            and self.target_tokens is not None
            and self.source_tokens > 0
        ):
            self.savings_percentage = (
                (self.source_tokens - self.target_tokens) / self.source_tokens * 100
            )


@dataclass
class TokenAnalysis:
    """Analysis of token usage for different formats.

    Attributes:
        format: Data format analyzed
        token_count: Number of tokens
        model: Tokenizer model used
        encoding: Specific encoding method
        metadata: Additional analysis metadata
    """

    format: str
    token_count: int
    model: str = "cl100k_base"
    encoding: str = "utf-8"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonReport:
    """Comparative analysis of multiple formats.

    Attributes:
        analyses: Token analyses for each format
        best_format: Format with lowest token count
        worst_format: Format with highest token count
        recommendations: Optimization recommendations
    """

    analyses: list[TokenAnalysis]
    best_format: str
    worst_format: str
    recommendations: list[str] = field(default_factory=list)

    @property
    def max_savings_percentage(self) -> float:
        """Calculate maximum possible token savings.

        Returns:
            Percentage savings from worst to best format
        """
        if not self.analyses:
            return 0.0

        best = min(a.token_count for a in self.analyses)
        worst = max(a.token_count for a in self.analyses)

        if worst == 0:
            return 0.0

        return ((worst - best) / worst) * 100


# Type aliases for common structures
ToonData = dict[str, Any] | list[Any] | str | int | float | bool | None
FormatName = Literal["json", "yaml", "toml", "csv", "xml", "toon"]
