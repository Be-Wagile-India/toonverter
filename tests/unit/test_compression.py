"""Tests for Smart Dictionary Compression."""

from toonverter.optimization import SmartCompressor


class TestSmartCompressor:
    def test_compress_basic_repetition(self):
        compressor = SmartCompressor(min_length=4, min_occurrences=2, prefix="@")
        data = {"a": "long_value_string", "b": "long_value_string", "c": "unique"}

        compressed = compressor.compress(data)
        assert compressed["$schema"] == "toon-sdc-v1"
        # Check if "long_value_string" is in symbols
        assert "long_value_string" in compressed["$symbols"].values()

        # Check if replaced
        payload = compressed["$payload"]
        assert payload["a"].startswith("@")
        assert payload["b"] == payload["a"]
        assert payload["c"] == "unique"

    def test_compress_keys(self):
        compressor = SmartCompressor(min_length=4, min_occurrences=2)
        data = [{"very_long_key_name": 1}, {"very_long_key_name": 2}]

        compressed = compressor.compress(data)
        payload = compressed["$payload"]

        # The key should be replaced
        key_symbol = next(iter(payload[0].keys()))
        assert key_symbol.startswith("@")
        assert payload[1][key_symbol] == 2

    def test_roundtrip(self):
        compressor = SmartCompressor()
        data = {
            "users": [
                {"id": 1, "role": "administrator", "status": "active"},
                {"id": 2, "role": "administrator", "status": "inactive"},
                {"id": 3, "role": "user", "status": "active"},
            ]
        }

        compressed = compressor.compress(data)
        restored = compressor.decompress(compressed)

        assert restored == data

    def test_nested_structures(self):
        compressor = SmartCompressor()
        data = {"a": {"b": {"c": "repeat"}}, "d": ["repeat", "repeat"]}

        compressed = compressor.compress(data)
        restored = compressor.decompress(compressed)
        assert restored == data

    def test_no_compression_if_roi_negative(self):
        # Short string, few repeats -> Overhead > Savings
        compressor = SmartCompressor(min_length=10)  # Force ignore short
        data = ["short", "short"]

        compressed = compressor.compress(data)
        # Should not define symbols for "short"
        assert "short" not in compressed["$symbols"].values()
        assert compressed["$payload"] == data
