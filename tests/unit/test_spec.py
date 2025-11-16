"""Comprehensive tests for TOON specification types and constants."""

import pytest
from toonverter.core.spec import (
    Delimiter,
    ArrayForm,
    RootForm,
    ToonEncodeOptions,
    ToonDecodeOptions,
    ArrayHeader,
    KeyPath,
    RESERVED_WORDS,
    NUMBER_PATTERN,
    KEY_SEGMENT_PATTERN,
    DEFAULT_INDENT_SIZE,
    DEFAULT_DELIMITER,
)


class TestDelimiter:
    """Test Delimiter enum."""

    def test_delimiter_values(self):
        """Test delimiter enum values."""
        assert Delimiter.COMMA.value == ","
        assert Delimiter.TAB.value == "\t"
        assert Delimiter.PIPE.value == "|"

    def test_from_string_comma(self):
        """Test parsing comma delimiter."""
        result = Delimiter.from_string(",")
        assert result == Delimiter.COMMA

    def test_from_string_tab(self):
        """Test parsing tab delimiter."""
        result = Delimiter.from_string("\t")
        assert result == Delimiter.TAB

    def test_from_string_pipe(self):
        """Test parsing pipe delimiter."""
        result = Delimiter.from_string("|")
        assert result == Delimiter.PIPE

    def test_from_string_invalid_raises_error(self):
        """Test invalid delimiter raises ValueError."""
        with pytest.raises(ValueError, match="Invalid delimiter"):
            Delimiter.from_string(";")

    def test_str_conversion_comma(self):
        """Test converting comma delimiter to string."""
        assert str(Delimiter.COMMA) == ","

    def test_str_conversion_tab(self):
        """Test converting tab delimiter to string."""
        assert str(Delimiter.TAB) == "\t"

    def test_str_conversion_pipe(self):
        """Test converting pipe delimiter to string."""
        assert str(Delimiter.PIPE) == "|"


class TestArrayForm:
    """Test ArrayForm enum."""

    def test_array_form_values(self):
        """Test array form enum values."""
        assert ArrayForm.INLINE.value == "inline"
        assert ArrayForm.TABULAR.value == "tabular"
        assert ArrayForm.LIST.value == "list"


class TestRootForm:
    """Test RootForm enum."""

    def test_root_form_values(self):
        """Test root form enum values."""
        assert RootForm.OBJECT.value == "object"
        assert RootForm.ARRAY.value == "array"
        assert RootForm.PRIMITIVE.value == "primitive"


class TestToonEncodeOptions:
    """Test ToonEncodeOptions dataclass."""

    def test_default_options(self):
        """Test default encoding options."""
        options = ToonEncodeOptions()

        assert options.indent_size == DEFAULT_INDENT_SIZE
        assert options.delimiter == DEFAULT_DELIMITER
        assert options.key_folding == "none"
        assert options.strict is True

    def test_custom_indent_size(self):
        """Test custom indent size."""
        options = ToonEncodeOptions(indent_size=4)
        assert options.indent_size == 4

    def test_custom_delimiter(self):
        """Test custom delimiter."""
        options = ToonEncodeOptions(delimiter=Delimiter.PIPE)
        assert options.delimiter == Delimiter.PIPE

    def test_key_folding_safe(self):
        """Test safe key folding mode."""
        options = ToonEncodeOptions(key_folding="safe")
        assert options.key_folding == "safe"

    def test_key_folding_none(self):
        """Test no key folding mode."""
        options = ToonEncodeOptions(key_folding="none")
        assert options.key_folding == "none"

    def test_strict_mode_enabled(self):
        """Test strict mode enabled."""
        options = ToonEncodeOptions(strict=True)
        assert options.strict is True

    def test_strict_mode_disabled(self):
        """Test strict mode disabled."""
        options = ToonEncodeOptions(strict=False)
        assert options.strict is False

    def test_invalid_indent_size_zero_raises_error(self):
        """Test indent size of 0 raises error."""
        with pytest.raises(ValueError, match="indent_size must be at least 1"):
            ToonEncodeOptions(indent_size=0)

    def test_invalid_indent_size_negative_raises_error(self):
        """Test negative indent size raises error."""
        with pytest.raises(ValueError, match="indent_size must be at least 1"):
            ToonEncodeOptions(indent_size=-1)

    def test_invalid_key_folding_raises_error(self):
        """Test invalid key folding mode raises error."""
        with pytest.raises(ValueError, match="key_folding must be"):
            ToonEncodeOptions(key_folding="invalid")


class TestToonDecodeOptions:
    """Test ToonDecodeOptions dataclass."""

    def test_default_options(self):
        """Test default decoding options."""
        options = ToonDecodeOptions()

        assert options.strict is True
        assert options.type_inference is True

    def test_strict_mode_disabled(self):
        """Test strict mode disabled."""
        options = ToonDecodeOptions(strict=False)
        assert options.strict is False

    def test_type_inference_disabled(self):
        """Test type inference disabled."""
        options = ToonDecodeOptions(type_inference=False)
        assert options.type_inference is False

    def test_custom_options(self):
        """Test custom decoding options."""
        options = ToonDecodeOptions(strict=False, type_inference=False)

        assert options.strict is False
        assert options.type_inference is False


class TestArrayHeader:
    """Test ArrayHeader dataclass."""

    def test_default_array_header(self):
        """Test default array header."""
        header = ArrayHeader(length=5)

        assert header.length == 5
        assert header.fields is None
        assert header.delimiter == DEFAULT_DELIMITER
        assert header.form == ArrayForm.LIST

    def test_array_header_with_fields(self):
        """Test array header with fields."""
        header = ArrayHeader(
            length=3,
            fields=["name", "age", "city"],
            form=ArrayForm.TABULAR
        )

        assert header.length == 3
        assert header.fields == ["name", "age", "city"]
        assert header.form == ArrayForm.TABULAR

    def test_array_header_with_custom_delimiter(self):
        """Test array header with custom delimiter."""
        header = ArrayHeader(length=10, delimiter=Delimiter.PIPE)

        assert header.delimiter == Delimiter.PIPE

    def test_validate_row_count_matches(self):
        """Test validating matching row count."""
        header = ArrayHeader(length=5)

        # Should not raise
        header.validate_row_count(5)

    def test_validate_row_count_mismatch_raises_error(self):
        """Test validating mismatched row count raises error."""
        header = ArrayHeader(length=5)

        with pytest.raises(ValueError, match="Array length mismatch"):
            header.validate_row_count(3)

    def test_validate_row_count_too_many_raises_error(self):
        """Test validating too many rows raises error."""
        header = ArrayHeader(length=5)

        with pytest.raises(ValueError, match="declared 5, got 7"):
            header.validate_row_count(7)

    def test_validate_field_count_matches(self):
        """Test validating matching field count."""
        header = ArrayHeader(length=2, fields=["name", "age"])

        # Should not raise
        header.validate_field_count(2)

    def test_validate_field_count_mismatch_raises_error(self):
        """Test validating mismatched field count raises error."""
        header = ArrayHeader(length=2, fields=["name", "age", "city"])

        with pytest.raises(ValueError, match="Field count mismatch"):
            header.validate_field_count(2)

    def test_validate_field_count_no_fields(self):
        """Test validating field count when fields is None."""
        header = ArrayHeader(length=5, fields=None)

        # Should not raise even if count doesn't match
        header.validate_field_count(10)


class TestKeyPath:
    """Test KeyPath dataclass."""

    def test_simple_key_path(self):
        """Test simple key path."""
        path = KeyPath(segments=["key"])

        assert path.segments == ["key"]
        assert path.folded is False

    def test_folded_key_path(self):
        """Test folded key path."""
        path = KeyPath(segments=["a", "b", "c"], folded=True)

        assert path.segments == ["a", "b", "c"]
        assert path.folded is True

    def test_parse_simple_key(self):
        """Test parsing simple key."""
        path = KeyPath.parse("name")

        assert path.segments == ["name"]
        assert path.folded is False

    def test_parse_folded_key(self):
        """Test parsing folded key."""
        path = KeyPath.parse("user.name.first")

        assert path.segments == ["user", "name", "first"]
        assert path.folded is True

    def test_parse_two_segment_key(self):
        """Test parsing two-segment key."""
        path = KeyPath.parse("a.b")

        assert path.segments == ["a", "b"]
        assert path.folded is True

    def test_parse_invalid_segment_not_folded(self):
        """Test parsing invalid segment doesn't fold."""
        path = KeyPath.parse("invalid-segment.key")

        # Invalid segment (contains hyphen), so not folded
        assert path.folded is False

    def test_to_string_simple_key(self):
        """Test converting simple key to string."""
        path = KeyPath(segments=["key"], folded=False)

        result = path.to_string()

        assert result == "key"

    def test_to_string_folded_key(self):
        """Test converting folded key to string."""
        path = KeyPath(segments=["a", "b", "c"], folded=True)

        result = path.to_string()

        assert result == "a.b.c"

    def test_can_fold_single_segment(self):
        """Test single segment cannot fold."""
        path = KeyPath(segments=["key"])

        assert path.can_fold() is False

    def test_can_fold_multiple_valid_segments(self):
        """Test multiple valid segments can fold."""
        path = KeyPath(segments=["user", "name", "first"])

        assert path.can_fold() is True

    def test_can_fold_invalid_segment(self):
        """Test invalid segment cannot fold."""
        path = KeyPath(segments=["valid", "invalid-segment"])

        assert path.can_fold() is False

    def test_can_fold_empty_segment(self):
        """Test empty segment cannot fold."""
        path = KeyPath(segments=["valid", ""])

        assert path.can_fold() is False


class TestConstants:
    """Test specification constants."""

    def test_reserved_words(self):
        """Test reserved words set."""
        assert "true" in RESERVED_WORDS
        assert "false" in RESERVED_WORDS
        assert "null" in RESERVED_WORDS

    def test_number_pattern_integers(self):
        """Test number pattern matches integers."""
        assert NUMBER_PATTERN.match("42")
        assert NUMBER_PATTERN.match("0")
        assert NUMBER_PATTERN.match("-10")

    def test_number_pattern_floats(self):
        """Test number pattern matches floats."""
        assert NUMBER_PATTERN.match("3.14")
        assert NUMBER_PATTERN.match("0.5")
        assert NUMBER_PATTERN.match("-2.7")

    def test_number_pattern_scientific(self):
        """Test number pattern matches scientific notation."""
        assert NUMBER_PATTERN.match("1e5")
        assert NUMBER_PATTERN.match("1.5E-3")
        assert NUMBER_PATTERN.match("2.4e+10")

    def test_number_pattern_non_numbers(self):
        """Test number pattern doesn't match non-numbers."""
        assert not NUMBER_PATTERN.match("abc")
        assert not NUMBER_PATTERN.match("12abc")
        assert not NUMBER_PATTERN.match("1.2.3")

    def test_key_segment_pattern_valid(self):
        """Test key segment pattern matches valid identifiers."""
        assert KEY_SEGMENT_PATTERN.match("name")
        assert KEY_SEGMENT_PATTERN.match("_private")
        assert KEY_SEGMENT_PATTERN.match("var123")
        assert KEY_SEGMENT_PATTERN.match("CamelCase")

    def test_key_segment_pattern_invalid(self):
        """Test key segment pattern doesn't match invalid identifiers."""
        assert not KEY_SEGMENT_PATTERN.match("123")  # Starts with digit
        assert not KEY_SEGMENT_PATTERN.match("with-hyphen")
        assert not KEY_SEGMENT_PATTERN.match("with space")
        assert not KEY_SEGMENT_PATTERN.match("")

    def test_default_indent_size(self):
        """Test default indent size constant."""
        assert DEFAULT_INDENT_SIZE == 2

    def test_default_delimiter(self):
        """Test default delimiter constant."""
        assert DEFAULT_DELIMITER == Delimiter.COMMA


class TestEdgeCases:
    """Test edge cases."""

    def test_array_header_zero_length(self):
        """Test array header with zero length."""
        header = ArrayHeader(length=0)

        assert header.length == 0
        # Validation should pass
        header.validate_row_count(0)

    def test_array_header_large_length(self):
        """Test array header with large length."""
        header = ArrayHeader(length=1000000)

        assert header.length == 1000000

    def test_key_path_many_segments(self):
        """Test key path with many segments."""
        path = KeyPath(segments=["a", "b", "c", "d", "e", "f"])

        assert len(path.segments) == 6
        assert path.can_fold() is True

    def test_key_path_parse_empty_string(self):
        """Test parsing empty string."""
        path = KeyPath.parse("")

        assert path.segments == [""]
        assert path.folded is False

    def test_toon_encode_options_minimum_indent(self):
        """Test minimum valid indent size."""
        options = ToonEncodeOptions(indent_size=1)

        assert options.indent_size == 1
