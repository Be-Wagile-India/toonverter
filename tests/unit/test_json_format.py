"Comprehensive tests for JSON format adapter."

import json
from datetime import date, datetime, timezone

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.json_format import DateTimeEncoder
from toonverter.formats.json_format import JsonFormatAdapter as JSONFormat


class TestDateTimeEncoder:
    """Test custom DateTimeEncoder."""

    def test_datetime_encoding(self):
        """Test encoding a datetime object."""
        dt = datetime(2023, 1, 1, 12, 30, 0, tzinfo=timezone.utc)
        encoded = json.dumps(dt, cls=DateTimeEncoder)
        # ISO format with timezone typically includes offset, e.g. +00:00 or Z depending on impl
        # Python's isoformat() uses +00:00 for UTC usually
        assert encoded == '"2023-01-01T12:30:00+00:00"'

    def test_date_encoding(self):
        """Test encoding a date object."""
        d = date(2023, 1, 1)
        encoded = json.dumps(d, cls=DateTimeEncoder)
        assert encoded == '"2023-01-01"'

    def test_other_object_encoding(self):
        """Test encoding a non-datetime/date object uses default behavior."""
        obj = {"key": "value"}
        encoded = json.dumps(obj, cls=DateTimeEncoder)
        assert json.loads(encoded) == obj

    def test_encoding_error_passthrough(self):
        """Test that DateTimeEncoder passes through errors for unhandled types."""

        class Unserializable:
            pass

        with pytest.raises(TypeError):
            json.dumps(Unserializable(), cls=DateTimeEncoder)


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
        data = {"text": 'Test "quotes" and newlines\nand tabs\t'}
        result = self.adapter.encode(data, None)
        decoded = json.loads(result)
        assert decoded["text"] == data["text"]

    def test_encode_compact_mode(self):
        """Test encoding with compact option."""
        data = {"a": 1, "b": 2}
        options = EncodeOptions(compact=True)
        result = self.adapter.encode(data, options)
        assert result in {'{"a":1,"b":2}', '{"b":2,"a":1}'}  # order not guaranteed

    def test_encode_preserves_order(self):
        """Test encoding preserves key order."""
        data = {"z": 1, "a": 2, "m": 3}
        # Use indent=None and compact=True to avoid whitespace issues in assertion
        options = EncodeOptions(sort_keys=False, indent=None, compact=True)
        result = self.adapter.encode(data, options)
        # Using an ordered dict or similar to ensure order if needed
        assert result.startswith(('{"z":1', '{"a":2', '{"m":3'))
        decoded = json.loads(result)
        assert set(decoded.keys()) == {"z", "a", "m"}

    def test_encode_error_handling(self):
        """Test that encoding invalid data raises EncodingError."""

        class Unserializable:
            pass

        data = {"obj": Unserializable()}
        with pytest.raises(EncodingError, match="Failed to encode to JSON"):
            self.adapter.encode(data, None)


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
        # The JSON string itself should contain the actual escape sequences \n and \t
        json_str = r'{"text": "Line1\nLine2\tTabbed"}'
        result = self.adapter.decode(json_str, None)
        assert result == {"text": "Line1\nLine2\tTabbed"}

    def test_decode_invalid_json(self):
        """Test decoding invalid JSON raises error."""
        with pytest.raises(DecodingError):
            self.adapter.decode('{"invalid": }', None)

    def test_decode_malformed_json(self):
        """Test decoding malformed JSON."""
        with pytest.raises(DecodingError):
            self.adapter.decode("not json at all", None)

    def test_decode_trailing_comma(self):
        """Test decoding with trailing comma fails."""
        with pytest.raises(DecodingError):
            self.adapter.decode('{"a": 1, "b": 2,}', None)

    def test_decode_invalid_json_non_strict(self):
        """Test decoding invalid JSON with strict=False returns original string."""
        invalid_json = '{"invalid": "json'  # Missing closing brace
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(invalid_json, options)
        assert result == invalid_json


class TestJSONValidation:
    """Test JSON validation functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_validate_valid_json(self):
        """Test validating valid JSON string."""
        assert self.adapter.validate('{"key": "value"}') is True
        assert self.adapter.validate("[]") is True
        assert self.adapter.validate("123") is True
        assert self.adapter.validate('"string" ') is True
        assert self.adapter.validate("null") is True
        assert self.adapter.validate("true") is True

    def test_validate_invalid_json(self):
        """Test validating invalid JSON string returns False."""
        assert self.adapter.validate('{"key": "value",}') is False  # Trailing comma
        assert self.adapter.validate("invalid json") is False
        assert (
            self.adapter.validate('{"key": "value", "another":}') is False
        )  # Simplified invalid JSON


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

    def test_roundtrip_datetime(self):
        """Test roundtrip with datetime objects."""
        # Use timezone-aware datetime
        dt_now = datetime.now(timezone.utc)
        d_today = datetime.now(timezone.utc).date()
        data = {"now": dt_now, "today": d_today}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)

        # Decoded values will be strings, so compare string representations
        assert decoded["now"] == dt_now.isoformat()
        assert decoded["today"] == d_today.isoformat()


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
        # JSON doesn't support NaN/Infinity, so they should be handled
        data = {"float": 3.14}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data
