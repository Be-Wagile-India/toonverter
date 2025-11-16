"""TOON format adapter."""

from typing import Any

from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.decoders import decode as toon_decode
from toonverter.encoders import encode as toon_encode

from .base import BaseFormatAdapter


class ToonFormatAdapter(BaseFormatAdapter):
    """Adapter for TOON (Token-Optimized Object Notation) format."""

    def __init__(self) -> None:
        """Initialize TOON format adapter."""
        super().__init__("toon")

    def encode(self, data: Any, options: EncodeOptions | None = None) -> str:
        """Encode data to TOON format.

        Args:
            data: Data to encode
            options: Encoding options

        Returns:
            TOON formatted string
        """
        return toon_encode(data, options)

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode TOON format to Python data.

        Args:
            data_str: TOON format string
            options: Decoding options

        Returns:
            Decoded Python data
        """
        return toon_decode(data_str, options)

    def validate(self, data_str: str) -> bool:
        """Validate TOON format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid TOON format
        """
        try:
            toon_decode(data_str)
            return True
        except Exception:
            return False
