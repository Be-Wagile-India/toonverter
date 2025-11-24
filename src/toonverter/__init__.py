"""TOON Converter - Token-Optimized Object Notation for LLMs.

This package provides efficient data serialization specifically designed
to reduce token usage when sending data to Large Language Models.

Quick Start:
    >>> import toon_converter as toon
    >>> data = {"name": "Alice", "age": 30}
    >>> toon_str = toon.encode(data)
    >>> decoded = toon.decode(toon_str)
"""

from collections.abc import Callable
from typing import Any, Optional

from toonverter.core.spec import ToonEncodeOptions

from .__version__ import __author__, __license__, __version__
from .analysis import FormatComparator, TiktokenCounter, compare, count_tokens
from .analysis.deduplication import SemanticDeduplicator
from .core import (
    ComparisonReport,
    ConversionError,
    ConversionResult,
    DecodeOptions,
    DecodingError,
    EncodeOptions,
    EncodingError,
    FormatNotSupportedError,
    TokenAnalysis,
    ToonConverterError,
    ValidationError,
    registry,
)
from .core.registry import get_registry
from .decoders import ToonDecoder
from .differ import DiffResult
from .encoders import ToonEncoder
from .formats import register_default_formats
from .plugins import load_plugins
from .schema import SchemaField, SchemaInferrer, SchemaValidator
from .utils import read_file, write_file


# Initialize package
register_default_formats()

# Level 1 Facade API - Simple functions for 90% of users


def convert(
    source: str,
    target: str,
    from_format: str,
    to_format: str,
    **options: Any,
) -> ConversionResult:
    """Convert data from one format to another.

    Args:
        source: Path to source file
        target: Path to target file
        from_format: Source format (e.g., 'json', 'yaml')
        to_format: Target format (e.g., 'toon')
        **options: Additional conversion options

    Returns:
        ConversionResult with conversion details

    Raises:
        FormatNotSupportedError: If format not supported
        ConversionError: If conversion fails

    Examples:
        >>> convert('data.json', 'data.toon', 'json', 'toon')
    """
    try:
        # Read source file
        source_data_str = read_file(source)

        # Decode from source format
        source_adapter = registry.get(from_format)
        data = source_adapter.decode(source_data_str)

        # Encode to target format
        target_adapter = registry.get(to_format)
        target_data_str = target_adapter.encode(data)

        # Write target file
        write_file(target, target_data_str)

        # Count tokens for comparison
        counter = TiktokenCounter()
        source_tokens = counter.count_tokens(source_data_str)
        target_tokens = counter.count_tokens(target_data_str)

        return ConversionResult(
            success=True,
            source_format=from_format,
            target_format=to_format,
            source_tokens=source_tokens,
            target_tokens=target_tokens,
            data=data,
        )
    except Exception as e:
        return ConversionResult(
            success=False, source_format=from_format, target_format=to_format, error=str(e)
        )


def encode(data: Any, to_format: str = "toon", **options: Any) -> str:
    """Encode data to specified format.

    Args:
        data: Data to encode
        to_format: Target format (default: 'toon')
        **options: Encoding options

    Returns:
        Encoded string

    Raises:
        FormatNotSupportedError: If format not supported
        EncodingError: If encoding fails

    Examples:
        >>> encode({"name": "Alice"}, to_format='toon')
        '{name:Alice}'
    """
    adapter = registry.get(to_format)
    encode_opts = EncodeOptions(**options) if options else None
    return adapter.encode(data, encode_opts)


def decode(data_str: str, from_format: str = "toon", **options: Any) -> Any:
    """Decode data from specified format.

    Args:
        data_str: Data string to decode
        from_format: Source format (default: 'toon')
        **options: Decoding options

    Returns:
        Decoded Python data

    Raises:
        FormatNotSupportedError: If format not supported
        DecodingError: If decoding fails

    Examples:
        >>> decode('{name:Alice}', from_format='toon')
        {'name': 'Alice'}
    """
    adapter = registry.get(from_format)
    decode_opts = DecodeOptions(**options) if options else None
    return adapter.decode(data_str, decode_opts)


def analyze(
    data: Any, from_format: str = "json", compare_formats: list[str] | None = None
) -> ComparisonReport:
    """Analyze token usage across formats.

    Args:
        data: Data to analyze
        from_format: Source format
        compare_formats: Formats to compare (default: ['json', 'yaml', 'toon'])

    Returns:
        ComparisonReport with analysis

    Examples:
        >>> report = analyze({"name": "Alice"}, compare_formats=['json', 'toon'])
        >>> print(f"Best: {report.best_format}")
    """
    if compare_formats is None:
        compare_formats = ["json", "yaml", "toon"]

    comparator = FormatComparator()
    return comparator.compare_formats(data, compare_formats)


def load(path: str, format: str) -> Any:
    """Load data from file.

    Args:
        path: File path
        format: File format

    Returns:
        Decoded data

    Examples:
        >>> data = load('config.yaml', format='yaml')
    """
    content = read_file(path)
    return decode(content, from_format=format)


def save(data: Any, path: str, format: str, **options: Any) -> None:
    """Save data to file.

    Args:
        data: Data to save
        path: File path
        format: File format
        **options: Encoding options

    Examples:
        >>> save({"key": "value"}, 'data.toon', format='toon')
    """
    content = encode(data, to_format=format, **options)
    write_file(path, content)


def list_formats() -> list[str]:
    """List all supported formats.

    Returns:
        List of format names

    Examples:
        >>> formats = list_formats()
        >>> print(formats)
        ['json', 'yaml', 'toml', 'csv', 'xml', 'toon']
    """
    return registry.list_formats()


def is_supported(format: str) -> bool:
    """Check if format is supported.

    Args:
        format: Format name

    Returns:
        True if format is supported

    Examples:
        >>> is_supported('toon')
        True
    """
    return registry.is_supported(format)


# Level 2 OOP API - Exported classes for power users
class Converter:
    """Stateful converter for advanced use cases."""

    def __init__(
        self,
        from_format: str,
        to_format: str,
        **options: Any,
    ) -> None:
        """Initialize converter.

        Args:
            from_format: Source format
            to_format: Target format
            **options: Conversion options
        """
        self.from_format = from_format
        self.to_format = to_format
        self.options = options
        self.source_adapter = registry.get(from_format)
        self.target_adapter = registry.get(to_format)

    def convert_file(self, source: str, target: str) -> ConversionResult:
        """Convert file.

        Args:
            source: Source file path
            target: Target file path

        Returns:
            ConversionResult
        """
        return convert(source, target, self.from_format, self.to_format, **self.options)

    def convert_data(self, data: Any) -> Any:
        """Convert data in memory.

        Args:
            data: Data to convert

        Returns:
            Converted data
        """
        # Encode to target format and decode back
        encoded = self.target_adapter.encode(data)
        return self.target_adapter.decode(encoded)


class Encoder:
    """Stateful encoder for advanced use cases."""

    def __init__(self, format: str = "toon", **options: Any) -> None:
        """Initialize encoder.

        Args:
            format: Target format
            **options: Encoding options
        """
        self.format = format
        self.options = EncodeOptions(**options) if options else None
        self.adapter = registry.get(format)

    def encode(self, data: Any) -> str:
        """Encode data.

        Args:
            data: Data to encode

        Returns:
            Encoded string
        """
        return self.adapter.encode(data, self.options)


class Decoder:
    """Stateful decoder for advanced use cases."""

    def __init__(self, format: str = "toon", **options: Any) -> None:
        """Initialize decoder.

        Args:
            format: Source format
            **options: Decoding options
        """
        self.format = format
        self.options = DecodeOptions(**options) if options else None
        self.adapter = registry.get(format)

    def decode(self, data_str: str) -> Any:
        """Decode data.

        Args:
            data_str: Data string to decode

        Returns:
            Decoded data
        """
        return self.adapter.decode(data_str, self.options)


class Analyzer:
    """Token usage analyzer."""

    def __init__(self, model: str = "gpt-4", **options: Any) -> None:
        """Initialize analyzer.

        Args:
            model: Model for token counting
            **options: Analysis options
        """
        self.model = model
        self.comparator = FormatComparator(model)

    def analyze_multi_format(
        self, data: Any, formats: list[str], **options: Any
    ) -> ComparisonReport:
        """Analyze multiple formats.

        Args:
            data: Data to analyze
            formats: Formats to compare
            **options: Analysis options

        Returns:
            ComparisonReport
        """
        return self.comparator.compare_formats(data, formats)


__all__ = [
    "Analyzer",
    "ComparisonReport",
    "ConversionError",
    "ConversionResult",
    "DecodeOptions",
    "Decoder",
    "DecodingError",
    "DiffResult",
    # Types
    "EncodeOptions",
    "Encoder",
    "EncodingError",
    "FormatComparator",
    "FormatNotSupportedError",
    "TiktokenCounter",
    "TokenAnalysis",
    # Exceptions
    "ToonConverterError",
    "ToonDecoder",
    "ToonEncoder",
    "ValidationError",
    "__author__",
    "__license__",
    # Schema
    "SchemaField",
    "SchemaInferrer",
    "SchemaValidator",
    # Version info
    "__version__",
    "analyze",
    "compare",
    # Level 1 Facade API
    "convert",
    "count_tokens",
    "decode",
    "encode",
    "get_registry",
    "is_supported",
    "list_formats",
    "load",
    "load_plugins",
    # Utilities
    "registry",
    "save",
    # Schema Tools
    "infer_schema",
    "validate_schema",
    # Diff
    "diff",
    # Vision
    "optimize_vision",
    "deduplicate",
    "compress",
    "decompress",
]


def infer_schema(data: Any) -> "SchemaField":
    """Infer schema from data.

    Args:
        data: Data to analyze

    Returns:
        SchemaField definition
    """
    from toonverter.schema import SchemaField, SchemaInferrer

    inferrer = SchemaInferrer()
    return inferrer.infer(data)


def validate_schema(data: Any, schema: "SchemaField", strict: bool = False) -> list[str]:
    """Validate data against schema.

    Args:
        data: Data to validate
        schema: Schema definition
        strict: Strict validation mode

    Returns:
        List of error messages (empty if valid)
    """
    from toonverter.schema import SchemaField, SchemaValidator

    validator = SchemaValidator()
    return validator.validate(data, schema, strict=strict)


def diff(obj1: Any, obj2: Any) -> "DiffResult":
    """Compute difference between two objects.

    Args:
        obj1: Original object
        obj2: New object

    Returns:
        DiffResult object
    """
    from toonverter.differ import DiffResult, ToonDiffer

    differ = ToonDiffer()
    return differ.diff(obj1, obj2)


def optimize_vision(
    image_data: bytes, provider: str = "openai", return_payload: bool = False
) -> tuple[bytes, str] | dict[str, Any]:
    """Optimize image for vision models.

    Args:
        image_data: Raw image bytes
        provider: Target provider (openai, anthropic)
        return_payload: If True, returns vendor-specific dict payload instead of bytes

    Returns:
        Tuple of (optimized_bytes, mime_type) OR dict payload
    """
    from toonverter.multimodal import SmartImageProcessor, get_vendor_adapter

    processor = SmartImageProcessor()
    opt_bytes, mime = processor.process(image_data, target_provider=provider)

    if return_payload:
        adapter = get_vendor_adapter(provider)
        return adapter.format(opt_bytes, mime)

    return opt_bytes, mime


def compress(data: Any) -> dict[str, Any]:
    """Compress data using Smart Dictionary Compression.

    Args:
        data: Input data

    Returns:
        Compressed payload wrapper
    """
    from toonverter.optimization import SmartCompressor

    compressor = SmartCompressor()
    return compressor.compress(data)


def decompress(data: dict[str, Any]) -> Any:
    """Decompress SDC data.

    Args:
        data: Compressed payload wrapper

    Returns:
        Original data
    """
    from toonverter.optimization import SmartCompressor

    compressor = SmartCompressor()
    return compressor.decompress(data)


def deduplicate(
    data: Any,
    model_name: str = "all-MiniLM-L6-v2",
    threshold: float = 0.9,
    language_key: str = "language_code",
    embedding_batch_size: int = 32,
    text_extraction_func: Callable[[Any], str | None] | None = None,
    spec: ToonEncodeOptions | None = None,
) -> Any:
    """
    Detects and eliminates semantically duplicate items within lists in the data structure.

    Args:
        data: The input data structure.
        model_name: The name of the sentence transformer model to use for embeddings.
        threshold: The cosine similarity threshold above which items are considered duplicates.
        language_key: The key used to identify language-specific content, if applicable.
        embedding_batch_size: Batch size for sentence embedding generation.
        text_extraction_func: A callable that extracts a string for embedding from an item.
                              If None, a default extraction logic is used.
        spec: The TOON specification to use.

    Returns:
        The optimized data structure with duplicates removed.
    """
    if spec is None:
        spec = ToonEncodeOptions()

    deduplicator = SemanticDeduplicator(
        model_name=model_name,
        threshold=threshold,
        language_key=language_key,
        embedding_batch_size=embedding_batch_size,
        text_extraction_func=text_extraction_func,
        spec=spec,
    )
    return deduplicator.optimize(data)
