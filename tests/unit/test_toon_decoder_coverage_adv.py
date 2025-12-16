"""Advanced coverage tests for ToonDecoder."""

from unittest.mock import patch

import pytest

from toonverter.core.spec import ToonDecodeOptions
from toonverter.decoders.toon_decoder import DecodingError, ToonDecoder


class TestToonDecoderAdvancedCoverage:
    @pytest.fixture(autouse=True)
    def disable_rust_decoder(self):
        """Disable Rust decoder for all tests in this class to ensure Python coverage."""
        with patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", False):
            yield

    def test_rust_decoder_value_error(self):
        """Test proper handling of Rust decoder ValueError."""
        # Re-enable Rust for this specific test
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", True),
            patch("toonverter.decoders.toon_decoder.rust_core") as mock_rust,
        ):
            mock_rust.decode_toon.side_effect = ValueError("Rust error")
            decoder = ToonDecoder(ToonDecodeOptions(strict=True, type_inference=True))
            with pytest.raises(DecodingError, match="Rust error"):
                decoder.decode("some data")

    def test_rust_decoder_general_exception_fallback(self):
        """Test fallback to Python when Rust decoder panics/fails unexpectedly."""
        # Re-enable Rust for this specific test
        with (
            patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", True),
            patch("toonverter.decoders.toon_decoder.rust_core") as mock_rust,
        ):
            mock_rust.decode_toon.side_effect = Exception("Unexpected Rust panic")
            decoder = ToonDecoder(ToonDecodeOptions(strict=True, type_inference=True))
            # Should fallback to python and succeed
            result = decoder.decode("name: test")
            assert result == {"name": "test"}

    def test_root_object_missing_colon(self):
        """Test error when root object key is missing colon."""
        decoder = ToonDecoder()
        with pytest.raises(DecodingError, match="Expected ':' after key"):
            decoder.decode("key value")

    def test_root_object_unexpected_token(self):
        """Test error when root object starts with invalid token."""
        decoder = ToonDecoder()
        # Input starting with INDENT triggers root object detection, but loop finds INDENT
        with pytest.raises(DecodingError, match="Unexpected token at root object"):
            decoder.decode("  :")

    def test_list_array_unexpected_token(self):
        """Test error when list array has unexpected tokens (e.g. multiple values on line)."""
        decoder = ToonDecoder()
        # "- key" is parsed as primitive "key". "value" remains.
        with pytest.raises(DecodingError, match="Unexpected token in list array"):
            decoder.decode("- key value")

    def test_tabular_array_missing_fields_header(self):
        """Test error for tabular array without fields."""
        decoder = ToonDecoder()
        with pytest.raises(DecodingError, match="Tabular array must have fields"):
            decoder.decode("[3]{}:")

    def test_extra_tokens_after_root(self):
        """Test error when extra content exists after root object.

        Note: The Python decoder parses 'key: value', then sees 'extra_garbage'.
        It treats 'extra_garbage' as a new key in the root object loop, and fails
        because it's not followed by a colon.
        """
        decoder = ToonDecoder()
        with pytest.raises(DecodingError, match="Expected ':' after key"):
            decoder.decode("key: value\nextra_garbage")

    def test_inline_array_parsing_with_trailing_comma(self):
        """Test parsing of inline array with trailing comma."""
        decoder = ToonDecoder()  # strict=True by default
        # [3]: 1,2,3, -> parses [1, 2, 3], then comma is extra token
        from toonverter.core.exceptions import DecodingError

        with pytest.raises(DecodingError, match="Extra tokens"):
            decoder.decode("[3]: 1,2,3,")

    def test_nested_object_missing_colon(self):
        """Test missing colon in nested object."""
        decoder = ToonDecoder()
        data = """
root:
  nested value
"""
        with pytest.raises(DecodingError, match="Expected ':' after key"):
            decoder.decode(data)
