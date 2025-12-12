"""Unit tests for TOON decoder."""

import pytest

from toonverter.decoders import ToonDecoder, decode


class TestToonDecoder:
    """Test suite for TOON decoder."""

    def test_decode_simple_dict(self):
        """Test decoding of simple dictionary."""
        decoder = ToonDecoder()
        toon_str = "name: Alice\nage: 30"
        result = decoder.decode(toon_str)
        assert result["name"] == "Alice"
        assert result["age"] == 30

    def test_decode_list(self):
        """Test decoding of list."""
        from toonverter.encoders import ToonEncoder

        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Use encoder to generate correct TOON syntax
        data = [1, 2, 3, 4, 5]
        toon_str = encoder.encode(data)
        result = decoder.decode(toon_str)
        assert result == [1, 2, 3, 4, 5]

    def test_decode_tabular(self):
        """Test decoding of tabular data."""
        from toonverter.encoders import ToonEncoder

        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Use encoder to generate correct tabular TOON syntax
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        toon_str = encoder.encode(data)
        result = decoder.decode(toon_str)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == 25

    def test_decode_nested(self):
        """Test decoding of nested structure."""
        from toonverter.encoders import ToonEncoder

        encoder = ToonEncoder()
        decoder = ToonDecoder()

        # Use encoder to generate correct nested TOON syntax
        data = {"user": {"name": "Alice", "age": 30}, "tags": ["python", "llm"]}
        toon_str = encoder.encode(data)
        result = decoder.decode(toon_str)
        assert result["user"]["name"] == "Alice"
        assert "python" in result["tags"]

    @pytest.mark.parametrize(
        ("toon_str", "expected"),
        [
            ("true", True),
            ("false", False),
            ("null", None),
            ("42", 42),
            ("3.14", 3.14),
            ('"hello"', "hello"),
        ],
    )
    def test_decode_primitives(self, toon_str, expected):
        """Test decoding of primitive types."""
        decoder = ToonDecoder()
        result = decoder.decode(toon_str)
        assert result == expected

    def test_convenience_function(self):
        """Test convenience decode function."""
        result = decode("name: Alice")
        assert result["name"] == "Alice"

    def test_roundtrip(self, sample_dict):
        """Test encode-decode roundtrip."""
        from toonverter.encoders import encode

        encoded = encode(sample_dict)
        decoded = decode(encoded)
        assert decoded == sample_dict
