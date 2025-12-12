"""Tests for the main TOON encoder."""

import os
from unittest import mock

from toonverter.core.config import PARALLELISM_THRESHOLD
from toonverter.core.spec import ToonEncodeOptions
from toonverter.encoders.toon_encoder import ToonEncoder, encode


# Mock the actual ThreadPoolExecutor to just run sequentially for testing
class MockThreadPoolExecutor:
    def __init__(self, *args, **kwargs):
        pass

    def map(self, func, iterable):
        return (func(item) for item in iterable)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


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

    @mock.patch("toonverter.encoders.toon_encoder.ThreadPoolExecutor", new=MockThreadPoolExecutor)
    def test_encode_object_uses_parallelism_for_large_objects(self):
        """Test encode_object uses ThreadPoolExecutor for objects exceeding threshold."""
        # Set a low threshold to trigger parallelism
        options = ToonEncodeOptions(parallelism_threshold=2)
        encoder = ToonEncoder(options=options)

        large_obj = {"k1": 1, "k2": 2, "k3": 3}  # Size 3 > threshold 2

        with mock.patch.object(
            encoder, "_encode_single_item", wraps=encoder._encode_single_item
        ) as mock_single_item:
            encoded_output = encoder.encode_object(large_obj, 0)

            # Verify _encode_single_item was called for each item
            assert mock_single_item.call_count == len(large_obj)

            # Since ThreadPoolExecutor is mocked to run sequentially,
            # we just check the output correctness
            expected_output = [
                "k1: 1",
                "k2: 2",
                "k3: 3",
            ]
            assert encoded_output == expected_output

    def test_encode_object_no_parallelism_for_small_objects(self):
        """Test encode_object does not use ThreadPoolExecutor for objects below threshold."""
        # Set a threshold that prevents parallelism
        options = ToonEncodeOptions(parallelism_threshold=10)
        encoder = ToonEncoder(options=options)

        small_obj = {"k1": 1, "k2": 2}  # Size 2 < threshold 10

        with mock.patch("toonverter.encoders.toon_encoder.ThreadPoolExecutor") as mock_executor:
            encoded_output = encoder.encode_object(small_obj, 0)

            # Verify ThreadPoolExecutor was NOT called
            mock_executor.assert_not_called()

            expected_output = [
                "k1: 1",
                "k2: 2",
            ]
            assert encoded_output == expected_output

    @mock.patch("toonverter.encoders.toon_encoder.ToonEncoder")
    def test_encode_with_user_options_enables_parallelism(self, mock_toon_encoder):
        """Test convenience encode function passes parallelism options to ToonEncoder and triggers parallel path."""
        options = ToonEncodeOptions(parallelism_threshold=2)
        large_obj = {"k1": 1, "k2": 2, "k3": 3}

        # Configure the mock instance that will be returned by mock_toon_encoder()
        mock_encoder_instance = mock_toon_encoder.return_value
        mock_encoder_instance.encode.return_value = "k1: 1\nk2: 2\nk3: 3"  # Mock the final output

        # Call the convenience function
        encoded_output = encode(large_obj, options=options)

        # Verify ToonEncoder was instantiated with correct options
        mock_toon_encoder.assert_called_once()
        assert isinstance(mock_toon_encoder.call_args[0][0], ToonEncodeOptions)
        assert mock_toon_encoder.call_args[0][0].parallelism_threshold == 2

        # Verify the encode method of the mock instance was called with the data
        mock_encoder_instance.encode.assert_called_once_with(large_obj)
        assert encoded_output == "k1: 1\nk2: 2\nk3: 3"

    def test_encode_with_user_options_no_parallelism(self):
        """Test convenience encode function does not use parallelism with UserEncodeOptions."""
        options = ToonEncodeOptions(parallelism_threshold=10)  # Set a high threshold
        small_obj = {"k1": 1, "k2": 2}

        with mock.patch("toonverter.encoders.toon_encoder.ThreadPoolExecutor") as mock_executor:
            encoded_output = encode(small_obj, options=options)
            mock_executor.assert_not_called()
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
    def test_encode_does_not_use_parallelism_if_env_threshold_high(self):
        """Test encode function does not use parallelism if environment threshold is high."""
        large_obj = {"k1": 1, "k2": 2, "k3": 3}
        with mock.patch("toonverter.encoders.toon_encoder.ThreadPoolExecutor") as mock_executor:
            encoded_output = encode(large_obj, options=None)
            mock_executor.assert_not_called()
            expected_output = "k1: 1\nk2: 2\nk3: 3"
            assert encoded_output == expected_output
