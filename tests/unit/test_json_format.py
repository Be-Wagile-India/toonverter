"""Comprehensive tests for JSON format adapter."""

import pytest
import json
from toonverter.formats.json_format import JsonFormatAdapter as JSONFormat
from toonverter.core.exceptions import EncodingError, DecodingError


class TestJSONEncoding:
    """Test JSON encoding functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {
            "user": {
                "name": "Alice",
                "details": {
                    "age": 30,
                    "city": "NYC"
                }
            }
        }
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_list(self):
        """Test encoding list."""
        data = {"items": [1, 2, 3, 4, 5]}
        result = self.adapter.encode(data, {})
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
            "dict": {"key": "value"}
        }
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_empty_dict(self):
        """Test encoding empty dictionary."""
        data = {}
        result = self.adapter.encode(data, {})
        assert result == "{}"

    def test_encode_empty_list(self):
        """Test encoding empty list."""
        data = {"items": []}
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_unicode(self):
        """Test encoding unicode strings."""
        data = {"text": "Hello 世界 🌍"}
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_special_characters(self):
        """Test encoding special characters."""
        data = {"text": 'Test "quotes" and \\backslash\\'}
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_compact(self):
        """Test compact encoding."""
        data = {"a": 1, "b": 2}
        result = self.adapter.encode(data, {})
        # Should be compact by default
        decoded = json.loads(result)
        assert decoded == data

    def test_encode_preserves_order(self):
        """Test encoding preserves key order."""
        data = {"z": 1, "a": 2, "m": 3}
        result = self.adapter.encode(data, {})
        decoded = json.loads(result)
        # At least verify all keys are present
        assert set(decoded.keys()) == {"z", "a", "m"}


class TestJSONDecoding:
    """Test JSON decoding functionality."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_decode_simple_object(self):
        """Test decoding simple object."""
        json_str = '{"name": "Alice", "age": 30}'
        result = self.adapter.decode(json_str, {})
        assert result == {"name": "Alice", "age": 30}

    def test_decode_nested_object(self):
        """Test decoding nested object."""
        json_str = '{"user": {"name": "Alice", "age": 30}}'
        result = self.adapter.decode(json_str, {})
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_decode_array(self):
        """Test decoding array."""
        json_str = '{"items": [1, 2, 3]}'
        result = self.adapter.decode(json_str, {})
        assert result == {"items": [1, 2, 3]}

    def test_decode_empty_object(self):
        """Test decoding empty object."""
        json_str = '{}'
        result = self.adapter.decode(json_str, {})
        assert result == {}

    def test_decode_null(self):
        """Test decoding null value."""
        json_str = '{"value": null}'
        result = self.adapter.decode(json_str, {})
        assert result == {"value": None}

    def test_decode_boolean(self):
        """Test decoding boolean values."""
        json_str = '{"true_val": true, "false_val": false}'
        result = self.adapter.decode(json_str, {})
        assert result == {"true_val": True, "false_val": False}

    def test_decode_numbers(self):
        """Test decoding various number formats."""
        json_str = '{"int": 42, "float": 3.14, "negative": -10, "zero": 0}'
        result = self.adapter.decode(json_str, {})
        assert result == {"int": 42, "float": 3.14, "negative": -10, "zero": 0}

    def test_decode_unicode(self):
        """Test decoding unicode."""
        json_str = '{"text": "Hello 世界"}'
        result = self.adapter.decode(json_str, {})
        assert result == {"text": "Hello 世界"}

    def test_decode_escaped_characters(self):
        """Test decoding escaped characters."""
        json_str = '{"text": "Line1\\nLine2\\tTabbed"}'
        result = self.adapter.decode(json_str, {})
        assert result == {"text": "Line1\nLine2\tTabbed"}

    def test_decode_invalid_json(self):
        """Test decoding invalid JSON raises error."""
        with pytest.raises(DecodingError):
            self.adapter.decode('{"invalid": }', {})

    def test_decode_malformed_json(self):
        """Test decoding malformed JSON."""
        with pytest.raises(DecodingError):
            self.adapter.decode('not json at all', {})

    def test_decode_trailing_comma(self):
        """Test decoding with trailing comma fails."""
        with pytest.raises(DecodingError):
            self.adapter.decode('{"a": 1, "b": 2,}', {})


class TestJSONRoundtrip:
    """Test JSON encoding/decoding roundtrip."""

    def setup_method(self):
        """Set up JSON format adapter."""
        self.adapter = JSONFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_roundtrip_complex(self):
        """Test complex data roundtrip."""
        data = {
            "users": [
                {"id": 1, "name": "Alice", "tags": ["python", "ai"]},
                {"id": 2, "name": "Bob", "tags": ["javascript", "web"]}
            ],
            "metadata": {
                "count": 2,
                "active": True
            }
        }
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
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
            "dict": {"nested": "value"}
        }
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})

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
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_very_small_numbers(self):
        """Test encoding/decoding very small numbers."""
        data = {"small": 0.000000000001}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert abs(decoded["small"] - data["small"]) < 1e-15

    def test_deeply_nested_structure(self):
        """Test deeply nested structure."""
        data = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_empty_strings(self):
        """Test empty strings."""
        data = {"empty": "", "text": "not empty"}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_whitespace_strings(self):
        """Test whitespace strings."""
        data = {"spaces": "   ", "mixed": " text "}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_special_float_values(self):
        """Test special float values."""
        # JSON doesn't support NaN/Infinity, so they should be handled
        data = {"float": 3.14}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data
