"""CSV format adapter."""

import csv
import io
from typing import Any, Optional

from ..core.exceptions import DecodingError, EncodingError
from ..core.types import DecodeOptions, EncodeOptions
from .base import BaseFormatAdapter


class CsvFormatAdapter(BaseFormatAdapter):
    """Adapter for CSV format.

    CSV format is optimized for tabular data (list of dictionaries).
    """

    def __init__(self) -> None:
        """Initialize CSV format adapter."""
        super().__init__("csv")

    def encode(self, data: Any, options: Optional[EncodeOptions] = None) -> str:
        """Encode data to CSV format.

        Args:
            data: Data to encode (list of dictionaries or list of lists)
            options: Encoding options

        Returns:
            CSV formatted string

        Raises:
            EncodingError: If encoding fails or data is not tabular
        """
        if not isinstance(data, list) or not data:
            raise EncodingError("CSV format requires non-empty list data")

        delimiter = options.delimiter if options else ","

        try:
            output = io.StringIO()

            if isinstance(data[0], dict):
                # List of dictionaries
                keys = list(data[0].keys())
                if options and options.sort_keys:
                    keys = sorted(keys)

                writer = csv.DictWriter(output, fieldnames=keys, delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
            elif isinstance(data[0], (list, tuple)):
                # List of lists
                writer = csv.writer(output, delimiter=delimiter)
                writer.writerows(data)
            else:
                raise EncodingError("CSV format requires list of dictionaries or list of lists")

            return output.getvalue()
        except (TypeError, ValueError, AttributeError) as e:
            raise EncodingError(f"Failed to encode to CSV: {e}") from e

    def decode(self, data_str: str, options: Optional[DecodeOptions] = None) -> Any:
        """Decode CSV format to Python data.

        Args:
            data_str: CSV format string
            options: Decoding options

        Returns:
            List of dictionaries

        Raises:
            DecodingError: If decoding fails
        """
        delimiter = options.delimiter if options else ","

        try:
            input_io = io.StringIO(data_str)
            reader = csv.DictReader(input_io, delimiter=delimiter)
            result = list(reader)

            # Type inference for numeric values
            if options and options.type_inference:
                result = [self._infer_types(row) for row in result]

            return result
        except csv.Error as e:
            if options and not options.strict:
                return data_str
            raise DecodingError(f"Failed to decode CSV: {e}") from e

    def _infer_types(self, row: dict[str, str]) -> dict[str, Any]:
        """Infer types for CSV row values.

        Args:
            row: Dictionary with string values

        Returns:
            Dictionary with inferred types
        """
        result = {}
        for key, value in row.items():
            if not value:
                result[key] = None
            elif value.lower() in ("true", "false"):
                result[key] = value.lower() == "true"
            elif value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                result[key] = int(value)
            elif self._is_float(value):
                result[key] = float(value)
            else:
                result[key] = value
        return result

    def _is_float(self, value: str) -> bool:
        """Check if string represents a float.

        Args:
            value: String to check

        Returns:
            True if value is a valid float
        """
        try:
            float(value)
            return "." in value or "e" in value.lower()
        except ValueError:
            return False

    def validate(self, data_str: str) -> bool:
        """Validate CSV format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid CSV
        """
        try:
            input_io = io.StringIO(data_str)
            reader = csv.reader(input_io)
            list(reader)
            return True
        except csv.Error:
            return False
