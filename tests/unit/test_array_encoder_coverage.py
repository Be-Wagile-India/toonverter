from unittest.mock import Mock

import pytest

from toonverter.core.spec import Delimiter
from toonverter.encoders.array_encoder import ArrayEncoder
from toonverter.encoders.indentation import IndentationManager
from toonverter.encoders.number_encoder import NumberEncoder
from toonverter.encoders.string_encoder import StringEncoder


class TestArrayEncoderCoverage:
    @pytest.fixture
    def encoders(self):
        indent_mgr = IndentationManager()
        str_enc = StringEncoder(Delimiter.COMMA)
        num_enc = NumberEncoder()
        return str_enc, num_enc, indent_mgr

    @pytest.fixture
    def array_encoder(self, encoders):
        str_enc, num_enc, indent_mgr = encoders
        return ArrayEncoder(str_enc, num_enc, indent_mgr)

    @pytest.fixture
    def value_encoder(self):
        # Mock encoder that needs to provide encode_object
        mock = Mock()
        # Default behavior
        mock.encode_object.return_value = ["key: val"]
        return mock

    def test_encode_list_nested_empty_list(self, array_encoder, value_encoder):
        # Covers: if not item: lines.append(f"{item_indent}- [0]:")
        arr = [[]]
        lines = array_encoder.encode_list("root", arr, 0, value_encoder)
        # Indent 0 -> "root...:"
        # item indent (depth+1) -> 2 spaces
        assert any("- [0]:" in line for line in lines)

    def test_encode_list_nested_complex_list(self, array_encoder, value_encoder):
        # Covers: nested_form != INLINE -> _encode_nested_array_item
        arr = [[{"k": "v"}]]

        value_encoder.encode_object.return_value = ["k: v"]

        lines = array_encoder.encode_list("root", arr, 0, value_encoder)
        # Check that we recursed
        assert any("- [1]:" in line for line in lines)
        assert any("- k: v" in line for line in lines)

    def test_encode_root_array_list(self, array_encoder, value_encoder):
        arr = [1, {"k": "v"}]
        value_encoder.encode_object.return_value = ["k: v"]

        lines = array_encoder.encode_root_array_list(arr, value_encoder)
        assert lines[0] == "[2]:"
        assert "  - 1" in lines
        assert "  - k: v" in lines

    def test_encode_value_fallback(self, array_encoder):
        # Covers: fallback to str(val)
        class MyObj:
            def __str__(self):
                return "myobj"

        val = MyObj()
        encoded = array_encoder._encode_value(val)
        assert encoded == "myobj"

    def test_encode_nested_array_item_recursion(self, array_encoder, value_encoder):
        # Covers: _encode_nested_array_item recursion for list
        # Input: [ [ 1 ] ]  <- nested nested list
        arr = [[1]]

        lines = array_encoder._encode_nested_array_item(arr, 0, value_encoder)
        # Header for outer: depth 0 -> no indent
        assert lines[0] == "- [1]:"

        assert any("- 1" in line for line in lines)

    def test_encode_nested_array_item_mixed(self, array_encoder, value_encoder):
        # Covers: _encode_nested_array_item with dict and primitive
        arr = [{"k": "v"}, 42]
        value_encoder.encode_object.return_value = ["k: v"]

        lines = array_encoder._encode_nested_array_item(arr, 0, value_encoder)
        assert any("- k: v" in line for line in lines)
        assert any("- 42" in line for line in lines)
