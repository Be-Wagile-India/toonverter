"""Type definitions and data classes for TOON Converter, including context optimization types."""

import datetime
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


# --- Standard Data Types & Aliases ---

# Define the supported type for a single data record
DataRecord = dict[str, Any]
# Define the supported types for data structure (list of records or a single record/dictionary)
DataStructure = list[DataRecord] | DataRecord
# Type aliases for common structures
ToonData = dict[str, Any] | list[Any] | str | int | float | bool | None
FormatName = Literal["json", "yaml", "toml", "csv", "xml", "toon"]


# --- TOON Format Configuration Classes ---


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


# --- Context Optimization Types (Existing structure preserved) ---


class ContextPolicyType(str, Enum):
    """Defines the prioritization policy for different use cases."""

    # Existing Use Cases
    LONG_CONVERSATION = "long_conversation"
    MULTI_AGENT = "multi_agent"
    STREAMING_RAG = "streaming_rag"
    GENERIC = "generic"

    # ADDED: Strategies used by context_helpers.py logic
    RECENCY = "recency"
    PRIORITY_THEN_RECENCY = "priority_then_recency"
    SIZE_THEN_RECENCY = "size_then_recency"


@dataclass
class ContextRecord:
    """
    Represents a single piece of context data (message, tool call, log, state).
    Required fields for intelligent prioritization.
    """

    data: DataStructure  # The actual data payload (str for message, dict for log/tool)
    source: str  # e.g., "user", "system", "tool_output", "monitoring_log"
    id: str = field(
        default_factory=lambda: str(hash(datetime.datetime.now(tz=datetime.timezone.utc)))
    )  # Unique ID for stability
    timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now(tz=datetime.timezone.utc)
    )
    # An optional, pre-calculated priority score (0-100), used as a tie-breaker or explicit override
    explicit_priority: int = 0
    # Flag to ensure critical information is NEVER pruned (e.g., initial system prompt, current state)
    is_critical: bool = False


@dataclass
class OptimizeOptions:
    """
    Options for data optimization (prioritization and trimming).
    """

    target_context_size: int = 4096  # Target in approximate characters/tokens
    max_items: int = 10  # Target maximum number of records
    max_field_length: int = 256  # Maximum length for string values
    exclude_fields: list[str] = field(default_factory=list)

    # New: The policy to guide prioritization logic
    policy_type: ContextPolicyType = ContextPolicyType.GENERIC


# --- Conversion Result & Analysis Classes ---


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


# --- Master Configuration Container ---


@dataclass
class ConvertOptions:
    """Container for all options used during a conversion process."""

    encode_options: EncodeOptions | None = None
    decode_options: DecodeOptions | None = None
    optimize_options: OptimizeOptions | None = None
