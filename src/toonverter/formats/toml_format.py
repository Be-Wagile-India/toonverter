"""TOML format adapter."""

import sys
from typing import Any

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions

from .base import BaseFormatAdapter


# Python 3.11+ has tomllib built-in, earlier versions need toml package
if sys.version_info >= (3, 11):
    import tomllib

    try:
        import tomli_w

        TOML_WRITE_AVAILABLE = True
    except ImportError:
        TOML_WRITE_AVAILABLE = False
    TOML_READ_AVAILABLE = True
else:
    try:
        import toml

        TOML_READ_AVAILABLE = True
        TOML_WRITE_AVAILABLE = True
        tomllib = toml  # type: ignore
        tomli_w = toml  # type: ignore
    except ImportError:
        TOML_READ_AVAILABLE = False
        TOML_WRITE_AVAILABLE = False


class TomlFormatAdapter(BaseFormatAdapter):
    """Adapter for TOML format.

    Python 3.11+: Uses built-in tomllib for reading, requires tomli-w for writing
    Python <3.11: Requires toml package
    """

    def __init__(self) -> None:
        """Initialize TOML format adapter."""
        super().__init__("toml")
        if not TOML_READ_AVAILABLE:
            msg = (
                "TOML support requires 'toml' package on Python <3.11. "
                "Install with: pip install toon-converter[formats]"
            )
            raise ImportError(msg)

    def encode(self, data: Any, options: EncodeOptions | None = None) -> str:
        """Encode data to TOML format.

        Args:
            data: Data to encode (must be a dictionary)
            options: Encoding options

        Returns:
            TOML formatted string

        Raises:
            EncodingError: If encoding fails
        """
        if not isinstance(data, dict):
            msg = "TOML format only supports dictionary data at the top level"
            raise EncodingError(msg)

        if not TOML_WRITE_AVAILABLE:
            msg = (
                "TOML writing requires 'toml' package (Python <3.11) or "
                "'tomli-w' package (Python 3.11+). "
                "Install with: pip install toon-converter[formats]"
            )
            raise EncodingError(msg)

        try:
            if sys.version_info >= (3, 11):
                return tomli_w.dumps(data)
            return toml.dumps(data)  # type: ignore
        except Exception as e:
            msg = f"Failed to encode to TOML: {e}"
            raise EncodingError(msg) from e

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode TOML format to Python data.

        Args:
            data_str: TOML format string
            options: Decoding options

        Returns:
            Decoded Python dictionary

        Raises:
            DecodingError: If decoding fails
        """
        try:
            if sys.version_info >= (3, 11):
                return tomllib.loads(data_str)
            return toml.loads(data_str)  # type: ignore
        except Exception as e:
            if options and not options.strict:
                return data_str
            msg = f"Failed to decode TOML: {e}"
            raise DecodingError(msg) from e

    def validate(self, data_str: str) -> bool:
        """Validate TOML format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid TOML
        """
        try:
            if sys.version_info >= (3, 11):
                tomllib.loads(data_str)
            else:
                toml.loads(data_str)  # type: ignore
            return True
        except Exception:
            return False
