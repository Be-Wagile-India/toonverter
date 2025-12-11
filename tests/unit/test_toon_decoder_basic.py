import pytest

from toonverter.core.exceptions import ValidationError
from toonverter.core.spec import ToonDecodeOptions  # To ensure no strict/type_inference for Rust
from toonverter.decoders.toon_decoder import ToonDecoder


class TestToonDecoderBasicCoverage:
    # Use a fixture to ensure a fresh decoder instance for each test
    @pytest.fixture
    def decoder(self):
        # Explicitly set options to ensure Python decoder path and simple behavior
        # Setting strict=False and type_inference=False ensures the Python decoder path is taken
        # for empty/whitespace strings without complex mocking of USE_RUST_DECODER.
        return ToonDecoder(options=ToonDecodeOptions(strict=False, type_inference=False))

    @pytest.fixture
    def decoder_with_type_inference(self):
        return ToonDecoder(options=ToonDecodeOptions(strict=False, type_inference=True))

    def test_decode_empty_string(self, decoder):
        assert decoder.decode("") == {}

    def test_decode_whitespace_only_string(self, decoder):
        assert decoder.decode("   \n\n  ") == {}

    def test_decode_primitive_null(self, decoder):
        # With type_inference=False, "null" should remain string "null" if lexer returns IDENTIFIER.
        # But if lexer correctly identifies it as TokenType.NULL, it becomes None.
        # Per the spec, bare "null" is a primitive, so it goes to _token_to_value
        # which will convert TokenType.NULL to None regardless of type_inference.
        # So expected output is None.
        assert decoder.decode("null") is None

    def test_decode_primitive_boolean_true(self, decoder):
        # Similar to null, "true" should decode to True regardless of type_inference.
        assert decoder.decode("true") is True

    def test_decode_primitive_number(self, decoder):
        # Similar to null/true, "123" should decode to int 123 regardless of type_inference.
        assert decoder.decode("123") == 123

    def test_decode_root_unquoted_string_primitive(self, decoder):
        # Covers _detect_root_form for IDENTIFIER as primitive, with type_inference=False
        assert decoder.decode("bare_string") == "bare_string"

    def test_decode_root_implicit_object(self, decoder):
        # Covers _detect_root_form for OBJECT, and _parse_root_object
        assert decoder.decode("key: value") == {"key": "value"}

    def test_decode_root_dash_array(self, decoder):
        # Covers _detect_root_form for ARRAY (DASH), and _parse_root_array
        # Requires type_inference=False, so "item1" remains a string.
        assert decoder.decode("- item1") == ["item1"]

    def test_decode_simple_nested_object(self, decoder):
        # Covers _parse_value for nested objects and _parse_nested_object
        toon_str = "key:\n  nested_key: nested_value"
        expected = {"key": {"nested_key": "nested_value"}}
        assert decoder.decode(toon_str) == expected

    def test_decode_object_with_empty_nested_value(self, decoder):
        # Covers _parse_nested_object when a key has no value, expecting None
        toon_str = "key:\n  nested_key:"
        expected = {"key": {"nested_key": None}}
        assert decoder.decode(toon_str) == expected

    # --- New tests for coverage ---

    def test_decode_inline_object_in_list_array(self, decoder):
        # Covers _parse_inline_object method (lines 452-520)
        toon_str = "- name: Alice\n  age: 30"
        expected = [{"name": "Alice", "age": 30}]
        assert decoder.decode(toon_str) == expected

    def test_decode_inline_object_in_list_array_with_none_value(self, decoder):
        # Covers _parse_inline_object when value is None (lines 476-479)
        toon_str = "- name:\n  age: 30"
        expected = [{"name": None, "age": 30}]
        assert decoder.decode(toon_str) == expected

    def test_decode_inline_array_length_mismatch_strict_mode(self):
        # Covers _parse_inline_array strict length validation (lines 666-667)
        decoder = ToonDecoder(options=ToonDecodeOptions(strict=True, type_inference=False))
        toon_str = "values[3]: 1,2"  # Declared length 3, but only 2 values
        with pytest.raises(ValidationError, match="Array length mismatch"):
            decoder.decode(toon_str)

    # --- Tests for type_inference=True ---
    def test_decode_primitive_null_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("null") is None

    def test_decode_primitive_boolean_true_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("true") is True

    def test_decode_primitive_boolean_false_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("false") is False

    def test_decode_primitive_integer_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("123") == 123

    def test_decode_primitive_float_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("1.23") == 1.23

    def test_decode_primitive_float_negative_inferred(self, decoder_with_type_inference):
        assert decoder_with_type_inference.decode("-4.5") == -4.5

    def test_decode_primitive_string_no_inference(self, decoder_with_type_inference):
        # Should remain a string if not null, boolean, or number
        assert decoder_with_type_inference.decode("hello_world") == "hello_world"

    def test_decode_object_with_inferred_values(self, decoder_with_type_inference):
        toon_str = "key1: true\nkey2: 123\nkey3: 4.56\nkey4: hello"
        expected = {"key1": True, "key2": 123, "key3": 4.56, "key4": "hello"}
        assert decoder_with_type_inference.decode(toon_str) == expected

    def test_decode_list_array_with_inferred_values(self, decoder_with_type_inference):
        toon_str = "- true\n- 123\n- 4.56\n- hello"
        expected = [True, 123, 4.56, "hello"]
        assert decoder_with_type_inference.decode(toon_str) == expected
