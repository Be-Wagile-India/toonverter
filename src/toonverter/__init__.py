"""TOON Converter - Token-Optimized Object Notation for LLMs.

This package provides efficient data serialization specifically designed
to reduce token usage when sending data to Large Language Models.

Quick Start:
    >>> import toon_converter as toon
    >>> data = {"name": "Alice", "age": 30}
    >>> toon_str = toon.encode(data)
    >>> decoded = toon.decode(toon_str)
"""

from typing import Any, Optional

from .__version__ import __author__, __license__, __version__
from .analysis import FormatComparator, TiktokenCounter, compare, count_tokens
from .analysis.diff import ToonDiffer, ToonDiffResult
from .async_api import async_convert, async_decode, async_encode
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
from .encoders import ToonEncoder
from .formats import register_default_formats
from .plugins import load_plugins
from .streaming import (
    StreamingDecoder,
    StreamingEncoder,
    stream_dump,
    stream_load,
)
from .utils import read_file, write_file
from .utils.async_io import async_read_file, async_write_file


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


def diff_data(data_a: Any, data_b: Any, model: str = "gpt-4") -> ToonDiffResult:
    """Compare two Python data structures for token and structural differences.

    Args:
        data_a: First data structure.
        data_b: Second data structure.
        model: Token counting model to use.

    Returns:
        ToonDiffResult with comparison details.

    Examples:
        >>> report = diff_data({'a': 1}, {'a': 2, 'b': 3})
        >>> print(report.token_diff)
    """
    differ = ToonDiffer(model)
    return differ.diff_data(data_a, data_b)


def diff_files(
    file_a_path: str,
    file_b_path: str,
    format_a: str,
    format_b: str,
    model: str = "gpt-4",
    **options: Any,
) -> ToonDiffResult:
    """Compare data from two files for token and structural differences.

    Args:
        file_a_path: Path to the first file.
        file_b_path: Path to the second file.
        format_a: Format of the first file (e.g., 'json', 'yaml').
        format_b: Format of the second file.
        model: Token counting model to use.
        **options: Decoding options passed to the underlying adapters.

    Returns:
        ToonDiffResult with comparison details.
    """
    differ = ToonDiffer(model)
    return differ.diff_files(file_a_path, file_b_path, format_a, format_b, **options)


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
    "async_convert",
    "async_decode",
    "async_encode",
    "async_read_file",
    "async_write_file",
    "ComparisonReport",
    "ConversionError",
    "ConversionResult",
    # Level 2 OOP API
    "Converter",
    "DecodeOptions",
    "Decoder",
    "DecodingError",
    # Streaming
    "StreamingEncoder",
    "StreamingDecoder",
    "stream_dump",
    "stream_load",
    # Types
    "EncodeOptions",
    "Encoder",
    "EncodingError",
    "FormatComparator",
    "FormatNotSupportedError",
    "TiktokenCounter",
    "TokenAnalysis",
    "ToonDiffer",
    "ToonDiffResult",
    "diff_data",
    "diff_files",
    # Exceptions
    "ToonConverterError",
    "ToonDecoder",
    "ToonEncoder",
    "ValidationError",
    "__author__",
    "__license__",
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
]
