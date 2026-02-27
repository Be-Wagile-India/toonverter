"""Tests for the main TOON encoder."""

import os
from unittest import mock

import pytest

from toonverter.core.config import PARALLELISM_THRESHOLD
from toonverter.core.spec import ToonEncodeOptions
from toonverter.encoders.toon_encoder import ToonEncoder, _convert_options, encode


class TestToonEncoder:
    """Test ToonEncoder functionality."""

    def test_init_default_parallelism_threshold(self):
        """Test ToonEncoder initializes with default parallelism threshold."""
        encoder = ToonEncoder()
        assert encoder._parallelism_threshold == PARALLELISM_THRESHOLD

    def test_init_custom_parallelism_threshold_from_options(self):
        """Test ToonEncoder initializes with custom parallelism threshold from options."""
        options = ToonEncodeOptions(parallelism_threshold=50)
        encoder = ToonEncoder(options=options)
        assert encoder._parallelism_threshold == 50

    def test_encode_object_correctness_for_large_objects(self):
        """Test encode_object correctness for objects (formerly testing parallelism)."""
        # Set a low threshold (though unused for parallelism now in Python)
        options = ToonEncodeOptions(parallelism_threshold=2)
        encoder = ToonEncoder(options=options)

        large_obj = {"k1": 1, "k2": 2, "k3": 3}

        encoded_output = encoder.encode_object(large_obj, 0)
        expected_output = [
            "k1: 1",
            "k2: 2",
            "k3: 3",
        ]
        assert encoded_output == expected_output

    def test_encode_object_correctness_for_small_objects(self):
        """Test encode_object correctness for small objects."""
        options = ToonEncodeOptions(parallelism_threshold=10)
        encoder = ToonEncoder(options=options)

        small_obj = {"k1": 1, "k2": 2}

        encoded_output = encoder.encode_object(small_obj, 0)

        expected_output = [
            "k1: 1",
            "k2: 2",
        ]
        assert encoded_output == expected_output

    @mock.patch("toonverter.encoders.toon_encoder.ToonEncoder")
    def test_encode_with_user_options_instantiation(self, mock_toon_encoder):
        """Test convenience encode function passes options to ToonEncoder."""
        options = ToonEncodeOptions(parallelism_threshold=2)
        large_obj = {"k1": 1, "k2": 2, "k3": 3}

        # Configure the mock instance that will be returned by mock_toon_encoder()
        mock_encoder_instance = mock_toon_encoder.return_value
        mock_encoder_instance.encode.return_value = "k1: 1\nk2: 2\nk3: 3"

        # Call the convenience function
        encoded_output = encode(large_obj, options=options)

        # Verify ToonEncoder was instantiated with correct options
        mock_toon_encoder.assert_called_once()
        assert isinstance(mock_toon_encoder.call_args[0][0], ToonEncodeOptions)
        assert mock_toon_encoder.call_args[0][0].parallelism_threshold == 2

        # Verify the encode method of the mock instance was called with the data
        mock_encoder_instance.encode.assert_called_once_with(large_obj)
        assert encoded_output == "k1: 1\nk2: 2\nk3: 3"

    def test_encode_with_user_options_correctness(self):
        """Test convenience encode function correctness."""
        options = ToonEncodeOptions(parallelism_threshold=10)
        small_obj = {"k1": 1, "k2": 2}

        encoded_output = encode(small_obj, options=options)
        expected_output = "k1: 1\nk2: 2"
        assert encoded_output == expected_output

    @mock.patch.dict(os.environ, {"TOON_PARALLELISM_THRESHOLD": "1"})
    @mock.patch("toonverter.encoders.toon_encoder.ToonEncoder")
    def test_encode_respects_global_parallelism_threshold_from_env(self, mock_toon_encoder):
        """Test encode function respects global parallelism threshold from environment variable."""
        large_obj = {"k1": 1, "k2": 2, "k3": 3}
        expected_output = "mocked output for env"

        mock_encoder_instance = mock_toon_encoder.return_value
        mock_encoder_instance.encode.return_value = expected_output

        actual_output = encode(large_obj, options=None)

        # Verify ToonEncoder was instantiated with None, indicating _convert_options passed through None
        mock_toon_encoder.assert_called_once_with(None)

        # Verify encode method of the instance was called
        mock_encoder_instance.encode.assert_called_once_with(large_obj)
        assert actual_output == expected_output

    @mock.patch.dict(os.environ, {"TOON_PARALLELISM_THRESHOLD": "100"})
    def test_encode_correctness_with_env_vars(self):
        """Test encode function correctness when environment variables are set."""
        large_obj = {"k1": 1, "k2": 2, "k3": 3}
        encoded_output = encode(large_obj, options=None)
        expected_output = "k1: 1\nk2: 2\nk3: 3"
        assert encoded_output == expected_output

    def test_encode_with_optimization_hook(self):
        """Test that encode calls ContextOptimizer when token_budget is provided."""
        from toonverter.core.spec import ToonEncodeOptions

        data = {"large": "data" * 100}
        options = ToonEncodeOptions(token_budget=10)

        with mock.patch("toonverter.encoders.toon_encoder.ContextOptimizer") as mock_opt_cls:
            mock_opt_instance = mock_opt_cls.return_value
            mock_opt_instance.optimize.return_value = {"small": "data"}

            encoder = ToonEncoder(options)
            result = encoder.encode(data)

            mock_opt_cls.assert_called_once()
            assert "small: data" in result

    def test_encode_rust_error_fallback(self):
        """Test that encode falls back to Python when Rust encoder fails."""
        from toonverter.core.spec import ToonEncodeOptions

        data = {"key": "value"}
        options = ToonEncodeOptions()

        with (
            mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", True),
            mock.patch("toonverter.encoders.toon_encoder.rust_core") as mock_rust,
        ):
            # Simulate a general exception in Rust
            mock_rust.encode_toon.side_effect = Exception("Rust crash")
            encoder = ToonEncoder(options)
            result = encoder.encode(data)

            # Should have fallen back to Python
            assert "key: value" in result

    def test_encode_rust_value_error_raises_encoding_error(self):
        """Test that Rust ValueError is mapped to EncodingError."""
        from toonverter.core.exceptions import EncodingError
        from toonverter.core.spec import ToonEncodeOptions

        data = {"key": "value"}
        options = ToonEncodeOptions()

        with (
            mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", True),
            mock.patch("toonverter.encoders.toon_encoder.rust_core") as mock_rust,
        ):
            mock_rust.encode_toon.side_effect = ValueError("Bad data")
            encoder = ToonEncoder(options)
            with pytest.raises(EncodingError, match=r"Failed to encode data \(Rust\)"):
                encoder.encode(data)

    def test_encode_primitive_root(self):
        """Test encoding a primitive value at the root."""
        assert encode(42) == "42"
        assert encode("hello") == "hello"
        assert encode(True) == "true"

    def test_encode_empty_nested_object(self):
        """Test encoding an empty nested object."""
        data = {"parent": {}}
        assert "parent: {}" in encode(data)

    def test_encode_unsupported_type_raises_validation_error(self):
        """Test that unsupported types raise ValidationError."""
        from toonverter.core.exceptions import ValidationError

        data = {"key": {1, 2}}
        encoder = ToonEncoder()
        with (
            mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False),
            pytest.raises(ValidationError, match="Unsupported type"),
        ):
            encoder.encode(data)

    @mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False)
    def test_encode_root_array_forms_python(self):
        """Test different forms of root arrays using Python encoder."""
        # Inline
        assert encode([1, 2, 3]) == "[3]: 1,2,3"
        # Tabular
        tabular_data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        result = encode(tabular_data)
        assert "[2]{a,b}:" in result
        list_data = [1, {"a": 1}]
        result = encode(list_data)
        assert "[2]:" in result

    @mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False)
    def test_encode_empty_object_python(self):
        """Test encoding empty objects in Python."""
        encoder = ToonEncoder()
        assert encoder.encode_object({}, 0) == []
        assert encoder.encode({}) == ""

    @mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False)
    def test_encode_single_item_key_folding_no_match(self):
        """Test _encode_single_item with key folding disabled or not matching."""
        from toonverter.core.spec import ToonEncodeOptions

        data = {"a": 1}
        options = ToonEncodeOptions(key_folding="none")
        encoder = ToonEncoder(options)
        assert "a: 1" in encoder.encode(data)

    @mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False)
    def test_encode_various_primitives_python(self):
        """Test primitive value encoding in Python."""
        encoder = ToonEncoder()
        assert encoder._encode_value(None) == "null"
        assert encoder._encode_value(True) == "true"
        assert encoder._encode_value(123) == "123"
        assert encoder._encode_value(1.23) == "1.23"
        assert encoder._encode_value("test") == "test"

    def test_encode_recursion_limit_raises_encoding_error(self):
        """Test that reaching recursion limit raises EncodingError."""
        import sys

        from toonverter.core.exceptions import EncodingError

        # Create deeply nested dict to hit Python's recursion limit
        limit = sys.getrecursionlimit()
        data = {}
        curr = data
        for _ in range(limit + 100):
            curr["a"] = {}
            curr = curr["a"]

        encoder = ToonEncoder()
        with (
            mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False),
            pytest.raises(EncodingError, match=r"Maximum recursion depth|maximum recursion depth"),
        ):
            encoder.encode(data)

    @mock.patch("toonverter.encoders.toon_encoder.USE_RUST_ENCODER", False)
    def test_encode_nested_arrays_python(self):
        """Test nested array forms in Python."""
        # Nested Inline (actually becomes list because of nesting detection)
        data = {"outer": [1, [2, 3]]}
        result = encode(data)
        # Python encoder detects list form for mixed/nested by default in some cases
        assert "outer[2]:" in result
        assert "- 1" in result
        assert "[2]: 2,3" in result

        # Nested Tabular (array of objects) - may become list if single element
        data2 = {"outer": [{"inner": [1, 2]}]}
        result2 = encode(data2)
        assert "outer[1]:" in result2
        assert "inner[2]: 1,2" in result2
        assert "  - 1" in result

    def test_encode_single_item_key_folding(self):
        """Test key folding in _encode_single_item."""
        from toonverter.core.spec import ToonEncodeOptions

        data = {"a": {"b": 1}}
        options = ToonEncodeOptions(key_folding="safe")
        encoder = ToonEncoder(options)

        # Should fold to a.b: 1
        result = encoder.encode(data)
        assert "a.b: 1" in result

    def test_convert_options_from_encode_options(self):
        """Test conversion of user-facing EncodeOptions."""
        from toonverter.core.types import EncodeOptions

        # Test compact
        opts = EncodeOptions(compact=True)
        converted = _convert_options(opts)
        assert converted.indent_size == 0

        # Test custom indent
        opts = EncodeOptions(indent=4)
        converted = _convert_options(opts)
        assert converted.indent_size == 4

        # Test with budget
        opts = EncodeOptions(token_budget=100)
        converted = _convert_options(opts)
        assert converted.token_budget == 100
