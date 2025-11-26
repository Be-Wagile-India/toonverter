#!/usr/bin/env python3
"""
Example 1: Simple Encoding and Decoding

This example demonstrates the most basic TOON operations:
- Encoding Python dict to TOON
- Decoding TOON back to Python dict
- Token counting and savings
"""

import toonverter as toon


def main():
    print("=" * 60)
    print("Example 1: Simple Encoding and Decoding")
    print("=" * 60)

    # Create a simple Python dictionary
    data = {"name": "Alice", "age": 30, "city": "NYC", "active": True}

    print("\n1. Original Python dict:")
    print(data)

    # Encode to TOON
    toon_str = toon.encode(data)
    print("\n2. Encoded to TOON:")
    print(toon_str)

    # Decode back to Python
    decoded = toon.decode(toon_str)
    print("\n3. Decoded back to Python:")
    print(decoded)

    # Verify roundtrip
    print("\n4. Roundtrip verification:")
    print(f"Original == Decoded: {data == decoded}")

    # Analyze token savings
    print("\n5. Token Analysis:")
    report = toon.analyze(data, compare_formats=["json", "toon"])
    print(f"Best format: {report.best_format}")
    print(f"Token savings: {report.max_savings_percentage:.1f}%")
    print(f"JSON tokens: {report.format_results['json'].token_count}")
    print(f"TOON tokens: {report.format_results['toon'].token_count}")


if __name__ == "__main__":
    main()
