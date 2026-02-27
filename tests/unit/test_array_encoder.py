"""Comprehensive tests for array encoder."""

from unittest.mock import Mock

from toonverter.core.spec import ArrayForm, Delimiter
from toonverter.encoders.array_encoder import ArrayEncoder
from toonverter.encoders.indentation import IndentationManager
from toonverter.encoders.number_encoder import NumberEncoder
from toonverter.encoders.string_encoder import StringEncoder


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
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
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
        arr = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
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
            {"id": 2, "email": "bob@example.com"},  # Different keys
        ]
        result = self.encoder.detect_array_form(arr)
        assert result == ArrayForm.LIST

    def test_detect_dicts_with_nested_values_as_list(self):
        """Test dicts with non-primitive values detected as list."""
        arr = [
            {"id": 1, "tags": ["a", "b"]},  # Nested list
            {"id": 2, "tags": ["c", "d"]},
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
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
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
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
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
        encoder = ArrayEncoder(StringEncoder(Delimiter.PIPE), NumberEncoder(), IndentationManager())
        result = encoder.encode_inline("tags", ["a", "b"], 0)
        assert result == "tags[2|]: a|b"


class TestEncodeTabular:
    """Test tabular array encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
        )

    def test_encode_tabular_simple(self):
        """Test encoding simple tabular array."""
        arr = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
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
            {"name": "Bob", "age": 25, "city": "LA"},
        ]
        result = self.encoder.encode_tabular("people", arr, 0)

        assert "name,age,city" in result[0]

    def test_encode_tabular_with_pipe_delimiter(self):
        """Test encoding tabular with pipe delimiter."""
        encoder = ArrayEncoder(StringEncoder(Delimiter.PIPE), NumberEncoder(), IndentationManager())
        arr = [{"a": 1, "b": 2}]
        result = encoder.encode_tabular("data", arr, 0)

        assert result[0] == "data[1|]{a|b}:"
        assert result[1] == "  1|2"


class TestEncodeList:
    """Test list array encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
        )
        self.value_encoder = Mock()
        self.value_encoder.encode_object.return_value = ["key: val"]

    def test_encode_list_simple(self):
        """Test encoding simple list array."""
        result = self.encoder.encode_list("items", [1, "a", True], 0, self.value_encoder)
        assert result[0] == "items[3]:"
        assert result[1] == "  - 1"
        assert result[2] == "  - a"
        assert result[3] == "  - true"

    def test_encode_list_nested_empty_list(self):
        """Test encoding list with nested empty list."""
        arr = [[]]
        result = self.encoder.encode_list("root", arr, 0, self.value_encoder)
        assert any("- [0]:" in line for line in result)

    def test_encode_list_nested_complex_list(self):
        """Test encoding list with nested complex list."""
        arr = [[{"k": "v"}]]
        self.value_encoder.encode_object.return_value = ["k: v"]
        result = self.encoder.encode_list("root", arr, 0, self.value_encoder)
        assert any("- [1]:" in line for line in result)
        assert any("- k: v" in line for line in result)


class TestRootArrayEncoding:
    """Test root-level array encoding."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
        )
        self.value_encoder = Mock()

    def test_encode_root_array_list(self):
        """Test encoding root-level list array."""
        arr = [1, {"k": "v"}]
        self.value_encoder.encode_object.return_value = ["k: v"]
        result = self.encoder.encode_root_array_list(arr, self.value_encoder)
        assert result[0] == "[2]:"
        assert "  - 1" in result
        assert "  - k: v" in result


class TestValueEncoding:
    """Test value encoding internal method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
        )

    def test_encode_value_fallback(self):
        """Test fallback to str(val) for unknown types."""

        class MyObj:
            def __str__(self):
                return "myobj"

        val = MyObj()
        encoded = self.encoder._encode_value(val)
        assert encoded == "myobj"


class TestInternalMethods:
    """Test internal helper methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.encoder = ArrayEncoder(
            StringEncoder(Delimiter.COMMA), NumberEncoder(), IndentationManager()
        )
        self.value_encoder = Mock()

    def test_encode_nested_array_item_recursion(self):
        """Test _encode_nested_array_item recursion."""
        arr = [[1]]
        result = self.encoder._encode_nested_array_item(arr, 0, self.value_encoder)
        assert result[0] == "- [1]:"
        assert any("- 1" in line for line in result)

    def test_encode_nested_array_item_mixed(self):
        """Test _encode_nested_array_item with mixed content."""
        arr = [{"k": "v"}, 42]
        self.value_encoder.encode_object.return_value = ["k: v"]
        result = self.encoder._encode_nested_array_item(arr, 0, self.value_encoder)
        assert any("- k: v" in line for line in result)
        assert any("- 42" in line for line in result)
