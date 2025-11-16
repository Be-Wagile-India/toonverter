"""Tests for base format adapter."""

import pytest
from toonverter.formats.base import BaseFormatAdapter
from toonverter.core.types import EncodeOptions, DecodeOptions


class MockFormatAdapter(BaseFormatAdapter):
    """Mock implementation of BaseFormatAdapter for testing."""

    def encode(self, data, options=None):
        """Mock encode implementation."""
        return "encoded"

    def decode(self, data_str, options=None):
        """Mock decode implementation."""
        return {"decoded": True}

    def validate(self, data_str):
        """Mock validate implementation."""
        return True


class TestBaseFormatAdapter:
    """Test BaseFormatAdapter functionality."""

    def setup_method(self):
        """Set up test adapter."""
        self.adapter = MockFormatAdapter("test")

    def test_format_name_property(self):
        """Test format_name property returns correct name."""
        assert self.adapter.format_name == "test"

    def test_init_sets_format_name(self):
        """Test __init__ sets format name."""
        adapter = MockFormatAdapter("custom")
        assert adapter.format_name == "custom"

    def test_supports_streaming_default_false(self):
        """Test supports_streaming returns False by default."""
        assert self.adapter.supports_streaming() is False

    def test_get_encode_kwargs_none_options(self):
        """Test _get_encode_kwargs with None options."""
        result = self.adapter._get_encode_kwargs(None)
        assert result == {}

    def test_get_encode_kwargs_with_options(self):
        """Test _get_encode_kwargs with EncodeOptions."""
        options = EncodeOptions(
            indent=2,
            compact=False,
            sort_keys=True,
            ensure_ascii=False
        )
        result = self.adapter._get_encode_kwargs(options)

        assert result["indent"] == 2
        assert result["sort_keys"] is True
        assert result["ensure_ascii"] is False

    def test_get_encode_kwargs_compact_mode(self):
        """Test _get_encode_kwargs with compact mode."""
        options = EncodeOptions(indent=2, compact=True)
        result = self.adapter._get_encode_kwargs(options)

        # When compact is True, indent should be None
        assert result["indent"] is None

    def test_get_decode_kwargs_none_options(self):
        """Test _get_decode_kwargs with None options."""
        result = self.adapter._get_decode_kwargs(None)
        assert result == {}

    def test_get_decode_kwargs_with_options(self):
        """Test _get_decode_kwargs with DecodeOptions."""
        options = DecodeOptions(strict=True)
        result = self.adapter._get_decode_kwargs(options)

        assert result["strict"] is True

    def test_get_decode_kwargs_non_strict(self):
        """Test _get_decode_kwargs with strict=False."""
        options = DecodeOptions(strict=False)
        result = self.adapter._get_decode_kwargs(options)

        assert result["strict"] is False
