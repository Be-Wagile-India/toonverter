"""Comprehensive tests for XML format adapter."""

from unittest.mock import patch

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.xml_format import XmlFormatAdapter as XMLFormat


class TestXMLEncoding:
    """Test XML encoding functionality."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_encode_simple_dict(self):
        """Test encoding simple dictionary."""
        data = {"name": "Alice", "age": 30}
        result = self.adapter.encode(data)
        assert "<root>" in result
        assert "<name>Alice</name>" in result
        # integer encoding
        assert "<age" in result
        assert 'type="int"' in result
        assert ">30</age>" in result

    def test_encode_types(self):
        """Test encoding various data types."""
        data = {
            "is_valid": True,
            "is_false": False,
            "score": 95.5,
            "nothing": None,
            "simple_str": "hello",
        }
        result = self.adapter.encode(data)

        # Bool
        assert '<is_valid type="bool">true</is_valid>' in result
        assert '<is_false type="bool">false</is_false>' in result

        # Float
        assert '<score type="float">95.5</score>' in result

        # None
        assert (
            '<nothing nil="true" />' in result
            or '<nothing nil="true"/>' in result
            or '<nothing nil="true" />' in result.replace(" />", "/>")
        )

        # String
        assert "<simple_str>hello</simple_str>" in result

    def test_encode_unknown_type(self):
        """Test encoding a type that falls through to str()."""

        class Unknown:
            def __str__(self):
                return "unknown_val"

        data = {"custom": Unknown()}
        result = self.adapter.encode(data)
        assert "<custom>unknown_val</custom>" in result

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {"user": {"name": "Alice", "age": 30}}
        result = self.adapter.encode(data)
        assert "<user>" in result
        assert "<name>Alice</name>" in result

    def test_encode_list(self):
        """Test encoding list."""
        data = {"items": [1, 2, 3]}
        result = self.adapter.encode(data)
        assert "<items>" in result
        assert result.count('<item type="int">') == 3
        assert '<item type="int">1</item>' in result

    def test_encode_pretty_print(self):
        """Test encoding with pretty print (compact=False)."""
        data = {"root": {"child": "value"}}
        options = EncodeOptions(compact=False, indent=4)
        result = self.adapter.encode(data, options)
        # Verify indentation
        assert "\n" in result
        # Standard minidom pretty print might have specific indentation behavior
        # We look for the child element indented
        assert "    <child>value</child>" in result

    def test_encode_error(self):
        """Test encoding error handling."""
        # Mocking _to_xml_element to raise an exception
        with patch.object(self.adapter, "_to_xml_element", side_effect=ValueError("Mock Error")):
            with pytest.raises(EncodingError) as excinfo:
                self.adapter.encode({"a": 1})
            assert "Failed to encode to XML" in str(excinfo.value)


class TestXMLDecoding:
    """Test XML decoding functionality."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_decode_simple_xml(self):
        """Test decoding simple XML."""
        xml_str = '<root><name>Alice</name><age type="int">30</age></root>'
        result = self.adapter.decode(xml_str)
        assert result["name"] == "Alice"
        assert result["age"] == 30

    def test_decode_types_explicit(self):
        """Test decoding with explicit type attributes."""
        xml_str = """
        <root>
            <flag type="bool">true</flag>
            <flag_false type="bool">false</flag_false>
            <val type="int">42</val>
            <pi type="float">3.14</pi>
            <empty nil="true" />
        </root>
        """
        result = self.adapter.decode(xml_str)
        assert result["flag"] is True
        assert result["flag_false"] is False
        assert result["val"] == 42
        assert result["pi"] == 3.14
        assert result["empty"] is None

    def test_decode_types_defaults(self):
        """Test decoding types with empty text defaulting."""
        xml_str = """
        <root>
            <val type="int"></val>
            <pi type="float"></pi>
        </root>
        """
        result = self.adapter.decode(xml_str)
        assert result["val"] == 0
        assert result["pi"] == 0.0

    def test_decode_list(self):
        """Test decoding XML list (repeated item tags)."""
        xml_str = "<root><item>1</item><item>2</item></root>"
        result = self.adapter.decode(xml_str, DecodeOptions(type_inference=True))
        assert isinstance(result, list)
        assert result == [1, 2]

    def test_decode_nested_dict_mixed(self):
        """Test decoding mixed children (dict logic)."""
        xml_str = "<root><name>Alice</name><role>Admin</role></root>"
        result = self.adapter.decode(xml_str)
        assert result == {"name": "Alice", "role": "Admin"}

    def test_decode_type_inference(self):
        """Test decoding with type inference."""
        options = DecodeOptions(type_inference=True)

        assert self.adapter.decode("<root>123</root>", options) == 123
        assert self.adapter.decode("<root>-123</root>", options) == -123
        assert self.adapter.decode("<root>12.34</root>", options) == 12.34
        assert self.adapter.decode("<root>true</root>", options) is True
        assert self.adapter.decode("<root>FALSE</root>", options) is False
        assert self.adapter.decode("<root>hello</root>", options) == "hello"
        assert self.adapter.decode("<root>12.34.56</root>", options) == "12.34.56"
        assert self.adapter.decode("<root></root>", options) is None  # Empty text

    def test_decode_invalid_xml_strict(self):
        """Test decoding invalid XML with strict mode (default)."""
        with pytest.raises(DecodingError):
            self.adapter.decode("<root>unclosed", DecodeOptions(strict=True))

    def test_decode_invalid_xml_non_strict(self):
        """Test decoding invalid XML with non-strict mode."""
        raw_data = "<root>unclosed"
        result = self.adapter.decode(raw_data, DecodeOptions(strict=False))
        assert result == raw_data


class TestXMLValidation:
    """Test XML validation."""

    def setup_method(self):
        self.adapter = XMLFormat()

    def test_validate_valid(self):
        assert self.adapter.validate("<root></root>") is True

    def test_validate_invalid(self):
        assert self.adapter.validate("<root>unclosed") is False
