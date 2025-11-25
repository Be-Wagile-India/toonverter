from collections.abc import Iterator

from toonverter.core.spec import ToonDecodeOptions
from toonverter.core.types import DecodeOptions
from toonverter.formats.toon_format import ToonFormatAdapter, _convert_decode_options


class TestToonFormatAdapter:
    def test_init(self):
        adapter = ToonFormatAdapter()
        assert adapter.format_name == "toon"

    def test_validate_valid(self):
        adapter = ToonFormatAdapter()
        # Simple valid TOON (looks like JSON/YAML)
        valid_toon = "key: value"
        assert adapter.validate(valid_toon) is True

    def test_validate_invalid(self):
        adapter = ToonFormatAdapter()
        # Invalid TOON (e.g., malformed structure)
        # Unclosed array should definitely fail
        invalid_toon = "[1, 2"
        assert adapter.validate(invalid_toon) is False

    def test_convert_decode_options_none(self):
        assert _convert_decode_options(None) is None

    def test_convert_decode_options_toon_options(self):
        options = ToonDecodeOptions(strict=True)
        converted = _convert_decode_options(options)
        assert converted is options

    def test_convert_decode_options_base_options(self):
        options = DecodeOptions(strict=True, type_inference=False)
        converted = _convert_decode_options(options)
        assert isinstance(converted, ToonDecodeOptions)
        assert converted.strict is True
        assert converted.type_inference is False

    def test_decode_with_options(self):
        adapter = ToonFormatAdapter()
        data = "key: value"
        options = DecodeOptions(strict=True)
        # We just want to ensure it runs without error and calls internal decode
        # mocking internal decode isn't strictly necessary if we just want coverage of the adapter wrapper
        result = adapter.decode(data, options)
        assert result == {"key": "value"}

    def test_encode_stream(self):
        adapter = ToonFormatAdapter()
        data = [{"a": 1}, {"b": 2}]
        stream = adapter.encode_stream(data)
        assert isinstance(stream, Iterator)
        result = list(stream)
        assert len(result) > 0

    def test_decode_stream(self):
        adapter = ToonFormatAdapter()
        # Use explicit array header to trigger streaming mode
        stream_data = ["[2]:\n", "- a: 1\n", "- b: 2\n"]
        decoded_stream = adapter.decode_stream(iter(stream_data))
        assert isinstance(decoded_stream, Iterator)
        result = list(decoded_stream)
        assert result == [{"a": 1}, {"b": 2}]
