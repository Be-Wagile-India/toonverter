"""Number encoding with canonical form per TOON specification.

The TOON spec requires numbers in canonical decimal form:
- No leading zeros (except "0" itself)
- No trailing zeros after decimal point
- No exponent notation in output
- -0 becomes 0
- NaN and Infinity become null
"""

import math
from decimal import Decimal, InvalidOperation


class NumberEncoder:
    """Encoder for numbers in canonical TOON format."""

    def encode(self, n: int | float) -> str:
        """Encode number to canonical form per TOON spec.

        Args:
            n: Number to encode

        Returns:
            Canonical number string or "null" for special values

        Examples:
            >>> encoder = NumberEncoder()
            >>> encoder.encode(42)
            '42'
            >>> encoder.encode(3.14)
            '3.14'
            >>> encoder.encode(3.0)
            '3'
            >>> encoder.encode(-0.0)
            '0'
            >>> encoder.encode(float('nan'))
            'null'
        """
        # Handle special float values -> null
        if isinstance(n, float):
            if math.isnan(n) or math.isinf(n):
                return "null"

        # Handle negative zero -> 0
        if n == 0:
            # Check for negative zero
            if isinstance(n, float) and math.copysign(1.0, n) == -1.0:
                return "0"
            return "0"

        # Integer (or float that's a whole number)
        if isinstance(n, int) or (isinstance(n, float) and n.is_integer()):
            return str(int(n))

        # Float with decimal part
        return self._format_decimal(n)

    def _format_decimal(self, n: float) -> str:
        """Format float in canonical decimal form.

        Args:
            n: Float to format

        Returns:
            Canonical decimal string without exponent or trailing zeros

        Examples:
            >>> encoder = NumberEncoder()
            >>> encoder._format_decimal(3.14)
            '3.14'
            >>> encoder._format_decimal(3.10)
            '3.1'
            >>> encoder._format_decimal(1e10)
            '10000000000'
            >>> encoder._format_decimal(1.23e-5)
            '0.0000123'
        """
        try:
            # Use Decimal for precise control over formatting
            d = Decimal(str(n))

            # Check if in exponential form
            d_str = str(d)
            if "E" in d_str or "e" in d_str:
                # Normalize to remove exponent
                # This converts 1.23e-5 -> 0.0000123
                d = d.normalize()

                # If normalize still has exponent, use quantize
                if "E" in str(d):
                    # Get exponent
                    d_str = f"{d:.20f}"  # Format with enough precision
                    d = Decimal(d_str)

            # Remove trailing zeros after decimal point
            result = str(d)

            # Strip trailing zeros and trailing decimal point
            if "." in result:
                result = result.rstrip("0").rstrip(".")

            return result if result and result != "-" else "0"

        except (ValueError, InvalidOperation):
            # Fallback for edge cases
            # Format with reasonable precision
            result = f"{n:.15f}"

            # Remove trailing zeros
            if "." in result:
                result = result.rstrip("0").rstrip(".")

            return result

    def decode(self, s: str) -> int | float:
        """Decode number from string.

        Args:
            s: Number string

        Returns:
            Parsed number (int or float)

        Raises:
            ValueError: If string is not a valid number

        Examples:
            >>> encoder = NumberEncoder()
            >>> encoder.decode("42")
            42
            >>> encoder.decode("3.14")
            3.14
            >>> encoder.decode("-5")
            -5
        """
        # Try integer first
        if "." not in s and "e" not in s.lower():
            try:
                return int(s)
            except ValueError:
                pass

        # Try float
        try:
            return float(s)
        except ValueError as e:
            raise ValueError(f"Invalid number: {s}") from e
