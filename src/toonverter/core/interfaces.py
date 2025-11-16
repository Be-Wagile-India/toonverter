"""Abstract base classes and interfaces for TOON Converter.

This module defines the core interfaces following the Strategy and
Adapter patterns for extensibility and loose coupling.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from .types import DecodeOptions, EncodeOptions, TokenAnalysis


class FormatAdapter(ABC):
    """Abstract base class for format adapters.

    Format adapters implement the Strategy pattern for different
    data format conversions.
    """

    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name (e.g., 'json', 'yaml', 'toon').

        Returns:
            Format identifier string
        """
        pass

    @abstractmethod
    def encode(self, data: Any, options: Optional[EncodeOptions] = None) -> str:
        """Encode data to this format.

        Args:
            data: Data to encode (dict, list, or primitive types)
            options: Encoding configuration options

        Returns:
            String representation in this format

        Raises:
            EncodingError: If encoding fails
        """
        pass

    @abstractmethod
    def decode(self, data_str: str, options: Optional[DecodeOptions] = None) -> Any:
        """Decode data from this format.

        Args:
            data_str: String data in this format
            options: Decoding configuration options

        Returns:
            Decoded data (dict, list, or primitive types)

        Raises:
            DecodingError: If decoding fails
        """
        pass

    @abstractmethod
    def validate(self, data_str: str) -> bool:
        """Validate that string conforms to this format.

        Args:
            data_str: String to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def supports_streaming(self) -> bool:
        """Check if adapter supports streaming for large files.

        Returns:
            True if streaming is supported
        """
        return False


class TokenCounter(ABC):
    """Abstract base class for token counting implementations."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the tokenizer model name.

        Returns:
            Model identifier (e.g., 'cl100k_base', 'gpt-4')
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to analyze

        Returns:
            Number of tokens

        Raises:
            TokenCountError: If counting fails
        """
        pass

    @abstractmethod
    def analyze(self, text: str, format_name: str) -> TokenAnalysis:
        """Analyze token usage for text in given format.

        Args:
            text: Text to analyze
            format_name: Format of the text

        Returns:
            TokenAnalysis with detailed statistics

        Raises:
            TokenCountError: If analysis fails
        """
        pass


class Plugin(ABC):
    """Abstract base class for plugins.

    Plugins extend TOON Converter functionality without modifying
    the core codebase.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return plugin name.

        Returns:
            Unique plugin identifier
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Return plugin version.

        Returns:
            Version string (e.g., '1.0.0')
        """
        pass

    @abstractmethod
    def register(self, registry: "FormatRegistry") -> None:
        """Register plugin components with the registry.

        Args:
            registry: Format registry instance

        Raises:
            PluginError: If registration fails
        """
        pass

    def initialize(self) -> None:
        """Optional initialization hook called after registration."""
        pass

    def cleanup(self) -> None:
        """Optional cleanup hook called on shutdown."""
        pass


class FormatRegistry(ABC):
    """Abstract base class for format adapter registry.

    Implements the Factory pattern for creating format adapters.
    """

    @abstractmethod
    def register(self, format_name: str, adapter: FormatAdapter) -> None:
        """Register a format adapter.

        Args:
            format_name: Format identifier
            adapter: FormatAdapter instance

        Raises:
            ValueError: If format already registered
        """
        pass

    @abstractmethod
    def get(self, format_name: str) -> FormatAdapter:
        """Retrieve format adapter by name.

        Args:
            format_name: Format identifier

        Returns:
            FormatAdapter instance

        Raises:
            FormatNotSupportedError: If format not found
        """
        pass

    @abstractmethod
    def unregister(self, format_name: str) -> None:
        """Unregister a format adapter.

        Args:
            format_name: Format identifier

        Raises:
            FormatNotSupportedError: If format not found
        """
        pass

    @abstractmethod
    def list_formats(self) -> list[str]:
        """List all registered format names.

        Returns:
            List of format identifiers
        """
        pass

    @abstractmethod
    def is_supported(self, format_name: str) -> bool:
        """Check if format is supported.

        Args:
            format_name: Format identifier

        Returns:
            True if format is registered
        """
        pass
