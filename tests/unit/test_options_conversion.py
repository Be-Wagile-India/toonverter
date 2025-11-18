"""Comprehensive tests for EncodeOptions to ToonEncodeOptions conversion.

This test suite verifies that the encoder properly handles both user-facing
EncodeOptions and internal ToonEncodeOptions, addressing the critical bug
where integrations were failing due to delimiter type mismatches.
"""

import pytest

from toonverter.core.spec import Delimiter, ToonEncodeOptions
from toonverter.core.types import EncodeOptions
from toonverter.encoders.toon_encoder import ToonEncoder, _convert_options, encode


class TestOptionsConversion:
    """Test conversion between EncodeOptions and ToonEncodeOptions."""

    def test_convert_none_returns_none(self):
        """Test that None options returns None."""
        result = _convert_options(None)
        assert result is None

    def test_convert_toon_encode_options_passthrough(self):
        """Test that ToonEncodeOptions passes through unchanged."""
        options = ToonEncodeOptions(indent_size=4, delimiter=Delimiter.COMMA)
        result = _convert_options(options)
        assert result is options
        assert result.indent_size == 4
        assert result.delimiter == Delimiter.COMMA

    def test_convert_encode_options_with_comma_delimiter(self):
        """Test conversion of EncodeOptions with comma delimiter."""
        options = EncodeOptions(delimiter=",", indent=2, compact=False)
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.delimiter == Delimiter.COMMA
        assert result.indent_size == 2
        assert result.key_folding == "none"
        assert result.strict is True

    def test_convert_encode_options_with_tab_delimiter(self):
        """Test conversion of EncodeOptions with tab delimiter."""
        options = EncodeOptions(delimiter="\t", indent=4)
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.delimiter == Delimiter.TAB
        assert result.indent_size == 4

    def test_convert_encode_options_with_pipe_delimiter(self):
        """Test conversion of EncodeOptions with pipe delimiter."""
        options = EncodeOptions(delimiter="|", indent=2)
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.delimiter == Delimiter.PIPE
        assert result.indent_size == 2

    def test_convert_encode_options_compact_mode(self):
        """Test conversion with compact=True sets indent_size to 0."""
        options = EncodeOptions(compact=True, indent=2)
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.indent_size == 0  # Compact mode

    def test_convert_encode_options_tabular_preset(self):
        """Test conversion of tabular preset (used by pandas)."""
        options = EncodeOptions.tabular()
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.indent_size == 0  # Tabular is compact
        assert result.delimiter == Delimiter.COMMA

    def test_convert_encode_options_compact_preset(self):
        """Test conversion of compact preset."""
        options = EncodeOptions.create_compact()
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.indent_size == 0
        assert result.delimiter == Delimiter.COMMA

    def test_convert_encode_options_readable_preset(self):
        """Test conversion of readable preset."""
        options = EncodeOptions.readable()
        result = _convert_options(options)

        assert isinstance(result, ToonEncodeOptions)
        assert result.indent_size == 2
        assert result.delimiter == Delimiter.COMMA


class TestEncoderWithBothOptionTypes:
    """Test that ToonEncoder works with both option types."""

    def test_encoder_with_none_options(self):
        """Test encoder with no options."""
        encoder = ToonEncoder(None)
        result = encoder.encode({"name": "Alice", "age": 30})
        assert "name:" in result
        assert "Alice" in result

    def test_encoder_with_toon_encode_options(self):
        """Test encoder with ToonEncodeOptions."""
        options = ToonEncodeOptions(indent_size=4, delimiter=Delimiter.COMMA)
        encoder = ToonEncoder(options)
        result = encoder.encode({"name": "Alice", "age": 30})
        assert "name:" in result
        assert "Alice" in result

    def test_encode_function_with_encode_options(self):
        """Test encode() function with EncodeOptions."""
        options = EncodeOptions(indent=2, delimiter=",")
        result = encode({"name": "Alice", "age": 30}, options)
        assert "name:" in result
        assert "Alice" in result

    def test_encode_function_with_toon_encode_options(self):
        """Test encode() function with ToonEncodeOptions."""
        options = ToonEncodeOptions(indent_size=2, delimiter=Delimiter.COMMA)
        result = encode({"name": "Alice", "age": 30}, options)
        assert "name:" in result
        assert "Alice" in result

    def test_encode_function_with_compact_options(self):
        """Test encode() with compact EncodeOptions."""
        options = EncodeOptions.create_compact()
        result = encode({"name": "Alice", "age": 30}, options)
        # Compact mode should have no extra whitespace
        assert "\n" in result  # Still has newlines between fields


class TestCompactMode:
    """Test compact mode with indent_size=0."""

    def test_compact_mode_allowed_in_toon_encode_options(self):
        """Test that indent_size=0 is allowed in ToonEncodeOptions."""
        options = ToonEncodeOptions(indent_size=0, delimiter=Delimiter.COMMA)
        assert options.indent_size == 0

    def test_compact_mode_no_indentation(self):
        """Test that compact mode produces no indentation."""
        options = ToonEncodeOptions(indent_size=0, delimiter=Delimiter.COMMA)
        encoder = ToonEncoder(options)

        data = {"user": {"name": "Alice", "age": 30}}
        result = encoder.encode(data)

        # Should have no leading spaces
        lines = result.split("\n")
        for line in lines:
            if line:  # Skip empty lines
                assert not line.startswith(" "), f"Line should not be indented: {line!r}"

    def test_tabular_data_compact(self):
        """Test tabular data encoding in compact mode."""
        options = EncodeOptions.tabular()
        data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        result = encode(data, options)

        assert "[2]{x,y}:" in result
        assert "1,2" in result
        assert "3,4" in result


class TestDelimiterHandling:
    """Test different delimiter conversions."""

    def test_comma_delimiter_in_tabular_array(self):
        """Test comma delimiter in tabular arrays."""
        options = EncodeOptions(delimiter=",", compact=True)
        data = [{"a": 1, "b": 2}]
        result = encode(data, options)
        assert "[1]{a,b}:" in result
        assert "1,2" in result

    def test_tab_delimiter_in_tabular_array(self):
        """Test tab delimiter in tabular arrays."""
        options = EncodeOptions(delimiter="\t", compact=True)
        data = [{"a": 1, "b": 2}]
        result = encode(data, options)
        # TOON format uses delimiter in array header too
        assert "{a\tb}:" in result
        assert "1\t2" in result

    def test_pipe_delimiter_in_tabular_array(self):
        """Test pipe delimiter in tabular arrays."""
        options = EncodeOptions(delimiter="|", compact=True)
        data = [{"a": 1, "b": 2}]
        result = encode(data, options)
        # TOON format uses delimiter in array header too
        assert "{a|b}:" in result
        assert "1|2" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_negative_indent_size_raises_error(self):
        """Test that negative indent_size raises ValueError."""
        with pytest.raises(ValueError, match="must be at least 0"):
            ToonEncodeOptions(indent_size=-1, delimiter=Delimiter.COMMA)

    def test_invalid_delimiter_string_raises_error(self):
        """Test that invalid delimiter string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            Delimiter.from_string(";")

    def test_roundtrip_with_encode_options(self):
        """Test encode/decode roundtrip with EncodeOptions."""
        from toonverter.decoders import decode

        data = {"name": "Alice", "age": 30, "active": True}
        options = EncodeOptions(indent=2, delimiter=",")

        encoded = encode(data, options)
        decoded = decode(encoded)

        assert decoded == data

    def test_complex_nested_structure(self):
        """Test complex nested structure with EncodeOptions."""
        data = {
            "users": [
                {"name": "Alice", "age": 30, "tags": ["admin", "user"]},
                {"name": "Bob", "age": 25, "tags": ["user"]},
            ],
            "count": 2,
            "metadata": {"version": "1.0", "created": "2024-01-01"},
        }

        options = EncodeOptions.readable()
        result = encode(data, options)

        # Verify structure is present
        assert "users" in result
        assert "Alice" in result
        assert "Bob" in result
        assert "metadata" in result
