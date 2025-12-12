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

    def test_decompress_non_toon_sdc_v1_schema_missing_symbols(self):
        # Covers line 50: if "$symbols" not in compressed_data or "$payload" not in compressed_data:
        compressor = SmartCompressor()
        # Missing $symbols, should return data as-is if schema is not "toon-sdc-v1"
        compressed_data = {"$schema": "not-toon-sdc-v1", "$payload": {"key": "value"}}
        restored = compressor.decompress(compressed_data)
        assert restored == compressed_data

    def test_decompress_non_toon_sdc_v1_schema_missing_payload(self):
        # Covers line 50: if "$symbols" not in compressed_data or "$payload" not in compressed_data:
        compressor = SmartCompressor()
        # Missing $payload, should return data as-is if schema is not "toon-sdc-v1"
        compressed_data = {"$schema": "not-toon-sdc-v1", "$symbols": {"@0": "test"}}
        restored = compressor.decompress(compressed_data)
        assert restored == compressed_data

    def test_decompress_non_toon_sdc_v1_schema_missing_both(self):
        # Covers line 50: if "$symbols" not in compressed_data or "$payload" not in compressed_data:
        compressor = SmartCompressor()
        # Missing both, should return data as-is if schema is not "toon-sdc-v1"
        compressed_data = {"$schema": "not-toon-sdc-v1"}
        restored = compressor.decompress(compressed_data)
        assert restored == compressed_data

    def test_decompress_non_toon_sdc_v1_schema_with_symbols_and_payload(self):
        # Covers the branch 49->52: schema != "toon-sdc-v1" but symbols and payload exist
        compressor = SmartCompressor()
        compressed_data = {
            "$schema": "some-other-schema",
            "$symbols": {"@0": "some_value"},
            "$payload": "@0",
        }
        # In this case, the method should proceed to attempt decompression,
        # so the result should be the resolved payload, not the original compressed_data.
        # This will actually attempt to decompress the "@0" symbol.
        expected_decompressed = compressor._resolve(
            compressed_data["$payload"], compressed_data["$symbols"]
        )
        restored = compressor.decompress(compressed_data)
        assert restored == expected_decompressed
