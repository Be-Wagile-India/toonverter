"""JSON format adapter."""

import json
from datetime import date, datetime
from typing import Any, Optional

from ..core.exceptions import DecodingError, EncodingError
from ..core.types import DecodeOptions, EncodeOptions
from .base import BaseFormatAdapter


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj: Any) -> Any:
        """Encode datetime objects to ISO format.

        Args:
            obj: Object to encode

        Returns:
            ISO format string for datetime/date, default encoding otherwise
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class JsonFormatAdapter(BaseFormatAdapter):
    """Adapter for JSON format."""

    def __init__(self) -> None:
        """Initialize JSON format adapter."""
        super().__init__("json")

    def encode(self, data: Any, options: Optional[EncodeOptions] = None) -> str:
        """Encode data to JSON format.

        Args:
            data: Data to encode
            options: Encoding options

        Returns:
            JSON formatted string

        Raises:
            EncodingError: If encoding fails
        """
        try:
            kwargs = self._get_encode_kwargs(options) if options else {}
            # Handle compact mode
            if options and options.compact:
                kwargs["separators"] = (",", ":")
                kwargs["indent"] = None

            return json.dumps(data, cls=DateTimeEncoder, **kwargs)
        except (TypeError, ValueError) as e:
            raise EncodingError(f"Failed to encode to JSON: {e}") from e

    def decode(self, data_str: str, options: Optional[DecodeOptions] = None) -> Any:
        """Decode JSON format to Python data.

        Args:
            data_str: JSON format string
            options: Decoding options

        Returns:
            Decoded Python data

        Raises:
            DecodingError: If decoding fails
        """
        try:
            return json.loads(data_str)
        except json.JSONDecodeError as e:
            if options and not options.strict:
                return data_str
            raise DecodingError(f"Failed to decode JSON: {e}") from e

    def validate(self, data_str: str) -> bool:
        """Validate JSON format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid JSON
        """
        try:
            json.loads(data_str)
            return True
        except json.JSONDecodeError:
            return False
