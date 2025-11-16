"""Core module for TOON Converter.

This module contains the fundamental interfaces, types, and registry
following SOLID principles and clean architecture.
"""

from .exceptions import (
    ConversionError,
    DecodingError,
    EncodingError,
    FileOperationError,
    FormatNotSupportedError,
    PluginError,
    TokenCountError,
    ToonConverterError,
    ValidationError,
)
from .interfaces import FormatAdapter, FormatRegistry, Plugin, TokenCounter
from .registry import DefaultFormatRegistry, get_registry, registry
from .types import (
    ComparisonReport,
    ConversionResult,
    DecodeOptions,
    EncodeOptions,
    FormatName,
    TokenAnalysis,
    ToonData,
)


__all__ = [
    "ComparisonReport",
    "ConversionError",
    "ConversionResult",
    "DecodeOptions",
    "DecodingError",
    "DefaultFormatRegistry",
    # Types
    "EncodeOptions",
    "EncodingError",
    "FileOperationError",
    # Interfaces
    "FormatAdapter",
    "FormatName",
    "FormatNotSupportedError",
    "FormatRegistry",
    "Plugin",
    "PluginError",
    "TokenAnalysis",
    "TokenCountError",
    "TokenCounter",
    # Exceptions
    "ToonConverterError",
    "ToonData",
    "ValidationError",
    "get_registry",
    # Registry
    "registry",
]
