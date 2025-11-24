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

from toonverter.core.exceptions import DecodingError
from toonverter.formats.toml_format import TomlFormatAdapter as TOMLFormat


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
        data = {"string": "hello", "number": 42, "float": 3.14, "bool": True}
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
        toml_str = '[database]\nhost = "localhost"\nport = 5432'
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


class TestTOMLValidation:
    """Test TOML validation."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_validate_valid(self):
        """Test validating valid TOML."""
        assert self.adapter.validate('name = "test"') is True

    def test_validate_invalid(self):
        """Test validating invalid TOML."""
        assert self.adapter.validate("invalid toml =") is False


class TestTOMLEdgeCases:
    """Test TOML edge cases."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_encode_non_dict(self):
        """Test encoding non-dictionary data."""
        from toonverter.core.exceptions import EncodingError

        with pytest.raises(EncodingError, match="only supports dictionary"):
            self.adapter.encode(["not", "a", "dict"])

    def test_encode_write_not_available(self):
        """Test encoding when write support is not available."""
        from unittest.mock import patch

        from toonverter.core.exceptions import EncodingError

        with (
            patch("toonverter.formats.toml_format.TOML_WRITE_AVAILABLE", False),
            pytest.raises(EncodingError, match="TOML writing requires"),
        ):
            self.adapter.encode({"a": 1})

    def test_init_read_not_available(self):
        """Test initialization when read support is not available."""
        from unittest.mock import patch

        with (
            patch("toonverter.formats.toml_format.TOML_READ_AVAILABLE", False),
            pytest.raises(ImportError, match="TOML support requires"),
        ):
            TOMLFormat()

    def test_decode_non_strict(self):
        """Test non-strict decoding."""
        from toonverter.core.types import DecodeOptions

        options = DecodeOptions(strict=False)
        result = self.adapter.decode("invalid toml =", options)
        assert result == "invalid toml ="

    def test_encode_error(self):
        """Test encoding error handling."""
        from toonverter.core.exceptions import EncodingError

        class Unserializable:
            pass

        with pytest.raises(EncodingError, match="Failed to encode"):
            self.adapter.encode({"obj": Unserializable()})


class TestTOMLLegacy:
    """Tests simulating Python < 3.11 environment logic inside methods."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_legacy_encode(self):
        """Test legacy encoding path."""
        from unittest.mock import MagicMock, patch

        mock_toml = MagicMock()
        mock_toml.dumps.return_value = 'mock = "toml"'

        with (
            patch("sys.version_info", (3, 10)),
            patch("toonverter.formats.toml_format.toml", mock_toml, create=True),
        ):
            result = self.adapter.encode({"a": 1})
            assert result == 'mock = "toml"'
            mock_toml.dumps.assert_called_once()

    def test_legacy_decode(self):
        """Test legacy decoding path."""
        from unittest.mock import MagicMock, patch

        mock_toml = MagicMock()
        mock_toml.loads.return_value = {"mock": "data"}

        with (
            patch("sys.version_info", (3, 10)),
            patch("toonverter.formats.toml_format.toml", mock_toml, create=True),
        ):
            result = self.adapter.decode('mock = "toml"')
            assert result == {"mock": "data"}
            mock_toml.loads.assert_called_once()

    def test_legacy_validate(self):
        """Test legacy validation path."""
        from unittest.mock import MagicMock, patch

        mock_toml = MagicMock()

        with (
            patch("sys.version_info", (3, 10)),
            patch("toonverter.formats.toml_format.toml", mock_toml, create=True),
        ):
            assert self.adapter.validate("valid") is True
            mock_toml.loads.assert_called_once()
