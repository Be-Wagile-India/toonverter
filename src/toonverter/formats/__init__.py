"""Format adapters module for TOON Converter.

This module contains adapters for different data formats following
the Strategy pattern.
"""

from .base import BaseFormatAdapter
from .csv_format import CsvFormatAdapter
from .json_format import JsonFormatAdapter
from .toml_format import TomlFormatAdapter
from .toon_format import ToonFormatAdapter
from .xml_format import XmlFormatAdapter
from .yaml_format import YamlFormatAdapter


__all__ = [
    "BaseFormatAdapter",
    "CsvFormatAdapter",
    "JsonFormatAdapter",
    "TomlFormatAdapter",
    "ToonFormatAdapter",
    "XmlFormatAdapter",
    "YamlFormatAdapter",
]


def register_default_formats() -> None:
    """Register all default format adapters with the global registry.

    This function is called automatically when importing toon_converter.
    """
    from toonverter.core.registry import registry

    # Always available formats
    registry.register("json", JsonFormatAdapter())
    registry.register("toon", ToonFormatAdapter())
    registry.register("csv", CsvFormatAdapter())
    registry.register("xml", XmlFormatAdapter())

    # Optional formats (with graceful degradation)
    try:
        registry.register("yaml", YamlFormatAdapter())
    except ImportError:
        pass  # YAML support not available

    try:
        registry.register("toml", TomlFormatAdapter())
    except ImportError:
        pass  # TOML support not available
