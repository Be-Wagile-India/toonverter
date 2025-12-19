"""Tests for the main TOON encoder."""

import os
from unittest import mock

from toonverter.core.config import PARALLELISM_THRESHOLD
from toonverter.core.spec import ToonEncodeOptions
from toonverter.encoders.toon_encoder import ToonEncoder, encode


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
