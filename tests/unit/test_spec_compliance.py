"""TOON v2.0 Specification Compliance Tests.

Tests that the encoder and decoder strictly follow the official TOON v2.0 spec
from https://github.com/toon-format/spec
"""

import pytest

from src.toonverter.decoders.toon_decoder import ToonDecoder
from src.toonverter.encoders.toon_encoder import ToonEncoder
from src.toonverter.core.spec import ToonDecodeOptions, ToonEncodeOptions


class TestEmptyDocuments:
    """Test empty document handling per spec."""

    def test_empty_string_decodes_to_empty_dict(self):
        """Empty documents must decode to {}."""
        decoder = ToonDecoder()
        assert decoder.decode("") == {}

    def test_whitespace_only_decodes_to_empty_dict(self):
        """Whitespace-only documents must decode to {}."""
        decoder = ToonDecoder()
        assert decoder.decode("   ") == {}
        assert decoder.decode("\n\n\n") == {}
        assert decoder.decode("  \n  \n  ") == {}
        assert decoder.decode("\t\t") == {}


class TestRootForms:
    """Test the three root document forms."""

    def test_root_object_form(self):
        """Test root-level object (default form)."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {"name": "Alice", "age": 30}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert isinstance(decoded, dict)

    def test_root_array_form(self):
        """Test root-level array form."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = [1, 2, 3, 4, 5]
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert isinstance(decoded, list)

    def test_root_primitive_form(self):
        """Test root-level primitive form."""
        decoder = ToonDecoder()

        # Test various primitives
        assert decoder.decode("42") == 42
        assert decoder.decode("3.14") == 3.14
        assert decoder.decode("true") == True
        assert decoder.decode("false") == False
        assert decoder.decode("null") is None
        assert decoder.decode("hello") == "hello"


class TestArrayForms:
    """Test the three array forms: inline, tabular, list."""

    def test_inline_array_form(self):
        """Test inline array: [N]: val1,val2,val3."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {"numbers": [1, 2, 3, 4, 5]}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert "[5]:" in toon  # Inline form

    def test_tabular_array_form(self):
        """Test tabular array: [N]{fields}: with data rows."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
                {"name": "Carol", "age": 35}
            ]
        }
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert "{name,age}" in toon or "{age,name}" in toon  # Tabular form

    def test_list_array_form(self):
        """Test list array: [N]: with - items."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Mixed types force list form
        data = {"items": [1, "hello", True, None, {"nested": "object"}]}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert "- " in toon  # List form marker

    def test_empty_array(self):
        """Test empty array encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {"empty": []}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert "[0]:" in toon


class TestPrimitiveTypes:
    """Test all primitive types."""

    def test_null_encoding(self):
        """Test null encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {"value": None}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data
        assert "null" in toon

    def test_boolean_encoding(self):
        """Test boolean encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data_true = {"flag": True}
        data_false = {"flag": False}

        toon_true = encoder.encode(data_true)
        toon_false = encoder.encode(data_false)

        assert decoder.decode(toon_true) == data_true
        assert decoder.decode(toon_false) == data_false
        assert "true" in toon_true
        assert "false" in toon_false

    def test_integer_encoding(self):
        """Test integer encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        test_cases = [0, 1, -1, 42, -999, 1000000]

        for num in test_cases:
            data = {"num": num}
            toon = encoder.encode(data)
            decoded = decoder.decode(toon)
            assert decoded == data

    def test_float_encoding(self):
        """Test float encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        test_cases = [0.0, 3.14, -2.5, 0.123456]

        for num in test_cases:
            data = {"num": num}
            toon = encoder.encode(data)
            decoded = decoder.decode(toon)
            # Use approximate comparison for floats
            assert abs(decoded["num"] - num) < 0.0001

    def test_string_encoding(self):
        """Test string encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

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
            toon = encoder.encode(data)
            decoded = decoder.decode(toon)
            assert decoded == data


class TestQuotedPrimitives:
    """Test that quoted primitives remain strings per spec."""

    def test_quoted_number_stays_string(self):
        """Quoted numbers like "123" must remain strings."""
        decoder = ToonDecoder()

        # Manually create TOON with quoted number
        toon = 'value: "123"'
        decoded = decoder.decode(toon)

        assert decoded == {"value": "123"}
        assert isinstance(decoded["value"], str)

    def test_quoted_boolean_stays_string(self):
        """Quoted booleans like "true" must remain strings."""
        decoder = ToonDecoder()

        toon_true = 'flag: "true"'
        toon_false = 'flag: "false"'

        assert decoder.decode(toon_true) == {"flag": "true"}
        assert decoder.decode(toon_false) == {"flag": "false"}
        assert isinstance(decoder.decode(toon_true)["flag"], str)

    def test_quoted_null_stays_string(self):
        """Quoted null like "null" must remain a string."""
        decoder = ToonDecoder()

        toon = 'value: "null"'
        decoded = decoder.decode(toon)

        assert decoded == {"value": "null"}
        assert isinstance(decoded["value"], str)


class TestNestedStructures:
    """Test nested objects and arrays."""

    def test_deeply_nested_objects(self):
        """Test multiple levels of object nesting."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep"
                        }
                    }
                }
            }
        }

        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data

    def test_nested_arrays(self):
        """Test nested arrays."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {
            "matrix": [
                [1, 2, 3],
                [4, 5, 6],
                [7, 8, 9]
            ]
        }

        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data

    def test_mixed_nesting(self):
        """Test mixed nesting of objects and arrays."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {
            "users": [
                {
                    "name": "Alice",
                    "roles": ["admin", "user"],
                    "metadata": {
                        "created": "2024-01-01",
                        "active": True
                    }
                },
                {
                    "name": "Bob",
                    "roles": ["user"],
                    "metadata": {
                        "created": "2024-01-02",
                        "active": False
                    }
                }
            ]
        }

        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data


class TestRoundtripConsistency:
    """Test that encode->decode->encode produces consistent results."""

    def test_simple_object_roundtrip(self):
        """Test roundtrip consistency for simple objects."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        original = {"name": "Alice", "age": 30, "active": True}

        # First roundtrip
        toon1 = encoder.encode(original)
        decoded1 = decoder.decode(toon1)
        assert decoded1 == original

        # Second roundtrip
        toon2 = encoder.encode(decoded1)
        decoded2 = decoder.decode(toon2)
        assert decoded2 == original

        # Encoded forms should be identical
        assert toon1 == toon2

    def test_complex_structure_roundtrip(self):
        """Test roundtrip consistency for complex structures."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        original = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            "metadata": {
                "count": 2,
                "active": True
            },
            "tags": ["python", "toon", "encoding"]
        }

        # Multiple roundtrips
        current = original
        for _ in range(3):
            toon = encoder.encode(current)
            current = decoder.decode(toon)

        assert current == original


class TestSpecEdgeCases:
    """Test edge cases defined in spec."""

    def test_zero_handling(self):
        """Test zero and negative zero."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Regular zero
        data = {"num": 0}
        toon = encoder.encode(data)
        assert decoder.decode(toon) == data
        assert toon == "num: 0"

        # Negative zero should become 0
        data_neg_zero = {"num": -0.0}
        toon_neg_zero = encoder.encode(data_neg_zero)
        assert "num: 0" in toon_neg_zero
        assert decoder.decode(toon_neg_zero)["num"] == 0

    def test_special_float_values(self):
        """Test NaN and Infinity handling."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # NaN should become null
        data_nan = {"value": float('nan')}
        toon_nan = encoder.encode(data_nan)
        assert "null" in toon_nan
        assert decoder.decode(toon_nan)["value"] is None

        # Infinity should become null
        data_inf = {"value": float('inf')}
        toon_inf = encoder.encode(data_inf)
        assert "null" in toon_inf
        assert decoder.decode(toon_inf)["value"] is None

        # Negative infinity should become null
        data_neg_inf = {"value": float('-inf')}
        toon_neg_inf = encoder.encode(data_neg_inf)
        assert "null" in toon_neg_inf
        assert decoder.decode(toon_neg_inf)["value"] is None

    def test_empty_string_value(self):
        """Test empty string as value."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {"text": ""}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data

    def test_empty_object(self):
        """Test empty object encoding."""
        encoder = ToonEncoder()
        decoder = ToonDecoder()

        data = {}
        toon = encoder.encode(data)
        decoded = decoder.decode(toon)

        assert decoded == data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
