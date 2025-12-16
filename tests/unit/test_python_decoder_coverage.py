from unittest.mock import patch

import pytest

from toonverter.core.exceptions import DecodingError, ValidationError
from toonverter.core.spec import ToonDecodeOptions
from toonverter.decoders.toon_decoder import decode


# Constants for reuse
SIMPLE_OBJECT = "key: value"
NESTED_OBJECT = "parent:\n  child: value"
INLINE_ARRAY = "[3]: 1, 2, 3"
TABULAR_ARRAY = """[2]{id, name}:
  1, Alice
  2, Bob
"""
LIST_ARRAY = """[2]:
  - item1
  - item2
"""
ROOT_LIST_ARRAY = """- item1
- item2
"""


@pytest.fixture
def force_python_decoder():
    """Fixture to ensure USE_RUST_DECODER is False for these tests."""
    with patch("toonverter.decoders.toon_decoder.USE_RUST_DECODER", False):
        yield


@pytest.mark.usefixtures("force_python_decoder")
class TestToonDecoderPythonCoverage:
    """Tests specifically targeting the Python implementation of the decoder."""

    def test_root_primitive(self):
        assert decode("42") == 42
        assert decode('"string"') == "string"
        assert decode("null") is None
        assert decode("true") is True

    def test_root_empty(self):
        assert decode("") == {}
        assert decode("   \n  ") == {}

    def test_root_object_simple(self):
        assert decode("key: value") == {"key": "value"}
        assert decode('key: "value"') == {"key": "value"}
        # Test missing colon
        with pytest.raises(DecodingError, match="Expected ':'"):
            decode("key value")

    def test_root_object_with_array_value(self):
        # key[N]: value syntax
        data = "numbers[3]: 1, 2, 3"
        assert decode(data) == {"numbers": [1, 2, 3]}

    def test_root_array_list_implicit(self):
        # - item1
        # - item2
        data = "- 1\n- 2"
        assert decode(data) == [1, 2]

    def test_root_array_explicit(self):
        assert decode("[2]: 1, 2") == [1, 2]

    def test_inline_array_parsing(self):
        # Test delimiters
        assert decode("[3]: 1, 2, 3") == [1, 2, 3]

    def test_inline_array_validation(self):
        # Length mismatch strict - extra items result in trailing tokens error
        options = ToonDecodeOptions(strict=True)
        from toonverter.core.exceptions import DecodingError

        with pytest.raises(DecodingError, match="Extra tokens"):
            decode("[2]: 1, 2, 3", options=options)

    def test_tabular_array_parsing(self):
        data = """[2]{col1, col2}:
  val1, val2
  val3, val4
"""
        expected = [{"col1": "val1", "col2": "val2"}, {"col1": "val3", "col2": "val4"}]
        assert decode(data) == expected

    def test_tabular_array_validation(self):
        data = """[1]{col1, col2}:
  val1
"""
        options = ToonDecodeOptions(strict=True)
        with pytest.raises(
            ValidationError, match="Row width mismatch: declared 2 fields, got 1 values"
        ):
            decode(data, options=options)

    def test_list_array_nested_objects(self):
        # This targets _parse_list_array and _parse_inline_object/nested logic
        data = """[2]:
  - name: Alice
    age: 30
  - name: Bob
    age: 25
"""
        expected = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        assert decode(data) == expected

    def test_list_array_inline_object_simple(self):
        data = """[1]:
  - key: value
"""
        assert decode(data) == [{"key": "value"}]

    def test_nested_object_structure(self):
        data = """root:
  level1:
    level2: value
"""
        assert decode(data) == {"root": {"level1": {"level2": "value"}}}

    def test_nested_object_mixed_inline(self):
        data = """
parent:
  child1: value1
  child2: value2
"""
        assert decode(data) == {"parent": {"child1": "value1", "child2": "value2"}}
        # Test strict=False, type_inference=False
        options = ToonDecodeOptions(type_inference=False)
        assert decode("key: 123", options=options) == {"key": 123}

    def test_type_inference_options(self):
        # Test strict=False, type_inference=False
        options = ToonDecodeOptions(type_inference=False)
        assert decode("key: 123", options=options) == {"key": 123}
        assert decode("key: true", options=options) == {"key": True}
        assert decode("key: null", options=options) == {"key": None}

    def test_parse_error_unexpected_token(self):
        with pytest.raises(DecodingError):
            decode("key: value }")  # Unexpected closing brace/invalid syntax

    def test_parse_error_root_array_start(self):
        # This should be a primitive string "]"
        assert decode("]") == "]"

    def test_parse_error_nested_object(self):
        data = """root:
  key value
"""
        with pytest.raises(DecodingError, match="Expected ':'"):
            decode(data)

    def test_inline_array_empty_items(self):
        # Coverage for "Allow empty strings as values if they result from splitting"
        # [3]: 1,,3  -> 1, None, 3
        data = "[3]: 1,,3"
        assert decode(data) == [1, None, 3]

    def test_lexer_edge_cases(self):
        # Ensure lexer handles weird indentation or spacing
        data = "key:    value"
        assert decode(data) == {"key": "value"}
