"""TOON v2.0 Specification Compliance Tests.

Tests that the encoder and decoder strictly follow the official TOON v2.0 spec
from https://github.com/toon-format/spec
"""

from unittest.mock import patch

import pytest

from toonverter.core import config  # Import config to access _RUST_AVAILABLE
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


# --- Fixtures for backend selection ---


@pytest.fixture(params=["python", "rust"])
def decoder_backend(request):
    """Fixture to provide a ToonDecoder configured for a specific backend (Python or Rust)."""
    if request.param == "python":
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", False),
            patch("toonverter.decoders.toon_decoder.rust_core", None),
        ):
            yield ToonDecoder()
    elif request.param == "rust":
        if not config._RUST_AVAILABLE:
            pytest.skip("Rust extension not available for Rust backend tests.")
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", True),
            patch("toonverter.decoders.toon_decoder.rust_core", config.rust_core),
        ):
            yield ToonDecoder()


@pytest.fixture(params=["python", "rust"])
def encoder_backend(request):
    """Fixture to provide a ToonEncoder configured for a specific backend (Python or Rust)."""
    if request.param == "python":
        with (
            patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False),
            patch("toonverter.encoders.toon_encoder.rust_core", None),
        ):  # Force Python fallback
            yield ToonEncoder()
    elif request.param == "rust":
        if not config._RUST_AVAILABLE:
            pytest.skip("Rust extension not available for Rust backend tests.")
        with (
            patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", True),
            patch("toonverter.encoders.toon_encoder.rust_core", config.rust_core),
        ):  # Ensure Rust is used
            yield ToonEncoder()


class TestEmptyDocuments:
    """Test empty document handling per spec."""

    def test_empty_string_decodes_to_empty_dict(self, decoder_backend):
        """Empty documents must decode to {}."""
        assert decoder_backend.decode("") == {}

    def test_whitespace_only_decodes_to_empty_dict(self, decoder_backend):
        """Whitespace-only documents must decode to {}."""
        assert decoder_backend.decode("   ") == {}
        assert decoder_backend.decode("\n\n\n") == {}
        assert decoder_backend.decode("  \n  \n  ") == {}
        assert decoder_backend.decode("\t\t") == {}


class TestRootForms:
    """Test the three root document forms."""

    def test_root_object_form(self, encoder_backend, decoder_backend):
        """Test root-level object (default form)."""
        data = {"name": "Alice", "age": 30}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert isinstance(decoded, dict)

    def test_root_array_form(self, encoder_backend, decoder_backend):
        """Test root-level array form."""
        data = [1, 2, 3, 4, 5]
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert isinstance(decoded, list)

    def test_root_primitive_form(self, decoder_backend):
        """Test root-level primitive form."""
        # Test various primitives
        assert decoder_backend.decode("42") == 42
        assert decoder_backend.decode("3.14") == 3.14
        assert decoder_backend.decode("true") is True  # Fixed: should be `is True`
        assert decoder_backend.decode("false") is False  # Fixed: should be `is False`
        assert decoder_backend.decode("null") is None
        assert decoder_backend.decode("hello") == "hello"


class TestArrayForms:
    """Test the three array forms: inline, tabular, list."""

    def test_inline_array_form(self, encoder_backend, decoder_backend):
        """Test inline array: [N]: val1,val2,val3."""
        data = {"numbers": [1, 2, 3, 4, 5]}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert "[5]:" in toon  # Inline form

    def test_tabular_array_form(self, encoder_backend, decoder_backend):
        """Test tabular array: [N]{fields}: with data rows."""
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
                {"name": "Carol", "age": 35},
            ]
        }
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        # Note: Order of fields might not be guaranteed in string representation due to dict.
        # But for spec compliance, both {name,age} and {age,name} should be fine.
        # We can do a more robust check if needed, but for now, this is fine.
        assert "{name,age}" in toon or "{age,name}" in toon  # Tabular form

    def test_list_array_form(self, encoder_backend, decoder_backend):
        """Test list array: [N]: with - items."""
        # Mixed types force list form
        data = {"items": [1, "hello", True, None, {"nested": "object"}]}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert "- " in toon  # List form marker

    def test_empty_array(self, encoder_backend, decoder_backend):
        """Test empty array encoding."""
        data = {"empty": []}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert "[0]:" in toon


class TestPrimitiveTypes:
    """Test all primitive types."""

    def test_null_encoding(self, encoder_backend, decoder_backend):
        """Test null encoding."""
        data = {"value": None}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data
        assert "null" in toon

    def test_boolean_encoding(self, encoder_backend, decoder_backend):
        """Test boolean encoding."""
        data_true = {"flag": True}
        data_false = {"flag": False}

        toon_true = encoder_backend.encode(data_true)
        toon_false = encoder_backend.encode(data_false)

        assert decoder_backend.decode(toon_true) == data_true
        assert decoder_backend.decode(toon_false) == data_false
        assert "true" in toon_true
        assert "false" in toon_false

    def test_integer_encoding(self, encoder_backend, decoder_backend):
        """Test integer encoding."""
        test_cases = [0, 1, -1, 42, -999, 1000000]

        for num in test_cases:
            data = {"num": num}
            toon = encoder_backend.encode(data)
            decoded = decoder_backend.decode(toon)
            assert decoded == data

    def test_float_encoding(self, encoder_backend, decoder_backend):
        """Test float encoding."""
        test_cases = [0.0, 3.14, -2.5, 0.123456]

        for num in test_cases:
            data = {"num": num}
            toon = encoder_backend.encode(data)
            decoded = decoder_backend.decode(toon)
            # Use approximate comparison for floats
            assert abs(decoded["num"] - num) < 0.0001

    def test_string_encoding(self, encoder_backend, decoder_backend):
        """Test string encoding."""
        test_strings = [
            "hello",
            "Hello World",
            "with spaces",
            "123",  # Number-like string
            "true",  # Boolean-like string
            "",  # Empty string
        ]

        for s in test_strings:
            data = {"text": s}
            toon = encoder_backend.encode(data)
            decoded = decoder_backend.decode(toon)
            assert decoded == data


class TestQuotedPrimitives:
    """Test that quoted primitives remain strings per spec."""

    def test_quoted_number_stays_string(self, decoder_backend):
        """Quoted numbers like "123" must remain strings."""
        # Manually create TOON with quoted number
        toon = 'value: "123"'
        decoded = decoder_backend.decode(toon)

        assert decoded == {"value": "123"}
        assert isinstance(decoded["value"], str)

    def test_quoted_boolean_stays_string(self, decoder_backend):
        """Quoted booleans like "true" must remain strings."""
        toon_true = 'flag: "true"'
        toon_false = 'flag: "false"'

        assert decoder_backend.decode(toon_true) == {"flag": "true"}
        assert decoder_backend.decode(toon_false) == {"flag": "false"}
        assert isinstance(decoder_backend.decode(toon_true)["flag"], str)

    def test_quoted_null_stays_string(self, decoder_backend):
        """Quoted null like "null" must remain a string."""
        toon = 'value: "null"'
        decoded = decoder_backend.decode(toon)

        assert decoded == {"value": "null"}
        assert isinstance(decoded["value"], str)


class TestNestedStructures:
    """Test nested objects and arrays."""

    def test_deeply_nested_objects(self, encoder_backend, decoder_backend):
        """Test multiple levels of object nesting."""
        data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}

        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data

    def test_nested_arrays(self, encoder_backend, decoder_backend):
        """Test nested arrays."""
        data = {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}

        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data

    def test_mixed_nesting(self, encoder_backend, decoder_backend):
        """Test mixed nesting of objects and arrays."""
        data = {
            "users": [
                {
                    "name": "Alice",
                    "roles": ["admin", "user"],
                    "metadata": {"created": "2024-01-01", "active": True},
                },
                {
                    "name": "Bob",
                    "roles": ["user"],
                    "metadata": {"created": "2024-01-02", "active": False},
                },
            ]
        }

        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data


class TestRoundtripConsistency:
    """Test that encode->decode->encode produces consistent results."""

    def test_simple_object_roundtrip(self, encoder_backend, decoder_backend):
        """Test roundtrip consistency for simple objects."""
        original = {"name": "Alice", "age": 30, "active": True}

        # First roundtrip
        toon1 = encoder_backend.encode(original)
        decoded1 = decoder_backend.decode(toon1)
        assert decoded1 == original

        # Second roundtrip
        toon2 = encoder_backend.encode(decoded1)
        decoded2 = decoder_backend.decode(toon2)
        assert decoded2 == original

        # Encoded forms should be identical
        assert toon1 == toon2

    def test_complex_structure_roundtrip(self, encoder_backend, decoder_backend):
        """Test roundtrip consistency for complex structures."""
        original = {
            "users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            "metadata": {"count": 2, "active": True},
            "tags": ["python", "toon", "encoding"],
        }

        # Multiple roundtrips
        current = original
        for _ in range(3):
            toon = encoder_backend.encode(current)
            current = decoder_backend.decode(toon)

        assert current == original


class TestSpecEdgeCases:
    """Test edge cases defined in spec."""

    def test_zero_handling(self, encoder_backend, decoder_backend):
        """Test zero and negative zero."""
        # Regular zero
        data = {"num": 0}
        toon = encoder_backend.encode(data)
        assert decoder_backend.decode(toon) == data
        assert toon == "num: 0"

        # Negative zero should become 0
        data_neg_zero = {"num": -0.0}
        toon_neg_zero = encoder_backend.encode(data_neg_zero)
        assert "num: 0" in toon_neg_zero
        assert decoder_backend.decode(toon_neg_zero)["num"] == 0

    def test_special_float_values(self, encoder_backend, decoder_backend):
        """Test NaN and Infinity handling."""
        # NaN should become null
        data_nan = {"value": float("nan")}
        toon_nan = encoder_backend.encode(data_nan)
        assert "null" in toon_nan
        assert decoder_backend.decode(toon_nan)["value"] is None

        # Infinity should become null
        data_inf = {"value": float("inf")}
        toon_inf = encoder_backend.encode(data_inf)
        assert "null" in toon_inf
        assert decoder_backend.decode(toon_inf)["value"] is None

        # Negative infinity should become null
        data_neg_inf = {"value": float("-inf")}
        toon_neg_inf = encoder_backend.encode(data_neg_inf)
        assert "null" in toon_neg_inf
        assert decoder_backend.decode(toon_neg_inf)["value"] is None

    def test_empty_string_value(self, encoder_backend, decoder_backend):
        """Test empty string as value."""
        data = {"text": ""}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data

    def test_empty_object(self, encoder_backend, decoder_backend):
        """Test empty object encoding."""
        data = {}
        toon = encoder_backend.encode(data)
        decoded = decoder_backend.decode(toon)

        assert decoded == data

    def test_comments_handling(self, decoder_backend):
        """Test that single-line comments are ignored by the decoder."""
        # Full line comment
        toon1 = "# This is a comment\nkey: value"
        assert decoder_backend.decode(toon1) == {"key": "value"}

        # Inline comment
        toon2 = "key: value # inline comment"
        assert decoder_backend.decode(toon2) == {"key": "value"}

        # Multiple comments
        toon3 = "# Comment 1\nkey: value\n# Comment 2\n"
        assert decoder_backend.decode(toon3) == {"key": "value"}

        # Comment with leading whitespace
        toon4 = "  # indented comment\nkey: value"
        assert decoder_backend.decode(toon4) == {"key": "value"}

        # Empty line with comment
        toon5 = "key: value\n\n# another comment\nkey2: value2"
        assert decoder_backend.decode(toon5) == {"key": "value", "key2": "value2"}

    def test_whitespace_tolerance(self, decoder_backend):
        """Test decoder tolerance for various whitespace scenarios."""
        # Multiple spaces between key and colon
        toon1 = "key   : value"
        assert decoder_backend.decode(toon1) == {"key": "value"}

        # Multiple spaces after colon and before value
        toon2 = "key:   value"
        assert decoder_backend.decode(toon2) == {"key": "value"}

        # Mixed spaces and tabs (should error if tabs used for indent, but tolerated otherwise)
        # Note: Lexer already errors on tabs for indentation, so this tests inline tabs
        toon3 = "key: \t value"
        assert decoder_backend.decode(toon3) == {"key": "value"}

        # Trailing whitespace on a line
        toon4 = "key: value   \nkey2: value2"
        assert decoder_backend.decode(toon4) == {"key": "value", "key2": "value2"}

        # Values with leading/trailing spaces (should be preserved if quoted, trimmed if unquoted and primitive)
        toon5 = 'key: "  value  "'
        assert decoder_backend.decode(toon5) == {"key": "  value  "}

        toon6 = "key:   value_with_spaces_at_ends  "  # Unquoted, spaces should be trimmed
        assert decoder_backend.decode(toon6) == {"key": "value_with_spaces_at_ends"}

    def test_escape_sequences(self, decoder_backend):
        """Test handling of various escape sequences in strings."""
        # Common escapes
        toon1 = 'text: "hello\\nworld\\t\\""'
        assert decoder_backend.decode(toon1) == {"text": 'hello\nworld\t"'}

        # Backslash itself
        toon2 = 'path: "C:\\\\Users\\\\Name"'
        assert decoder_backend.decode(toon2) == {"path": "C:\\Users\\Name"}

        # Unicode escapes (if supported by TOON spec) - assuming standard JSON-like \uXXXX
        # TOON spec does not explicitly mention Unicode escapes in the provided context,
        # so this might pass through as literal or error. For now, test as literal.
        toon3 = 'unicode: " café "'  # direct unicode chars are fine, no escape needed
        assert decoder_backend.decode(toon3) == {"unicode": " café "}

        # Invalid escape sequence should raise an error
        from toonverter.core.exceptions import (
            DecodingError,
        )  # Assuming this is the correct exception

        with pytest.raises(DecodingError, match="Invalid escape"):
            decoder_backend.decode('bad: "hello\\xworld"')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
