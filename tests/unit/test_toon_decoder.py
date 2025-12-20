"Comprehensive unit tests for TOON decoder."

from unittest.mock import patch

import pytest

from toonverter.core.exceptions import DecodingError, ValidationError
from toonverter.core.spec import ToonDecodeOptions
from toonverter.decoders.toon_decoder import ToonDecoder, decode


@pytest.fixture
def force_python_decoder():
    """Fixture to ensure USE_RUST_DECODER is False for these tests."""
    with patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", False):
        yield


class TestToonDecoderBasic:
    """Basic functional tests for TOON decoder."""

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

        data = [1, 2, 3, 4, 5]
        toon_str = encoder.encode(data)
        result = decoder.decode(toon_str)
        assert result == [1, 2, 3, 4, 5]

    def test_decode_tabular(self):
        """Test decoding of tabular data."""
        from toonverter.encoders import ToonEncoder

        encoder = ToonEncoder()
        decoder = ToonDecoder()

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


@pytest.mark.usefixtures("force_python_decoder")
class TestToonDecoderCoverage:
    """Tests specifically targeting Python decoder coverage."""

    def test_decode_empty_string(self):
        assert decode("") == {}
        assert decode("   \n\n  ") == {}

    def test_decode_root_unquoted_string_primitive(self):
        # type_inference=False to ensure it remains a string if desired
        options = ToonDecodeOptions(type_inference=False)
        assert decode("bare_string", options=options) == "bare_string"

    def test_decode_root_dash_array(self):
        assert decode("- item1") == ["item1"]

    def test_decode_object_with_empty_nested_value(self):
        toon_str = "key:\n  nested_key:"
        expected = {"key": {"nested_key": None}}
        assert decode(toon_str) == expected

    def test_decode_inline_object_in_list_array(self):
        toon_str = "- name: Alice\n  age: 30"
        expected = [{"name": "Alice", "age": 30}]
        assert decode(toon_str) == expected

    def test_decode_inline_object_in_list_array_with_none_value(self):
        toon_str = "- name:\n  age: 30"
        expected = [{"name": None, "age": 30}]
        assert decode(toon_str) == expected

    def test_decode_inline_array_implicit_null(self):
        # [3]: 1,2  -> 1, 2, None
        toon_str = "values[3]: 1,2"
        assert decode(toon_str) == {"values": [1, 2, None]}

    def test_root_object_with_array_value(self):
        data = "numbers[3]: 1, 2, 3"
        assert decode(data) == {"numbers": [1, 2, 3]}

    def test_tabular_array_validation(self):
        data = """
[1]{col1, col2}:
  val1
"""
        options = ToonDecodeOptions(strict=True)
        with pytest.raises(
            ValidationError, match="Row width mismatch: declared 2 fields, got 1 values"
        ):
            decode(data, options=options)

    def test_type_inference_options(self):
        options = ToonDecodeOptions(type_inference=False)
        assert decode("key: 123", options=options) == {"key": 123}
        assert decode("key: true", options=options) == {"key": True}
        assert decode("key: null", options=options) == {"key": None}

    def test_inline_array_empty_items(self):
        data = "[3]: 1,,3"
        assert decode(data) == [1, None, 3]


class TestToonDecoderErrorHandling:
    """Test error handling and edge cases."""

    def test_rust_decoder_value_error(self):
        """Test proper handling of Rust decoder ValueError."""
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", True),
            patch("toonverter.decoders.toon_decoder.rust_core") as mock_rust,
        ):
            mock_rust.decode_toon.side_effect = ValueError("Rust error")
            with pytest.raises(DecodingError, match="Rust error"):
                decode("some data")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_rust_decoder_general_exception_fallback(self):
        """Test fallback to Python when Rust decoder fails unexpectedly."""
        # Use a context where Rust IS enabled but fails
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", True),
            patch("toonverter.decoders.toon_decoder.rust_core") as mock_rust,
        ):
            mock_rust.decode_toon.side_effect = Exception("Panic")
            # Should fallback to python and succeed
            assert decode("name: test") == {"name": "test"}

    @pytest.mark.usefixtures("force_python_decoder")
    def test_root_object_missing_colon(self):
        with pytest.raises(DecodingError, match="Expected ':'"):
            decode("key value")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_root_object_unexpected_token(self):
        with pytest.raises(DecodingError, match="Unexpected token"):
            decode("  :")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_list_array_unexpected_token(self):
        with pytest.raises(DecodingError, match="Unexpected token"):
            decode("- key value")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_tabular_array_missing_fields_header(self):
        with pytest.raises(DecodingError, match="Tabular array must have fields"):
            decode("[3]{}:")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_extra_tokens_after_root(self):
        # Force python decoder so we get the expected error message
        with pytest.raises(DecodingError, match="Expected ':'"):
            decode("key: value\nextra_garbage")

    @pytest.mark.usefixtures("force_python_decoder")
    def test_nested_object_missing_colon(self):
        data = "root:\n  nested value"
        with pytest.raises(DecodingError, match="Expected ':'"):
            decode(data)

    def test_inline_array_parsing_with_trailing_comma(self):
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", False),
            pytest.raises(DecodingError, match="Extra tokens"),
        ):
            decode("[3]: 1,2,3,")
