"""XML format adapter."""

import xml.etree.ElementTree as ET
from typing import Any
from xml.dom import minidom

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions

from .base import BaseFormatAdapter


class XmlFormatAdapter(BaseFormatAdapter):
    """Adapter for XML format.

    Note: XML conversion is lossy for complex structures due to
    XML's text-based nature and attribute limitations.
    """

    def __init__(self) -> None:
        """Initialize XML format adapter."""
        super().__init__("xml")

    def encode(self, data: Any, options: EncodeOptions | None = None) -> str:
        """Encode data to XML format.

        Args:
            data: Data to encode (dict, list, or primitive types)
            options: Encoding options

        Returns:
            XML formatted string

        Raises:
            EncodingError: If encoding fails
        """
        try:
            root = self._to_xml_element(data, "root")
            xml_str = ET.tostring(root, encoding="unicode")

            # Pretty print if not compact
            if options and not options.compact:
                dom = minidom.parseString(xml_str)
                xml_str = dom.toprettyxml(indent=" " * (options.indent or 2))
                # Remove XML declaration and empty lines
                lines = [line for line in xml_str.split("\n") if line.strip()]
                xml_str = "\n".join(lines[1:]) if len(lines) > 1 else xml_str

                xml_str = xml_str.strip()

            return xml_str
        except Exception as e:
            msg = f"Failed to encode to XML: {e}"
            raise EncodingError(msg) from e

    def _to_xml_element(self, data: Any, tag: str) -> ET.Element:
        """Convert Python data to XML Element.

        Args:
            data: Data to convert
            tag: XML tag name

        Returns:
            XML Element
        """
        element = ET.Element(tag)

        if data is None:
            element.set("nil", "true")
        elif isinstance(data, bool):
            element.text = "true" if data else "false"
            element.set("type", "bool")
        elif isinstance(data, int):
            element.text = str(data)
            element.set("type", "int")
        elif isinstance(data, float):
            element.text = str(data)
            element.set("type", "float")
        elif isinstance(data, str):
            element.text = data
        elif isinstance(data, dict):
            for key, value in data.items():
                child = self._to_xml_element(value, str(key))
                element.append(child)
        elif isinstance(data, (list, tuple)):
            for _i, item in enumerate(data):
                child = self._to_xml_element(item, "item")
                element.append(child)
        else:
            element.text = str(data)

        return element

    def decode(self, data_str: str, options: DecodeOptions | None = None) -> Any:
        """Decode XML format to Python data.

        Args:
            data_str: XML format string
            options: Decoding options

        Returns:
            Decoded Python data

        Raises:
            DecodingError: If decoding fails
        """
        try:
            root = ET.fromstring(data_str)
            return self._from_xml_element(root, options)
        except ET.ParseError as e:
            if options and not options.strict:
                return data_str
            msg = f"Failed to decode XML: {e}"
            raise DecodingError(msg) from e

    def _from_xml_element(self, element: ET.Element, options: DecodeOptions | None = None) -> Any:
        """Convert XML Element to Python data.

        Args:
            element: XML Element
            options: Decoding options

        Returns:
            Python data
        """
        # Check for nil
        if element.get("nil") == "true":
            return None

        # Check for type attribute
        type_attr = element.get("type")
        if type_attr == "bool":
            return element.text == "true"
        if type_attr == "int":
            return int(element.text or "0")
        if type_attr == "float":
            return float(element.text or "0.0")

        # If has children, it's a dict or list
        if len(element):
            # Check if all children have "item" tag (list)
            if all(child.tag == "item" for child in element):
                return [self._from_xml_element(child, options) for child in element]
            # Dictionary
            result = {}
            for child in element:
                result[child.tag] = self._from_xml_element(child, options)
            return result

        # Leaf node (no children) - return text with type inference or default
        text = element.text.strip() if element.text else ""

        if not text and not element.attrib:
            return {}

        if options and options.type_inference:
            return self._infer_type(text)
        return text

    def _infer_type(self, value: str) -> Any:
        """Infer type from string value.

        Args:
            value: String value

        Returns:
            Value with inferred type
        """
        if not value:
            return None
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value

    def validate(self, data_str: str) -> bool:
        """Validate XML format string.

        Args:
            data_str: String to validate

        Returns:
            True if valid XML
        """
        try:
            ET.fromstring(data_str)
            return True
        except ET.ParseError:
            return False
