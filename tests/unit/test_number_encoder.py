"""Comprehensive tests for number encoder."""

import pytest
import math
from toonverter.encoders.number_encoder import NumberEncoder


class TestNumberEncoderEncoding:
    """Test number encoding functionality."""

    def setup_method(self):
        """Set up number encoder."""
        self.encoder = NumberEncoder()

    def test_encode_positive_integer(self):
        """Test encoding positive integers."""
        assert self.encoder.encode(42) == "42"
        assert self.encoder.encode(0) == "0"
        assert self.encoder.encode(999) == "999"

    def test_encode_negative_integer(self):
        """Test encoding negative integers."""
        assert self.encoder.encode(-42) == "-42"
        assert self.encoder.encode(-1) == "-1"
        assert self.encoder.encode(-999) == "-999"

    def test_encode_zero(self):
        """Test encoding zero."""
        assert self.encoder.encode(0) == "0"
        assert self.encoder.encode(0.0) == "0"

    def test_encode_negative_zero(self):
        """Test encoding negative zero becomes positive zero."""
        assert self.encoder.encode(-0.0) == "0"

    def test_encode_float_with_decimal(self):
        """Test encoding floats with decimal parts."""
        assert self.encoder.encode(3.14) == "3.14"
        assert self.encoder.encode(2.5) == "2.5"
        assert self.encoder.encode(0.5) == "0.5"

    def test_encode_float_whole_number(self):
        """Test encoding floats that are whole numbers."""
        assert self.encoder.encode(3.0) == "3"
        assert self.encoder.encode(42.0) == "42"
        assert self.encoder.encode(-10.0) == "-10"

    def test_encode_trailing_zeros_removed(self):
        """Test trailing zeros are removed."""
        assert self.encoder.encode(3.10) == "3.1"
        assert self.encoder.encode(3.100) == "3.1"
        assert self.encoder.encode(3.1000) == "3.1"

    def test_encode_nan_becomes_null(self):
        """Test NaN becomes null."""
        assert self.encoder.encode(float('nan')) == "null"

    def test_encode_positive_infinity_becomes_null(self):
        """Test positive infinity becomes null."""
        assert self.encoder.encode(float('inf')) == "null"

    def test_encode_negative_infinity_becomes_null(self):
        """Test negative infinity becomes null."""
        assert self.encoder.encode(float('-inf')) == "null"

    def test_encode_small_decimal(self):
        """Test encoding small decimal numbers."""
        result = self.encoder.encode(0.0000123)
        assert result == "0.0000123"

    def test_encode_large_number(self):
        """Test encoding large numbers without exponent."""
        result = self.encoder.encode(10000000000.0)
        assert result == "10000000000"

    def test_encode_negative_float(self):
        """Test encoding negative floats."""
        assert self.encoder.encode(-3.14) == "-3.14"
        assert self.encoder.encode(-0.5) == "-0.5"

    def test_encode_very_small_float(self):
        """Test encoding very small float."""
        result = self.encoder.encode(1.23e-5)
        assert "e" not in result.lower()  # No exponent notation
        assert result.startswith("0.")

    def test_encode_very_large_float(self):
        """Test encoding very large float."""
        result = self.encoder.encode(1e10)
        assert "e" not in result.lower()  # No exponent notation

    def test_encode_precision_maintained(self):
        """Test precision is maintained."""
        assert self.encoder.encode(1.23456789) == "1.23456789"


class TestNumberEncoderDecoding:
    """Test number decoding functionality."""

    def setup_method(self):
        """Set up number encoder."""
        self.encoder = NumberEncoder()

    def test_decode_positive_integer(self):
        """Test decoding positive integers."""
        assert self.encoder.decode("42") == 42
        assert self.encoder.decode("0") == 0
        assert self.encoder.decode("999") == 999

    def test_decode_negative_integer(self):
        """Test decoding negative integers."""
        assert self.encoder.decode("-42") == -42
        assert self.encoder.decode("-1") == -1

    def test_decode_float(self):
        """Test decoding floats."""
        assert self.encoder.decode("3.14") == 3.14
        assert self.encoder.decode("2.5") == 2.5
        assert self.encoder.decode("0.5") == 0.5

    def test_decode_negative_float(self):
        """Test decoding negative floats."""
        assert self.encoder.decode("-3.14") == -3.14
        assert self.encoder.decode("-0.5") == -0.5

    def test_decode_exponent_notation(self):
        """Test decoding numbers in exponent notation."""
        assert self.encoder.decode("1e5") == 100000.0
        assert self.encoder.decode("1.5e2") == 150.0
        assert self.encoder.decode("1.23E-5") == 1.23e-5

    def test_decode_invalid_number_raises_error(self):
        """Test decoding invalid number raises error."""
        with pytest.raises(ValueError, match="Invalid number"):
            self.encoder.decode("not a number")

    def test_decode_empty_string_raises_error(self):
        """Test decoding empty string raises error."""
        with pytest.raises(ValueError, match="Invalid number"):
            self.encoder.decode("")

    def test_decode_returns_int_for_integers(self):
        """Test decode returns int type for integers."""
        result = self.encoder.decode("42")
        assert isinstance(result, int)
        assert result == 42

    def test_decode_returns_float_for_decimals(self):
        """Test decode returns float type for decimals."""
        result = self.encoder.decode("3.14")
        assert isinstance(result, float)
        assert result == 3.14


class TestNumberEncoderRoundtrip:
    """Test encode/decode roundtrip."""

    def setup_method(self):
        """Set up number encoder."""
        self.encoder = NumberEncoder()

    def test_roundtrip_integers(self):
        """Test roundtrip for integers."""
        for n in [0, 1, -1, 42, -42, 999, -999]:
            encoded = self.encoder.encode(n)
            decoded = self.encoder.decode(encoded)
            assert decoded == n
            assert isinstance(decoded, int)

    def test_roundtrip_floats(self):
        """Test roundtrip for floats."""
        for n in [3.14, -3.14, 0.5, -0.5, 2.5]:
            encoded = self.encoder.encode(n)
            decoded = self.encoder.decode(encoded)
            assert abs(decoded - n) < 1e-10  # Allow small floating point error

    def test_roundtrip_whole_number_floats(self):
        """Test roundtrip for floats that are whole numbers."""
        for n in [3.0, 42.0, -10.0]:
            encoded = self.encoder.encode(n)
            decoded = self.encoder.decode(encoded)
            # Encoded as integer, decoded as integer
            assert decoded == int(n)

    def test_roundtrip_zero(self):
        """Test roundtrip for zero."""
        encoded = self.encoder.encode(0)
        decoded = self.encoder.decode(encoded)
        assert decoded == 0

    def test_roundtrip_negative_zero(self):
        """Test roundtrip for negative zero."""
        encoded = self.encoder.encode(-0.0)
        assert encoded == "0"
        decoded = self.encoder.decode(encoded)
        assert decoded == 0


class TestNumberEncoderEdgeCases:
    """Test edge cases."""

    def setup_method(self):
        """Set up number encoder."""
        self.encoder = NumberEncoder()

    def test_encode_max_int(self):
        """Test encoding very large integer."""
        n = 9999999999999999
        result = self.encoder.encode(n)
        assert result == str(n)

    def test_encode_min_int(self):
        """Test encoding very large negative integer."""
        n = -9999999999999999
        result = self.encoder.encode(n)
        assert result == str(n)

    def test_format_decimal_with_many_decimals(self):
        """Test formatting decimal with many decimal places."""
        n = 3.141592653589793
        result = self.encoder.encode(n)
        assert "e" not in result.lower()
        assert result.startswith("3.14159")

    def test_format_decimal_removes_trailing_point(self):
        """Test that trailing decimal point is removed."""
        # If a number like 100.0 gets formatted, ensure no trailing .
        result = self.encoder.encode(100.0)
        assert result == "100"
        assert "." not in result

    def test_format_decimal_large_exponent(self):
        """Test formatting number with large exponent."""
        n = 1.23e20
        result = self.encoder.encode(n)
        assert "e" not in result.lower()
        assert "E" not in result

    def test_format_decimal_negative_large_exponent(self):
        """Test formatting number with large negative exponent."""
        n = 0.00001  # Small but not too small
        result = self.encoder.encode(n)
        assert result == "0.00001"
        assert "e" not in result.lower()

    def test_format_decimal_normalize_with_exponent(self):
        """Test formatting that requires normalization."""
        n = 1.0e10
        result = self.encoder.encode(n)
        assert result == "10000000000"
        assert "e" not in result.lower()

    def test_encode_formats_decimal_correctly(self):
        """Test encoding decimal formatting."""
        result = self.encoder._format_decimal(3.14159)
        assert result == "3.14159"
        assert "e" not in result.lower()
