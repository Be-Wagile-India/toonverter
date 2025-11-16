"""Comprehensive tests for YAML format adapter."""

import pytest


try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from toonverter.core.exceptions import DecodingError
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
            self.adapter.decode("invalid:\n  - item1\n  item2: broken indentation", None)


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
