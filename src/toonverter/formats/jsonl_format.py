"""JSONL (Newline Delimited JSON) format adapter."""

import json
from typing import Any

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions

from .base import BaseFormatAdapter
from .json_format import DateTimeEncoder


class JsonlFormatAdapter(BaseFormatAdapter):
    """Adapter for JSONL/NDJSON format."""

    def __init__(self) -> None:
        """Initialize JSONL format adapter."""
        super().__init__("jsonl")

    def supports_streaming(self) -> bool:
        """Check if adapter supports streaming.

        Returns:
            True for JSONL format.
        """
        return True

    def encode(self, data: Any, _options: EncodeOptions | None = None) -> str:
        """Encode data to JSONL format.

        Expects a list of items.

        Args:
            data: Data to encode (must be a list/iterable)
            _options: Encoding options

        Returns:
            JSONL formatted string

        Raises:
            EncodingError: If encoding fails
        """
        if not isinstance(data, list):
            # If not a list, wrap it
            data = [data]

        try:
            lines = []
            for item in data:
                # JSONL lines are usually compact
                lines.append(json.dumps(item, cls=DateTimeEncoder, separators=(",", ":")))
            return "\n".join(lines)
        except (TypeError, ValueError) as e:
            msg = f"Failed to encode to JSONL: {e}"
            raise EncodingError(msg) from e

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode JSONL format to Python data.

        Args:
            data_str: JSONL format string
            options: Decoding options

        Returns:
            Decoded Python data (List of items)

        Raises:
            DecodingError: If decoding fails
        """
        try:
            result = []
            if not data_str.strip():
                return []

            for i, line in enumerate(data_str.splitlines()):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    result.append(json.loads(stripped_line))
                except json.JSONDecodeError as e:
                    if options and not options.strict:
                        continue  # Skip bad lines in non-strict mode
                    msg = f"Failed to decode JSONL line {i + 1}: {e}"
                    raise DecodingError(msg) from e
            return result
        except Exception as e:
            if isinstance(e, DecodingError):
                raise
            msg = f"Failed to decode JSONL: {e}"
            raise DecodingError(msg) from e

    def validate(self, data_str: str) -> bool:
        """Validate JSONL format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid JSONL
        """
        try:
            for line in data_str.splitlines():
                if line.strip():
                    json.loads(line)
            return True
        except json.JSONDecodeError:
            return False
