"""YAML format adapter."""

from typing import Any

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions

from .base import BaseFormatAdapter


# Optional dependency
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class YamlFormatAdapter(BaseFormatAdapter):
    """Adapter for YAML format.

    Requires PyYAML package to be installed.
    """

    def __init__(self) -> None:
        """Initialize YAML format adapter."""
        super().__init__("yaml")
        if not YAML_AVAILABLE:
            msg = (
                "PyYAML is required for YAML support. "
                "Install with: pip install toon-converter[formats]"
            )
            raise ImportError(msg)

    def encode(self, data: Any, options: EncodeOptions | None = None) -> str:
        """Encode data to YAML format.

        Args:
            data: Data to encode
            options: Encoding options

        Returns:
            YAML formatted string

        Raises:
            EncodingError: If encoding fails
        """
        try:
            _kwargs: dict[str, Any] = {}
            if options:
                if options.compact is not None:
                    _kwargs["default_flow_style"] = options.compact
                if options.sort_keys is not None:
                    _kwargs["sort_keys"] = options.sort_keys
                if options.ensure_ascii is not None:
                    _kwargs["allow_unicode"] = not options.ensure_ascii

            return yaml.dump(data, stream=None, **_kwargs)
        except yaml.YAMLError as e:
            msg = f"Failed to encode to YAML: {e}"
            raise EncodingError(msg) from e

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode YAML format to Python data.

        Args:
            data_str: YAML format string
            options: Decoding options

        Returns:
            Decoded Python data

        Raises:
            DecodingError: If decoding fails
        """
        try:
            return yaml.safe_load(data_str)
        except yaml.YAMLError as e:
            if options and not options.strict:
                return data_str
            msg = f"Failed to decode YAML: {e}"
            raise DecodingError(msg) from e

    def validate(self, data_str: str) -> bool:
        """Validate YAML format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid YAML
        """
        try:
            yaml.safe_load(data_str)
            return True
        except yaml.YAMLError:
            return False
