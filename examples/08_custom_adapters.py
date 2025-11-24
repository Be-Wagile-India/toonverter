#!/usr/bin/env python3
"""
Example 8: Custom Format Adapters

Demonstrates:
- Creating custom format adapters
- Registering custom formats
- Using custom formats with TOON Converter
- Plugin development
"""

import toonverter as toon
from toonverter.core.interfaces import FormatAdapter
from toonverter.core.registry import registry
from typing import Any, Dict


class INIAdapter(FormatAdapter):
    """Custom adapter for INI format."""

    def encode(self, data: Any, options: dict[str, Any]) -> str:
        """Encode data to INI format."""
        if not isinstance(data, dict):
            raise ValueError("INI format requires dict at root")

        lines = []
        for section, values in data.items():
            lines.append(f"[{section}]")
            if isinstance(values, dict):
                for key, value in values.items():
                    lines.append(f"{key} = {value}")
            lines.append("")
        return "\n".join(lines)

    def decode(self, data_str: str, options: dict[str, Any]) -> Any:
        """Decode INI format to data."""
        result = {}
        current_section = None

        for line in data_str.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1]
                result[current_section] = {}
            elif "=" in line and current_section:
                key, value = line.split("=", 1)
                result[current_section][key.strip()] = value.strip()

        return result


class MarkdownTableAdapter(FormatAdapter):
    """Custom adapter for Markdown tables."""

    def encode(self, data: Any, options: dict[str, Any]) -> str:
        """Encode data to Markdown table."""
        if not isinstance(data, dict) or "rows" not in data:
            raise ValueError("Markdown table requires {'rows': [...]}")

        rows = data["rows"]
        if not rows:
            return ""

        # Get headers from first row
        headers = list(rows[0].keys())

        # Create header row
        lines = []
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Create data rows
        for row in rows:
            values = [str(row.get(h, "")) for h in headers]
            lines.append("| " + " | ".join(values) + " |")

        return "\n".join(lines)

    def decode(self, data_str: str, options: dict[str, Any]) -> Any:
        """Decode Markdown table to data."""
        lines = [l.strip() for l in data_str.strip().split("\n") if l.strip()]

        if len(lines) < 3:
            return {"rows": []}

        # Parse headers
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]

        # Parse data rows (skip header and separator)
        rows = []
        for line in lines[2:]:
            values = [v.strip() for v in line.split("|")[1:-1]]
            row = dict(zip(headers, values))
            rows.append(row)

        return {"rows": rows}


def example_register_adapter():
    """Register a custom adapter."""
    print("\n--- Registering Custom Adapter ---")

    # Register INI adapter
    registry.register("ini", INIAdapter())
    print("\nRegistered 'ini' format adapter")

    # Verify registration
    print(f"Available formats: {toon.list_formats()}")


def example_use_custom_format():
    """Use custom format."""
    print("\n--- Using Custom Format ---")

    data = {
        "database": {"host": "localhost", "port": "5432", "name": "mydb"},
        "cache": {"enabled": "true", "ttl": "3600"},
    }

    print("\nOriginal data:")
    print(data)

    # Encode to INI
    ini_str = toon.encode(data, format="ini")
    print("\nINI format:")
    print(ini_str)

    # Decode from INI
    decoded = toon.decode(ini_str, format="ini")
    print("\nDecoded:")
    print(decoded)


def example_markdown_table():
    """Use Markdown table adapter."""
    print("\n--- Markdown Table Format ---")

    # Register adapter
    registry.register("mdtable", MarkdownTableAdapter())

    data = {
        "rows": [
            {"Name": "Alice", "Age": "30", "City": "NYC"},
            {"Name": "Bob", "Age": "25", "City": "LA"},
            {"Name": "Charlie", "Age": "35", "City": "SF"},
        ]
    }

    print("\nOriginal data:")
    print(data)

    # Encode to Markdown table
    md_str = toon.encode(data, format="mdtable")
    print("\nMarkdown table:")
    print(md_str)

    # Decode
    decoded = toon.decode(md_str, format="mdtable")
    print("\nDecoded:")
    print(decoded)


def example_convert_between_formats():
    """Convert between custom formats."""
    print("\n--- Converting Between Formats ---")

    import tempfile
    import os

    data = {"server": {"host": "example.com", "port": "8080"}}

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save as INI
        ini_file = os.path.join(tmpdir, "config.ini")
        toon.save(data, ini_file, format="ini")
        print(f"\nSaved as INI: {ini_file}")

        # Convert INI -> TOON
        toon_file = os.path.join(tmpdir, "config.toon")
        toon.convert(source=ini_file, target=toon_file, from_format="ini", to_format="toon")
        print(f"Converted to TOON: {toon_file}")

        # Show both
        with open(ini_file) as f:
            print("\nINI content:")
            print(f.read())

        with open(toon_file) as f:
            print("\nTOON content:")
            print(f.read())


def main():
    print("=" * 60)
    print("Example 8: Custom Format Adapters")
    print("=" * 60)

    example_register_adapter()
    example_use_custom_format()
    example_markdown_table()
    example_convert_between_formats()


if __name__ == "__main__":
    main()
