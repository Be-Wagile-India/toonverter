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
    # Exceptions
    "ToonConverterError",
    "ConversionError",
    "EncodingError",
    "DecodingError",
    "ValidationError",
    "FormatNotSupportedError",
    "PluginError",
    "TokenCountError",
    "FileOperationError",
    # Interfaces
    "FormatAdapter",
    "TokenCounter",
    "Plugin",
    "FormatRegistry",
    # Registry
    "registry",
    "get_registry",
    "DefaultFormatRegistry",
    # Types
    "EncodeOptions",
    "DecodeOptions",
    "ConversionResult",
    "TokenAnalysis",
    "ComparisonReport",
    "ToonData",
    "FormatName",
]
