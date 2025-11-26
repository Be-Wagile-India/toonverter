"Comprehensive tests for YAML format adapter."

from unittest.mock import patch

import pytest


try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.yaml_format import YamlFormatAdapter as YAMLFormat


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestYAMLEncoding:
    """Test YAML encoding functionality."""

    def setup_method(self):
        """Set up YAML format adapter."""
        self.adapter = YAMLFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, {})
        assert "name: Alice" in result
        assert "age: 30" in result

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = self.adapter.encode(data, {})
        decoded = yaml.safe_load(result)
        assert decoded == data

    def test_encode_list(self):
        """Test encoding list."""
        data = {"items": [1, 2, 3]}
        result = self.adapter.encode(data, {})
        decoded = yaml.safe_load(result)
        assert decoded == data

    def test_encode_mixed_types(self):
        """Test encoding mixed types."""
        data = {"string": "hello", "number": 42, "float": 3.14, "bool": True, "null": None}
        result = self.adapter.encode(data, {})
        decoded = yaml.safe_load(result)
        assert decoded == data

    def test_encode_multiline_string(self):
        """Test encoding multiline string."""
        data = {"text": "Line 1\nLine 2\nLine 3"}
        result = self.adapter.encode(data, {})
        decoded = yaml.safe_load(result)
        assert decoded == data

    def test_encode_unicode(self):
        """Test encoding unicode."""
        data = {"text": "Hello 世界"}
        result = self.adapter.encode(data, {})
        decoded = yaml.safe_load(result)
        assert decoded == data

    def test_encode_with_options(self):
        """Test encoding with options."""
        data = {"name": "Alice", "age": 30}

        # Test compact
        options = EncodeOptions(compact=True)
        result = self.adapter.encode(data, options)
        assert "{" in result and "}" in result

        # Test explicit not compact
        options = EncodeOptions(compact=False)
        result = self.adapter.encode(data, options)
        assert "name: Alice" in result

        # Test sort keys
        data_unordered = {"z": 1, "a": 2}
        options = EncodeOptions(sort_keys=True)
        result = self.adapter.encode(data_unordered, options)
        assert result.index("a") < result.index("z")

    def test_encode_ensure_ascii(self):
        """Test ensure_ascii option."""
        data = {"text": "Hello 世界"}

        # ensure_ascii=True -> allow_unicode=False
        options = EncodeOptions(ensure_ascii=True)
        result = self.adapter.encode(data, options)
        assert "世界" not in result

        # ensure_ascii=False -> allow_unicode=True
        options = EncodeOptions(ensure_ascii=False)
        result = self.adapter.encode(data, options)
        assert "世界" in result


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestYAMLDecoding:
    """Test YAML decoding functionality."""

    def setup_method(self):
        """Set up YAML format adapter."""
        self.adapter = YAMLFormat()

    def test_decode_simple_object(self):
        """Test decoding simple object."""
        yaml_str = "name: Alice\nage: 30"
        result = self.adapter.decode(yaml_str, {})
        assert result == {"name": "Alice", "age": 30}

    def test_decode_nested_object(self):
        """Test decoding nested object."""
        yaml_str = "user:\n  name: Alice\n  age: 30"
        result = self.adapter.decode(yaml_str, {})
        assert result == {"user": {"name": "Alice", "age": 30}}

    def test_decode_list(self):
        """Test decoding list."""
        yaml_str = "items:\n  - 1\n  - 2\n  - 3"
        result = self.adapter.decode(yaml_str, {})
        assert result == {"items": [1, 2, 3]}

    def test_decode_boolean(self):
        """Test decoding boolean."""
        yaml_str = "active: true\ninactive: false"
        result = self.adapter.decode(yaml_str, {})
        assert result == {"active": True, "inactive": False}

    def test_decode_null(self):
        """Test decoding null."""
        yaml_str = "value: null"
        result = self.adapter.decode(yaml_str, {})
        assert result == {"value": None}

    def test_decode_invalid_yaml(self):
        """Test decoding invalid YAML."""
        with pytest.raises(DecodingError):
            self.adapter.decode("invalid: [\n  item1\n  item2: broken indentation", None)

    def test_decode_strict_false(self):
        """Test decoding with strict=False."""
        invalid_yaml = "invalid: [\n  broken"
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(invalid_yaml, options)
        assert result == invalid_yaml


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestYAMLRoundtrip:
    """Test YAML roundtrip."""

    def setup_method(self):
        """Set up YAML format adapter."""
        self.adapter = YAMLFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data

    def test_roundtrip_complex(self):
        """Test complex roundtrip."""
        data = {
            "users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            "metadata": {"count": 2},
        }
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        assert decoded == data


@pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
class TestYAMLValidation:
    """Test YAML validation functionality."""

    def setup_method(self):
        """Set up YAML format adapter."""
        self.adapter = YAMLFormat()

    def test_validate_success(self):
        """Test validating valid YAML."""
        assert self.adapter.validate("name: Alice") is True

    def test_validate_failure(self):
        """Test validating invalid YAML."""
        assert self.adapter.validate("invalid: [") is False


class TestYAMLErrors:
    """Test YAML error handling and edge cases."""

    @patch("yaml.dump")
    def test_encode_error(self, mock_dump):
        """Test encoding error handling."""
        mock_dump.side_effect = yaml.YAMLError("Mock error")
        adapter = YAMLFormat()
        with pytest.raises(EncodingError) as exc:
            adapter.encode({"a": 1})
        assert "Failed to encode to YAML" in str(exc.value)

    @patch("yaml.safe_load")
    def test_decode_error_strict(self, mock_load):
        """Test decoding error with strict mode (default)."""
        mock_load.side_effect = yaml.YAMLError("Mock error")
        adapter = YAMLFormat()
        with pytest.raises(DecodingError) as exc:
            adapter.decode("bad yaml")
        assert "Failed to decode YAML" in str(exc.value)

    def test_missing_dependency(self):
        """Test behavior when yaml is missing."""
        with patch("toonverter.formats.yaml_format.YAML_AVAILABLE", False):
            with pytest.raises(ImportError) as exc:
                YAMLFormat()
            assert "PyYAML is required" in str(exc.value)
