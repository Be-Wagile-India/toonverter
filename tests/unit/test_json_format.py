"""Comprehensive tests for JSON format adapter."""

import json
from datetime import date, datetime, timezone

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.json_format import JsonFormatAdapter as JSONFormat


class TestJSONEncoding:
    """Test JSON encoding functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {"user": {"name": "Alice", "details": {"age": 30, "city": "NYC"}}}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_list(self):
        """Test encoding list."""
        data = {"items": [1, 2, 3, 4, 5]}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_mixed_types(self):
        """Test encoding mixed types."""
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_empty_dict(self):
        """Test encoding empty dictionary."""
        data = {}
        result = self.adapter.encode(data, None)
        assert result == "{}"

    def test_encode_empty_list(self):
        """Test encoding empty list."""
        data = {"items": []}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_unicode(self):
        """Test encoding unicode strings."""
        data = {"text": "Hello 世界 🌍"}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_special_characters(self):
        """Test encoding special characters."""
        data = {"text": 'Test "quotes" and \\backslash\\'}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_compact_default(self):
        """Test compact encoding (default behavior, no indent/newlines)."""
        data = {"a": 1, "b": 2}
        result = self.adapter.encode(data, None)
        # Check that there are no newlines, which implies non-indented output
        assert "\n" not in result

    def test_encode_compact_with_options(self):
        """Test compact encoding when explicitly set in options."""
        data = {"a": 1, "b": 2, "c": 3}
        options = EncodeOptions(compact=True)
        result = self.adapter.encode(data, options)
        # This path explicitly sets separators=(",", ":") in the adapter
        assert result == '{"a":1,"b":2,"c":3}'

    def test_encode_with_options_indent(self):
        """Test encoding with indent option (non-compact)."""
        data = {"a": 1, "b": 2}
        options = EncodeOptions(indent=4)
        result = self.adapter.encode(data, options)
        assert result.count("\n") > 0
        assert '    "a": 1' in result

    def test_encode_preserves_order(self):
        """Test encoding preserves key order."""
        data = {"z": 1, "a": 2, "m": 3}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        # Python dicts preserve insertion order from 3.7+
        assert list(decoded.keys()) == ["z", "a", "m"]

    def test_encode_datetime_and_date(self):
        """Test encoding datetime and date objects using custom encoder."""
        # Use a timezone-aware datetime object to satisfy DTZ001
        now = datetime(2025, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        today = date(2025, 1, 1)
        data = {"now": now, "today": today}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)

        # Check ISO format output, including the +00:00 for UTC
        assert decoded["now"] == "2025-01-01T12:30:00+00:00"
        assert decoded["today"] == "2025-01-01"

    def test_encode_unencodable_data(self):
        """Test encoding failure raises EncodingError."""
        # A set is not JSON serializable and should trigger TypeError
        data = {"key": {1, 2, 3}}
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "Failed to encode to JSON: Object of type set is not JSON serializable" in str(
            excinfo.value
        )


class TestJSONDecoding:
    """Test JSON decoding functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_decode_simple_object(self):
        """Test decoding simple object."""
        json_str = '{"name": "Alice", "age": 30}'
        result = self.adapter.decode(json_str, None)
        assert result == {"name": "Alice", "age": 30}

    def test_decode_nested_object(self):
        """Test decoding nested object."""
        json_str = '{"user": {"name": "Alice", "age": 30}}'
        result = self.adapter.decode(json_str, None)
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_decode_array(self):
        """Test decoding array."""
        json_str = '{"items": [1, 2, 3]}'
        result = self.adapter.decode(json_str, None)
        assert result == {"items": [1, 2, 3]}

    def test_decode_empty_object(self):
        """Test decoding empty object."""
        json_str = "{}"
        result = self.adapter.decode(json_str, None)
        assert result == {}

    def test_decode_null(self):
        """Test decoding null value."""
        json_str = '{"value": null}'
        result = self.adapter.decode(json_str, None)
        assert result == {"value": None}

    def test_decode_boolean(self):
        """Test decoding boolean values."""
        json_str = '{"true_val": true, "false_val": false}'
        result = self.adapter.decode(json_str, None)
        assert result == {"true_val": True, "false_val": False}

    def test_decode_numbers(self):
        """Test decoding various number formats."""
        json_str = '{"int": 42, "float": 3.14, "negative": -10, "zero": 0}'
        result = self.adapter.decode(json_str, None)
        assert result == {"int": 42, "float": 3.14, "negative": -10, "zero": 0}

    def test_decode_unicode(self):
        """Test decoding unicode."""
        json_str = '{"text": "Hello 世界"}'
        result = self.adapter.decode(json_str, None)
        assert result == {"text": "Hello 世界"}

    def test_decode_escaped_characters(self):
        """Test decoding escaped characters."""
        json_str = '{"text": "Line1\\nLine2\\tTabbed"}'
        result = self.adapter.decode(json_str, None)
        assert result == {"text": "Line1\nLine2\tTabbed"}

    def test_decode_invalid_json_strict(self):
        """Test decoding invalid JSON in strict mode raises error."""
        options = DecodeOptions(strict=True)
        with pytest.raises(DecodingError):
            self.adapter.decode('{"invalid": }', options)

    def test_decode_invalid_json_non_strict(self):
        """Test decoding invalid JSON in non-strict mode returns the raw string."""
        invalid_json_str = '{"malformed": "oops'
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(invalid_json_str, options)
        assert result == invalid_json_str

    def test_decode_malformed_json(self):
        """Test decoding malformed JSON."""
        with pytest.raises(DecodingError):
            self.adapter.decode("not json at all", None)

    def test_decode_trailing_comma(self):
        """Test decoding with trailing comma fails."""
        with pytest.raises(DecodingError):
            self.adapter.decode('{"a": 1, "b": 2,}', None)


class TestJSONValidation:
    """Test JSON validation functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_validate_valid_json(self):
        """Test validation for valid JSON."""
        assert self.adapter.validate('{"a": 1, "b": "two"}') is True

    def test_validate_empty_string(self):
        """Test validation for an empty string (is valid JSON)."""
        # An empty string is not valid JSON and should fail validation.
        assert self.adapter.validate("") is False

    def test_validate_invalid_json(self):
        """Test validation for invalid JSON (covers exception path)."""
        assert self.adapter.validate('{"a": 1, "b": "two') is False


class TestJSONRoundtrip:
    """Test JSON encoding/decoding roundtrip."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_roundtrip_complex(self):
        """Test complex data roundtrip."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": ["python", "ai"]},
                {"id": 2, "name": "Bob", "tags": ["javascript", "web"]},
            ],
            "metadata": {"count": 2, "active": True},
        }
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_roundtrip_preserves_types(self):
        """Test roundtrip preserves data types."""
        data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null": None,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
        }
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)

        assert isinstance(decoded["string"], str)
        assert isinstance(decoded["integer"], int)
        assert isinstance(decoded["float"], float)
        assert isinstance(decoded["boolean"], bool)
        assert decoded["null"] is None
        assert isinstance(decoded["list"], list)
        assert isinstance(decoded["dict"], dict)


class TestJSONEdgeCases:
    """Test JSON edge cases."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_large_numbers(self):
        """Test encoding/decoding large numbers."""
        data = {"big": 999999999999999999}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_very_small_numbers(self):
        """Test encoding/decoding very small numbers."""
        data = {"small": 0.000000000001}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert abs(decoded["small"] - data["small"]) < 1e-15

    def test_deeply_nested_structure(self):
        """Test deeply nested structure."""
        data = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_empty_strings(self):
        """Test empty strings."""
        data = {"empty": "", "text": "not empty"}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_whitespace_strings(self):
        """Test whitespace strings."""
        data = {"spaces": "   ", "mixed": " text "}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_special_float_values(self):
        """Test special float values."""
        data = {"float": 3.14}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data
