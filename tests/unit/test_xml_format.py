"""Comprehensive tests for XML format adapter."""

import pytest
from toonverter.formats.xml_format import XmlFormatAdapter as XMLFormat
from toonverter.core.exceptions import EncodingError, DecodingError


class TestXMLEncoding:
    """Test XML encoding functionality."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data, None)
        assert "<root>" in result
        assert "<name>Alice</name>" in result
        assert "<age" in result and ">30</age>" in result

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = self.adapter.encode(data, {})
        assert "<user>" in result
        assert "<name>Alice</name>" in result

    def test_encode_list(self):
        """Test encoding list."""
        data = {"items": [1, 2, 3]}
        result = self.adapter.encode(data, {})
        assert "<items>" in result

    def test_encode_with_attributes(self):
        """Test encoding with XML attributes."""
        data = {"user": {"name": "Alice", "id": 1}}
        result = self.adapter.encode(data, {})
        # Should create valid XML
        assert "<user>" in result or "<user " in result


class TestXMLDecoding:
    """Test XML decoding functionality."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_decode_simple_xml(self):
        """Test decoding simple XML."""
        xml_str = "<root><name>Alice</name><age>30</age></root>"
        result = self.adapter.decode(xml_str, {})
        assert "name" in result
        assert "age" in result

    def test_decode_nested_xml(self):
        """Test decoding nested XML."""
        xml_str = "<root><user><name>Alice</name></user></root>"
        result = self.adapter.decode(xml_str, {})
        assert "user" in result

    def test_decode_invalid_xml(self):
        """Test decoding invalid XML."""
        with pytest.raises(DecodingError):
            self.adapter.decode("<invalid>no closing tag", {})

    def test_decode_empty_xml(self):
        """Test decoding empty XML."""
        xml_str = "<root></root>"
        result = self.adapter.decode(xml_str, {})
        assert result is not None


class TestXMLRoundtrip:
    """Test XML roundtrip."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = {"name": "Alice", "age": 30}
        encoded = self.adapter.encode(data, {})
        decoded = self.adapter.decode(encoded, {})
        # XML roundtrip may change types
        assert "name" in decoded
        assert "age" in decoded
