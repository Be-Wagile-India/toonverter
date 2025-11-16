"""YAML format adapter."""

from typing import Any, Optional

from ..core.exceptions import DecodingError, EncodingError
from ..core.types import DecodeOptions, EncodeOptions
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
            raise ImportError(
                "PyYAML is required for YAML support. "
                "Install with: pip install toon-converter[formats]"
            )

    def encode(self, data: Any, options: Optional[EncodeOptions] = None) -> str:
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
            kwargs = {}
            if options:
                kwargs["default_flow_style"] = options.compact
                kwargs["sort_keys"] = options.sort_keys
                kwargs["allow_unicode"] = not options.ensure_ascii

            return yaml.dump(data, **kwargs)
        except yaml.YAMLError as e:
            raise EncodingError(f"Failed to encode to YAML: {e}") from e

    def decode(self, data_str: str, options: Optional[DecodeOptions] = None) -> Any:
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
            raise DecodingError(f"Failed to decode YAML: {e}") from e

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
