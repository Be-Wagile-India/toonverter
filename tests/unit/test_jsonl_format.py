import json
from datetime import datetime, timezone

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions
from toonverter.formats.jsonl_format import JsonlFormatAdapter


class TestJsonlFormatAdapter:
    def setup_method(self):
        self.adapter = JsonlFormatAdapter()

    def test_init(self):
        assert self.adapter.format_name == "jsonl"
        assert self.adapter.supports_streaming  # JSONL inherently supports streaming

    # --- Encode Tests ---

    def test_encode_empty_list(self):
        assert self.adapter.encode([]) == ""

    def test_encode_list_of_items(self):
        data = [{"name": "Alice"}, {"name": "Bob"}]
        expected = '{"name":"Alice"}\n{"name":"Bob"}'
        assert self.adapter.encode(data) == expected

    def test_encode_single_item_not_list(self):
        data = {"name": "Charlie"}
        expected = '{"name":"Charlie"}'
        assert self.adapter.encode(data) == expected

    def test_encode_with_datetime(self):
        data = [{"timestamp": datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)}]
        expected = '{"timestamp":"2023-01-01T12:00:00+00:00"}'
        assert self.adapter.encode(data) == expected

    def test_encode_type_error(self):
        class NonSerializable:
            pass

        data = [NonSerializable()]
        with pytest.raises(EncodingError) as exc_info:
            self.adapter.encode(data)
        assert "Failed to encode to JSONL" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, TypeError)

    # --- Decode Tests ---

    def test_decode_empty_string(self):
        assert self.adapter.decode("") == []

    def test_decode_whitespace_only_string(self):
        assert self.adapter.decode("   \n\t  ") == []

    def test_decode_multiple_lines(self):
        data_str = '{"name":"Alice"}\n{"name":"Bob"}'
        expected = [{"name": "Alice"}, {"name": "Bob"}]
        assert self.adapter.decode(data_str) == expected

    def test_decode_with_blank_lines(self):
        data_str = '{"name":"Alice"}\n\n   \n{"name":"Bob"}'
        expected = [{"name": "Alice"}, {"name": "Bob"}]
        assert self.adapter.decode(data_str) == expected

    def test_decode_malformed_line_strict_mode(self):
        data_str = '{"name":"Alice"}\n{"name":\n{"name":"Bob"}'
        with pytest.raises(DecodingError) as exc_info:
            self.adapter.decode(data_str, options=DecodeOptions(strict=True))
        assert "Failed to decode JSONL line 2" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)

    def test_decode_malformed_line_non_strict_mode(self):
        data_str = '{"name":"Alice"}\n{"name":\n{"name":"Bob"}'
        expected = [{"name": "Alice"}, {"name": "Bob"}]
        # In non-strict mode, malformed lines are skipped
        assert self.adapter.decode(data_str, options=DecodeOptions(strict=False)) == expected

    def test_decode_invalid_jsonl_overall(self):
        # Test case where a non-json error occurs during line processing
        data_str = "invalid jsonl string"
        with pytest.raises(DecodingError) as exc_info:
            self.adapter.decode(data_str)
        # The specific error is JSONDecodeError, but wrapped by DecodingError
        assert "Failed to decode JSONL line 1" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, json.JSONDecodeError)

    # --- Validate Tests ---

    def test_validate_valid_jsonl(self):
        data_str = '{"a":1}\n{"b":2}'
        assert self.adapter.validate(data_str)

    def test_validate_empty_string(self):
        assert self.adapter.validate("")

    def test_validate_whitespace_only(self):
        assert self.adapter.validate("   \n\t  ")

    def test_validate_invalid_jsonl(self):
        data_str = '{"a":1}\ninvalid json\n{"b":2}'
        assert not self.adapter.validate(data_str)

    def test_validate_single_invalid_line(self):
        data_str = "invalid json"
        assert not self.adapter.validate(data_str)
