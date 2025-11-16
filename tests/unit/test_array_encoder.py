"""Comprehensive tests for array encoder."""

import pytest
from toonverter.encoders.array_encoder import ArrayEncoder
from toonverter.encoders.string_encoder import StringEncoder
from toonverter.encoders.number_encoder import NumberEncoder
from toonverter.encoders.indentation import IndentationManager
from toonverter.core.spec import ArrayForm, Delimiter


class TestArrayEncoderInit:
    """Test ArrayEncoder initialization."""

    def test_init_with_encoders(self):
        """Test initialization with encoders."""
        str_enc = StringEncoder(Delimiter.COMMA)
        num_enc = NumberEncoder()
        indent_mgr = IndentationManager()

        encoder = ArrayEncoder(str_enc, num_enc, indent_mgr)

        assert encoder.str_enc is str_enc
        assert encoder.num_enc is num_enc
        assert encoder.indent_mgr is indent_mgr
        assert encoder.delimiter == ","


class TestDetectArrayForm:
    """Test array form detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_detect_empty_array_as_inline(self):
        """Test empty array detected as inline."""
        result = self.encoder.detect_array_form([])
        assert result == ArrayForm.INLINE

    def test_detect_primitive_array_as_inline(self):
        """Test primitive array detected as inline."""
        result = self.encoder.detect_array_form([1, 2, 3, 4, 5])
        assert result == ArrayForm.INLINE

    def test_detect_string_array_as_inline(self):
        """Test string array detected as inline."""
        result = self.encoder.detect_array_form(["a", "b", "c"])
        assert result == ArrayForm.INLINE

    def test_detect_mixed_primitives_as_inline(self):
        """Test mixed primitive array detected as inline."""
        result = self.encoder.detect_array_form([1, "hello", True, None, 3.14])
        assert result == ArrayForm.INLINE

    def test_detect_uniform_dicts_as_tabular(self):
        """Test uniform dict array detected as tabular."""
        arr = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.TABULAR

    def test_detect_single_dict_as_tabular(self):
        """Test single dict array detected as tabular."""
        arr = [{"id": 1, "name": "Alice"}]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.TABULAR

    def test_detect_non_uniform_dicts_as_list(self):
        """Test non-uniform dict keys detected as list."""
        arr = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "email": "bob@example.com"}  # Different keys
        ]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.LIST

    def test_detect_dicts_with_nested_values_as_list(self):
        """Test dicts with non-primitive values detected as list."""
        arr = [
            {"id": 1, "tags": ["a", "b"]},  # Nested list
            {"id": 2, "tags": ["c", "d"]}
        ]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.LIST

    def test_detect_mixed_types_as_list(self):
        """Test mixed types detected as list."""
        arr = [1, {"name": "Alice"}, "hello"]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.LIST

    def test_detect_nested_arrays_as_list(self):
        """Test nested arrays detected as list."""
        arr = [[1, 2], [3, 4], [5, 6]]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.LIST


class TestIsPrimitive:
    """Test primitive type detection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_string_is_primitive(self):
        """Test string is primitive."""
        assert self.encoder._is_primitive("hello") is True

    def test_int_is_primitive(self):
        """Test int is primitive."""
        assert self.encoder._is_primitive(42) is True

    def test_float_is_primitive(self):
        """Test float is primitive."""
        assert self.encoder._is_primitive(3.14) is True

    def test_bool_is_primitive(self):
        """Test bool is primitive."""
        assert self.encoder._is_primitive(True) is True
        assert self.encoder._is_primitive(False) is True

    def test_none_is_primitive(self):
        """Test None is primitive."""
        assert self.encoder._is_primitive(None) is True

    def test_list_not_primitive(self):
        """Test list is not primitive."""
        assert self.encoder._is_primitive([1, 2, 3]) is False

    def test_dict_not_primitive(self):
        """Test dict is not primitive."""
        assert self.encoder._is_primitive({"key": "value"}) is False


class TestEncodeInline:
    """Test inline array encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_encode_inline_integers(self):
        """Test encoding inline integer array."""
        result = self.encoder.encode_inline("numbers", [1, 2, 3], 0)
        assert result == "numbers[3]: 1,2,3"

    def test_encode_inline_strings(self):
        """Test encoding inline string array."""
        result = self.encoder.encode_inline("tags", ["a", "b", "c"], 0)
        assert result == "tags[3]: a,b,c"

    def test_encode_inline_mixed_primitives(self):
        """Test encoding inline mixed primitives."""
        result = self.encoder.encode_inline("mixed", [1, "hello", True], 0)
        assert result == "mixed[3]: 1,hello,true"

    def test_encode_inline_with_indentation(self):
        """Test encoding inline with indentation."""
        result = self.encoder.encode_inline("tags", ["x", "y"], 1)
        assert result == "  tags[2]: x,y"

    def test_encode_inline_empty_array(self):
        """Test encoding empty inline array."""
        result = self.encoder.encode_inline("empty", [], 0)
        assert result == "empty[0]: "

    def test_encode_inline_with_pipe_delimiter(self):
        """Test encoding inline with pipe delimiter."""
        encoder = ArrayEncoder(
            StringEncoder(Delimiter.PIPE),
            NumberEncoder(),
            IndentationManager()
        )
        result = encoder.encode_inline("tags", ["a", "b"], 0)
        assert result == "tags[2|]: a|b"


class TestEncodeTabular:
    """Test tabular array encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_encode_tabular_simple(self):
        """Test encoding simple tabular array."""
        arr = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        result = self.encoder.encode_tabular("users", arr, 0)

        assert len(result) == 3  # Header + 2 rows
        assert result[0] == "users[2]{id,name}:"
        assert result[1] == "  1,Alice"
        assert result[2] == "  2,Bob"

    def test_encode_tabular_single_row(self):
        """Test encoding tabular with single row."""
        arr = [{"id": 1, "name": "Alice"}]
        result = self.encoder.encode_tabular("users", arr, 0)

        assert len(result) == 2  # Header + 1 row
        assert result[0] == "users[1]{id,name}:"
        assert result[1] == "  1,Alice"

    def test_encode_tabular_with_indentation(self):
        """Test encoding tabular with indentation."""
        arr = [{"x": 1, "y": 2}]
        result = self.encoder.encode_tabular("point", arr, 1)

        assert result[0] == "  point[1]{x,y}:"
        assert result[1] == "    1,2"

    def test_encode_tabular_preserves_field_order(self):
        """Test tabular encoding preserves field order."""
        arr = [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"}
        ]
        result = self.encoder.encode_tabular("people", arr, 0)

        assert "name,age,city" in result[0]

    def test_encode_tabular_with_pipe_delimiter(self):
        """Test encoding tabular with pipe delimiter."""
        encoder = ArrayEncoder(
            StringEncoder(Delimiter.PIPE),
            NumberEncoder(),
            IndentationManager()
        )
        arr = [{"a": 1, "b": 2}]
        result = encoder.encode_tabular("data", arr, 0)

        assert result[0] == "data[1|]{a|b}:"
        assert result[1] == "  1|2"


class TestEncodeValue:
    """Test value encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_encode_integer(self):
        """Test encoding integer value."""
        result = self.encoder._encode_value(42)
        assert result == "42"

    def test_encode_float(self):
        """Test encoding float value."""
        result = self.encoder._encode_value(3.14)
        assert result == "3.14"

    def test_encode_string(self):
        """Test encoding string value."""
        result = self.encoder._encode_value("hello")
        assert result == "hello"

    def test_encode_bool_true(self):
        """Test encoding true."""
        result = self.encoder._encode_value(True)
        assert result == "true"

    def test_encode_bool_false(self):
        """Test encoding false."""
        result = self.encoder._encode_value(False)
        assert result == "false"

    def test_encode_none(self):
        """Test encoding None."""
        result = self.encoder._encode_value(None)
        assert result == "null"

    def test_encode_string_needing_quotes(self):
        """Test encoding string that needs quotes."""
        result = self.encoder._encode_value("hello world")
        assert result == '"hello world"'


class TestEdgeCases:
    """Test edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA),
            NumberEncoder(),
            IndentationManager()
        )

    def test_detect_array_with_boolean_primitives(self):
        """Test detecting array with booleans."""
        result = self.encoder.detect_array_form([True, False, True])
        assert result == ArrayForm.INLINE

    def test_detect_array_with_null_values(self):
        """Test detecting array with None values."""
        result = self.encoder.detect_array_form([None, None, None])
        assert result == ArrayForm.INLINE

    def test_encode_inline_with_nulls(self):
        """Test encoding inline array with nulls."""
        result = self.encoder.encode_inline("vals", [1, None, 3], 0)
        assert result == "vals[3]: 1,null,3"

    def test_encode_tabular_with_nulls(self):
        """Test encoding tabular with null values."""
        arr = [{"a": 1, "b": None}, {"a": None, "b": 2}]
        result = self.encoder.encode_tabular("data", arr, 0)

        assert result[1] == "  1,null"
        assert result[2] == "  null,2"

    def test_detect_array_all_same_empty_dicts(self):
        """Test detecting array of empty dicts."""
        arr = [{}, {}]
        result = self.encoder.detect_array_form(arr)
        # Empty dicts have same keys (none), so should be tabular
        assert result == ArrayForm.TABULAR
