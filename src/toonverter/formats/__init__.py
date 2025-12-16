"""Format adapters module for TOON Converter.

This module contains adapters for different data formats following
the Strategy pattern.
"""

from .base import BaseFormatAdapter
from .csv_format import CsvFormatAdapter
from .json_format import JsonFormatAdapter
from .jsonl_format import JsonlFormatAdapter
from .toml_format import TomlFormatAdapter
from .toon_format import ToonFormatAdapter
from .xml_format import XmlFormatAdapter
from .yaml_format import YamlFormatAdapter


__all__ = [
    "BaseFormatAdapter",
    "CsvFormatAdapter",
    "JsonFormatAdapter",
    "JsonlFormatAdapter",
    "TomlFormatAdapter",
    "ToonFormatAdapter",
    "XmlFormatAdapter",
    "YamlFormatAdapter",
]


def register_default_formats() -> None:
    """Register all default format adapters with the global registry.

    This function is called automatically when importing toon_converter.
    Idempotent - safe to call multiple times.
    """
    from toonverter.core.registry import registry

    # Helper to register if not already registered
    def register_if_not_exists(name: str, adapter: BaseFormatAdapter) -> None:
        if not registry.is_supported(name):
            registry.register(name, adapter)

    # Always available formats
    register_if_not_exists("json", JsonFormatAdapter())

    # JSONL/NDJSON
    jsonl_adapter = JsonlFormatAdapter()
    register_if_not_exists("jsonl", jsonl_adapter)
    register_if_not_exists("ndjson", jsonl_adapter)

    register_if_not_exists("toon", ToonFormatAdapter())
    register_if_not_exists("csv", CsvFormatAdapter())
    register_if_not_exists("xml", XmlFormatAdapter())

    # Optional formats (with graceful degradation)
    try:
        register_if_not_exists("yaml", YamlFormatAdapter())
    except ImportError:
        pass  # YAML support not available

    try:
        register_if_not_exists("toml", TomlFormatAdapter())
    except ImportError:
        pass  # TOML support not available
