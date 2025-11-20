"""Comprehensive tests for TOML format adapter."""

import sys

import pytest

# Imports for the adapter and core types must be at the top of the file (E402 fix)
from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.toml_format import TomlFormatAdapter as TOMLFormat


# Check for TOML availability, mimicking the logic in toml_format.py
TOML_AVAILABLE = False
if sys.version_info >= (3, 11):
    try:
        # tomllib (built-in reader) and tomli_w (writer) are needed for 3.11+
        import tomli_w

        TOML_AVAILABLE = True
    except ImportError as e:
        # tomli_w is not available; TOML tests will be skipped.
        # Assigning the exception 'e' is a common no-op replacement for 'pass'.
        _ = e
else:
    try:
        # toml package handles both reading and writing on older Python versions.
        import toml

        TOML_AVAILABLE = True
    except ImportError as e:
        # toml is not available; TOML tests will be skipped.
        # Assigning the exception 'e' is a common no-op replacement for 'pass'.
        _ = e


# Helper function to safely import the module under test for monkeypatching
# This is necessary to modify the global state (TOML_READ_AVAILABLE, TOML_WRITE_AVAILABLE)
def get_toml_format_module():
    """Attempts to import the toml_format module for monkeypatching."""
    try:
        # Note: This path must match your project structure to work correctly
        from toonverter.formats import toml_format

        return toml_format
    except ImportError:
        pytest.skip("Could not import toml_format module for monkeypatching.")
        return None


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed or cannot be imported")
class TestTOMLEncoding:
    """Test TOML encoding functionality."""

    def setup_method(self):
        """Set up TOML format adapter."""
        # Initialize the adapter, which checks for read availability
        self.adapter = TOMLFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, None)
        assert 'name = "Alice"' in result or "name = 'Alice'" in result
        assert "age = 30" in result

    def test_encode_section(self):
        """Test encoding section."""
        data = {"database": {"host": "localhost", "port": 5432}}
        result = self.adapter.encode(data, None)
        assert "[database]" in result
        assert 'host = "localhost"' in result or "host = 'localhost'" in result
        assert "port = 5432" in result

    def test_encode_array(self):
        """Test encoding array."""
        data = {"items": [1, 2, 3]}
        result = self.adapter.encode(data, None)
        # Check for the key, brackets, and elements, regardless of line breaks or spacing.
        assert "items =" in result
        assert "[" in result
        assert "]" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result

    def test_encode_array_of_tables(self):
        """Test encoding an array of tables (e.g., list of dictionaries)."""
        data = {"servers": [{"ip": "1.1.1.1", "name": "web"}, {"ip": "2.2.2.2", "name": "db"}]}
        result = self.adapter.encode(data, None)
        # The library may use '[[servers]]' (Array of Tables) or 'servers = [ {..}, {..} ]' (Inline Table Array).
        # We assert the presence of key elements regardless of the specific formatting.
        assert "servers" in result
        assert 'ip = "1.1.1.1"' in result or "ip = '1.1.1.1'" in result
        assert 'name = "db"' in result or "name = 'db'" in result

    def test_encode_mixed_types(self):
        """Test encoding mixed types."""
        data = {"string": "hello", "number": 42, "float": 3.14, "bool": True, "date": [2024, 1, 1]}
        result = self.adapter.encode(data, None)
        # Just verify it encodes without error and contains key elements
        assert "string = " in result
        assert "number = 42" in result
        assert "float = 3.14" in result
        assert "bool = true" in result

    def test_encode_non_dict_input(self):
        """Test encoding non-dictionary input raises EncodingError (initial check)."""
        data = [1, 2, 3]
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "only supports dictionary data" in str(excinfo.value)

    def test_encode_unencodable_data(self):
        """Test encoding data with an unencodable type (e.g., a set) raises EncodingError (internal failure)."""
        # Sets are not directly supported by TOML and should trigger TypeError/ValueError.
        data = {"key": {1, 2, 3}}
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "Failed to encode to TOML" in str(excinfo.value)

    def test_encode_with_options(self):
        """Test encoding when an EncodeOptions instance is passed (currently no configurable TOML options)."""
        data = {"key": "value"}
        options = EncodeOptions()
        result = self.adapter.encode(data, options)
        assert 'key = "value"' in result or "key = 'value'" in result

    def test_encode_no_write_library(self, monkeypatch):
        """Test encoding failure when TOML_WRITE_AVAILABLE is False (Targets lines 51-56)."""
        toml_format = get_toml_format_module()
        if not toml_format:
            return

        # Mock TOML_WRITE_AVAILABLE to False to hit the EncodingError path
        monkeypatch.setattr(toml_format, "TOML_WRITE_AVAILABLE", False)

        # Re-initialize the adapter instance to ensure the mocked global state is used
        adapter = toml_format.TomlFormatAdapter()

        data = {"key": "value"}

        with pytest.raises(EncodingError) as excinfo:
            adapter.encode(data, None)

        expected_msg_part = "TOML writing requires 'toml' package"
        assert expected_msg_part in str(excinfo.value)


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed or cannot be imported")
class TestTOMLDecoding:
    """Test TOML decoding functionality."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_decode_simple(self):
        """Test decoding simple TOML."""
        toml_str = 'name = "Alice"\nage = 30'
        result = self.adapter.decode(toml_str, None)
        assert result == {"name": "Alice", "age": 30}

    def test_decode_section(self):
        """Test decoding section."""
        toml_str = '[database]\nhost = "localhost"\nport = 5432'
        result = self.adapter.decode(toml_str, None)
        assert result == {"database": {"host": "localhost", "port": 5432}}

    def test_decode_array(self):
        """Test decoding array."""
        toml_str = "items = [1, 2, 3]"
        result = self.adapter.decode(toml_str, None)
        assert result == {"items": [1, 2, 3]}

    def test_decode_boolean(self):
        """Test decoding boolean."""
        toml_str = "active = true\ninactive = false"
        result = self.adapter.decode(toml_str, None)
        assert result == {"active": True, "inactive": False}

    def test_decode_invalid_toml_strict(self):
        """Test decoding invalid TOML in strict mode raises DecodingError."""
        # Note: strict is True by default in DecodeOptions, but we pass None to check adapter default
        with pytest.raises(DecodingError):
            self.adapter.decode("invalid toml = ", None)

    def test_decode_invalid_toml_non_strict(self):
        """Test decoding invalid TOML in non-strict mode returns the raw string."""
        invalid_str = "invalid toml = "
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(invalid_str, options)
        assert result == invalid_str

    def test_decode_empty_string(self):
        """Test decoding an empty string returns an empty dictionary (valid TOML)."""
        result = self.adapter.decode("", None)
        assert result == {}


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed or cannot be imported")
class TestTOMLValidation:
    """Test TOML validation functionality."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_validate_valid_toml(self):
        """Test validation for a valid TOML string."""
        toml_str = 'name = "Test"\n[section]\nvalue = 1'
        assert self.adapter.validate(toml_str) is True

    def test_validate_empty_string(self):
        """Test validation for an empty string (is valid TOML)."""
        assert self.adapter.validate("") is True

    def test_validate_invalid_toml(self):
        """Test validation for an invalid TOML string."""
        toml_str = 'key = "missing quote'
        assert self.adapter.validate(toml_str) is False

    def test_validate_another_invalid_toml(self):
        """Test validation for an invalid TOML structure."""
        toml_str = "[invalid section\nkey = value"
        assert self.adapter.validate(toml_str) is False


@pytest.mark.skipif(not TOML_AVAILABLE, reason="TOML library not installed or cannot be imported")
class TestTOMLRoundtrip:
    """Test TOML roundtrip."""

    def setup_method(self):
        """Set up TOML format adapter."""
        self.adapter = TOMLFormat()

    def test_roundtrip_simple(self):
        """Test simple dictionary roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_roundtrip_section(self):
        """Test nested section roundtrip."""
        data = {"database": {"host": "localhost", "port": 5432, "enabled": True}}
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_roundtrip_complex(self):
        """Test complex data structure roundtrip."""
        data = {
            "title": "TOML Example",
            "owner": {
                "name": "Tom Preston-Werner",
                "dob": [1979, 5, 27],
            },
            "servers": {
                "alpha": {"ip": "10.0.0.1", "role": "frontend"},
                "beta": {"ip": "10.0.0.2", "role": "backend"},
            },
        }
        encoded = self.adapter.encode(data, EncodeOptions())
        decoded = self.adapter.decode(encoded, DecodeOptions())
        assert decoded == data


class TestTOMLInitError:
    """Test the initialization logic of the adapter."""

    def test_init_no_read_library(self, monkeypatch):
        """Test initialization failure when TOML_READ_AVAILABLE is False (Targets __init__ ImportError path)."""
        toml_format = get_toml_format_module()
        if not toml_format:
            return

        # Mock TOML_READ_AVAILABLE to False to hit the ImportError path
        monkeypatch.setattr(toml_format, "TOML_READ_AVAILABLE", False)

        with pytest.raises(ImportError) as excinfo:
            # We must use the original adapter class from the module
            toml_format.TomlFormatAdapter()

        expected_msg_part = "TOML support requires 'toml' package"
        assert expected_msg_part in str(excinfo.value)
