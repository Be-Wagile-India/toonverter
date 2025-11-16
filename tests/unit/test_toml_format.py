"""Comprehensive tests for TOML format adapter."""

import pytest
try:
    import tomli
    import tomli_w
    TOML_AVAILABLE = True
except ImportError:
    try:
        import toml
        TOML_AVAILABLE = True
    except ImportError:
        TOML_AVAILABLE = False

from toonverter.formats.toml_format import TomlFormatAdapter as TOMLFormat
from toonverter.core.exceptions import DecodingError


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed")
class TestTOMLEncoding:
    """Test TOML encoding functionality."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, {})
        assert 'name = "Alice"' in result or "name = 'Alice'" in result
        assert "age = 30" in result

    def test_encode_section(self):
        """Test encoding section."""
        data = {"database": {"host": "localhost", "port": 5432}}
        result = self.adapter.encode(data, {})
        assert "[database]" in result
        assert "host" in result
        assert "port" in result

    def test_encode_array(self):
        """Test encoding array."""
        data = {"items": [1, 2, 3]}
        result = self.adapter.encode(data, {})
        assert "items" in result

    def test_encode_mixed_types(self):
        """Test encoding mixed types."""
        data = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "bool": True
        }
        result = self.adapter.encode(data, {})
        # Just verify it encodes without error
        assert result


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed")
class TestTOMLDecoding:
    """Test TOML decoding functionality."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_decode_simple(self):
        """Test decoding simple TOML."""
        toml_str = 'name = "Alice"\nage = 30'
        result = self.adapter.decode(toml_str, {})
        assert result == {"name": "Alice", "age": 30}

    def test_decode_section(self):
        """Test decoding section."""
        toml_str = "[database]\nhost = \"localhost\"\nport = 5432"
        result = self.adapter.decode(toml_str, {})
        assert result == {"database": {"host": "localhost", "port": 5432}}

    def test_decode_array(self):
        """Test decoding array."""
        toml_str = "items = [1, 2, 3]"
        result = self.adapter.decode(toml_str, {})
        assert result == {"items": [1, 2, 3]}

    def test_decode_boolean(self):
        """Test decoding boolean."""
        toml_str = "active = true\ninactive = false"
        result = self.adapter.decode(toml_str, {})
        assert result == {"active": True, "inactive": False}

    def test_decode_invalid_toml(self):
        """Test decoding invalid TOML."""
        with pytest.raises(DecodingError):
            self.adapter.decode("invalid toml = ", {})


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed")
class TestTOMLRoundtrip:
    """Test TOML roundtrip."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_roundtrip_section(self):
        """Test section roundtrip."""
        data = {"database": {"host": "localhost", "port": 5432}}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data
