"""Comprehensive tests for XML format adapter."""

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.xml_format import XmlFormatAdapter as XMLFormat


# Helper function to reliably cause an exception on string conversion for testing EncodingError
class Unstringifiable:
    """An object designed to fail when str() is called on it."""

    def __str__(self):
        # Fix for EM101: Exception message assigned to a variable first
        error_message = "Cannot convert to string"
        raise ValueError(error_message)


# Helper function to clean up minidom-generated XML for robust comparison
def cleanup_xml(xml_str: str) -> str:
    """Removes minidom's XML declaration, leading/trailing whitespace, and empty lines."""
    if not xml_str:
        return ""

    lines = [line.strip() for line in xml_str.splitlines() if line.strip()]
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    return "\n".join(lines).strip()


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
        assert '<age type="int">30</age>' in result

    def test_encode_nested_dict(self):
        """Test encoding nested dictionary."""
        data = {"user": {"name": "Alice", "details": {"city": "NYC"}}}
        result = self.adapter.encode(data, None)
        assert "<user>" in result
        assert "<name>Alice</name>" in result
        assert "<details>" in result
        assert "<city>NYC</city>" in result

    def test_encode_list_of_primitives(self):
        """Test encoding list of primitives (should use <item> tags)."""
        data = {"items": [1, True, "three"]}
        result = self.adapter.encode(data, None)
        assert "<items>" in result
        # Check for list structure and types
        assert '<item type="int">1</item>' in result
        assert '<item type="bool">true</item>' in result
        assert "<item>three</item>" in result

    def test_encode_primitives_and_types(self):
        """Test encoding all primitive types and ensuring correct attributes."""
        data = {
            "is_active": True,
            "count": 42,
            "pi": 3.14,
            "status": "ok",
            "missing": None,
        }
        result = self.adapter.encode(data, None)
        assert '<is_active type="bool">true</is_active>' in result
        assert '<count type="int">42</count>' in result
        assert '<pi type="float">3.14</pi>' in result
        assert "<status>ok</status>" in result
        assert '<missing nil="true" />' in result or '<missing nil="true"/>' in result

    def test_encode_compact_default(self):
        """Test encoding in compact mode (default) ensures no newlines/indentation."""
        data = {"a": 1, "b": 2}
        options = EncodeOptions(compact=True)
        result = self.adapter.encode(data, options)
        assert "\n" not in result
        assert result == '<root><a type="int">1</a><b type="int">2</b></root>'

    def test_encode_non_compact_default_indent(self):
        """Test encoding with default indentation (2 spaces) when compact=False. (FIXED)"""
        data = {"a": 1, "b": 2}
        options = EncodeOptions(compact=False)
        result = self.adapter.encode(data, options)
        assert "\n" in result

        # Check for the presence of the indented line (robust against minidom's specific whitespace characters)
        lines = result.strip().splitlines()
        # The second line should be the first indented child
        assert lines[1].strip().startswith('<a type="int">1</a>')
        # Check that the result string contains the standard indentation characters
        assert '  <a type="int">1</a>' in result

    def test_encode_with_custom_indent(self):
        """Test encoding with custom indentation (4 spaces)."""
        data = {"a": 1, "b": 2}
        options = EncodeOptions(compact=False, indent=4)
        result = self.adapter.encode(data, options)
        assert "\n" in result
        assert '    <a type="int">1</a>' in result

    def test_encode_unencodable_data(self):
        """Test encoding failure raises EncodingError using an unstringifiable object. (FIXED)"""
        # Using a custom class that fails on str() to reliably trigger an internal exception
        data = {"key": Unstringifiable()}
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "Failed to encode to XML" in str(excinfo.value)

    def test_encode_empty_dict(self):
        """Test encoding empty dictionary. (FIXED)"""
        data = {}
        result = self.adapter.encode(data, None)
        # Check for the three common formats of an empty self-closing root tag
        assert result in {"<root/>", "<root></root>", "<root />"}


class TestXMLDecoding:
    """Test XML decoding functionality."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_decode_simple_xml_no_inference(self):
        """Test decoding simple XML without type inference (all strings)."""
        xml_str = "<root><name>Alice</name><age>30</age></root>"
        options = DecodeOptions(type_inference=False)
        result = self.adapter.decode(xml_str, options)
        assert result == {"name": "Alice", "age": "30"}

    def test_decode_nested_xml(self):
        """Test decoding nested XML."""
        xml_str = "<root><user><name>Alice</name></user></root>"
        result = self.adapter.decode(xml_str, None)
        assert result == {"user": {"name": "Alice"}}

    def test_decode_xml_with_list(self):
        """Test decoding XML where child tags are all 'item' (list)."""
        xml_str = "<root><items><item>A</item><item>B</item></items></root>"
        result = self.adapter.decode(xml_str, None)
        assert result == {"items": ["A", "B"]}

    def test_decode_xml_with_mixed_children(self):
        """Test decoding XML where child tags are mixed (should be dict)."""
        xml_str = "<root><items><item>A</item><other>B</other></items></root>"
        result = self.adapter.decode(xml_str, None)
        assert result == {"items": {"item": "A", "other": "B"}}

    def test_decode_xml_with_attributes_and_no_text(self):
        """Test decoding XML with type attributes but no text (should default to 0/False)."""
        xml_str = '<root><count type="int"/><active type="bool"/></root>'
        options = DecodeOptions(type_inference=True)
        result = self.adapter.decode(xml_str, options)
        assert result == {"count": 0, "active": False}  # Defaults to 0/False if text is empty

    def test_decode_nil_value(self):
        """Test decoding XML with nil attribute (should return None)."""
        xml_str = '<root><missing nil="true"/></root>'
        result = self.adapter.decode(xml_str, None)
        assert result == {"missing": None}

    def test_decode_with_explicit_type_attributes(self):
        """Test decoding primitives using the explicit type attribute."""
        xml_str = (
            "<root>"
            '<bool type="bool">true</bool>'
            '<int type="int">42</int>'
            '<float type="float">3.14</float>'
            "</root>"
        )
        # Type attribute dictates conversion regardless of inference option
        result = self.adapter.decode(xml_str, None)
        assert result == {"bool": True, "int": 42, "float": 3.14}

    def test_decode_invalid_xml_strict(self):
        """Test decoding invalid XML in strict mode raises DecodingError."""
        xml_str = "<invalid>no closing tag"
        options = DecodeOptions(strict=True)
        with pytest.raises(DecodingError) as excinfo:
            self.adapter.decode(xml_str, options)
        assert "Failed to decode XML" in str(excinfo.value)

    def test_decode_invalid_xml_non_strict(self):
        """Test decoding invalid XML in non-strict mode returns the raw string."""
        xml_str = "<invalid>no closing tag"
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(xml_str, options)
        assert result == xml_str

    def test_decode_empty_xml(self):
        """Test decoding empty root XML returns an empty dictionary. (FIXED)"""
        xml_str = "<root></root>"
        result = self.adapter.decode(xml_str, None)
        # The fix in xml_format.py ensures this returns {} for an empty structural tag
        assert result == {}


class TestXMLTypeInference:
    """Test the internal _infer_type logic."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_infer_type_empty_string(self):
        """Test inference for empty string."""
        assert self.adapter._infer_type("") is None

    def test_infer_type_none(self):
        """Test inference for non-string empty value (e.g., in a list)."""
        assert self.adapter._infer_type(None) is None

    def test_infer_type_boolean(self):
        """Test inference for boolean strings."""
        assert self.adapter._infer_type("true") is True
        assert self.adapter._infer_type("FALSE") is False
        assert self.adapter._infer_type("True") is True

    def test_infer_type_integer(self):
        """Test inference for integer strings."""
        assert self.adapter._infer_type("123") == 123
        assert self.adapter._infer_type("-45") == -45
        assert self.adapter._infer_type("0") == 0

    def test_infer_type_float(self):
        """Test inference for float strings."""
        assert self.adapter._infer_type("3.14") == 3.14
        assert self.adapter._infer_type("-10.5") == -10.5
        assert self.adapter._infer_type("1e-5") == 0.00001

    def test_infer_type_string(self):
        """Test inference for general string (fails float conversion)."""
        assert self.adapter._infer_type("hello world") == "hello world"
        assert self.adapter._infer_type("123a") == "123a"
        assert self.adapter._infer_type("3.1.4") == "3.1.4"


class TestXMLRoundtrip:
    """Test XML roundtrip."""

    def setup_method(self):
        """Set up XML format adapter."""
        self.adapter = XMLFormat()

    def test_roundtrip_complex_with_types(self):
        """Test complex roundtrip with all types preserved via attributes. (FIXED)"""
        data = {
            "title": "Config",
            "metadata": {
                "version": 1.0,
                "enabled": True,
                "count": 100,
                "notes": None,
            },
            "servers": [
                {"id": 1, "host": "srv1"},
                {"id": 2, "host": "srv2"},
            ],
        }
        encoded = self.adapter.encode(data, EncodeOptions(compact=True))

        # Check raw decoded data (type_inference=False).
        # Type attributes *must* still trigger conversion (float, bool, int)
        decoded = self.adapter.decode(encoded, DecodeOptions(type_inference=False))

        # Check that the decoded structure is correct and types were preserved by XML attributes
        assert decoded["title"] == "Config"
        # These fields had type attributes in the XML and must be the correct Python type
        assert decoded["metadata"]["version"] == 1.0
        assert decoded["metadata"]["enabled"] is True
        assert decoded["metadata"]["count"] == 100
        assert decoded["metadata"]["notes"] is None

        # Now check with default inference (should yield the same result for these fields)
        decoded_inferred = self.adapter.decode(encoded, None)
        assert decoded_inferred["metadata"]["version"] == 1.0
        assert decoded_inferred["metadata"]["enabled"] is True
        assert decoded_inferred["metadata"]["count"] == 100
        assert decoded_inferred["metadata"]["notes"] is None

        # Check list structure and internal type inference
        assert decoded_inferred["servers"] == [
            {"id": 1, "host": "srv1"},
            {"id": 2, "host": "srv2"},
        ]
