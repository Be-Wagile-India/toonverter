"""Base format adapter implementation."""

from abc import ABC
from typing import Any

from toonverter.core.interfaces import FormatAdapter
from toonverter.core.types import DecodeOptions, EncodeOptions


class BaseFormatAdapter(FormatAdapter, ABC):
    """Base class for format adapters with common functionality."""

    def __init__(self, format_name: str) -> None:
        """Initialize adapter.

        Args:
            format_name: Format identifier
        """
        self._format_name = format_name

    @property
    def format_name(self) -> str:
        """Return the format name.

        Returns:
            Format identifier string
        """
        return self._format_name

    def supports_streaming(self) -> bool:
        """Check if adapter supports streaming.

        Returns:
            False by default (override in subclasses if supported)
        """
        return False

    def _get_encode_kwargs(self, options: EncodeOptions | None) -> dict[str, Any]:
        """Convert EncodeOptions to format-specific encoding arguments.

        Args:
            options: Encoding options

        Returns:
            Dictionary of format-specific arguments
        """
        if options is None:
            return {}

        return {
            "indent": options.indent if not options.compact else None,
            "sort_keys": options.sort_keys,
            "ensure_ascii": options.ensure_ascii,
        }

    def _get_decode_kwargs(self, options: DecodeOptions | None) -> dict[str, Any]:
        """Convert DecodeOptions to format-specific decoding arguments.

        Args:
            options: Decoding options

        Returns:
            Dictionary of format-specific arguments
        """
        if options is None:
            return {}

        return {
            "strict": options.strict,
        }
