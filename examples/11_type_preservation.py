#!/usr/bin/env python3
"""
Example 11: Type Preservation

Demonstrates:
- Type inference and preservation
- Type annotations
- Custom type handling
- Strict validation
"""

import toonverter as toon
from datetime import datetime, date
from decimal import Decimal


def example_basic_types():
    """Basic type preservation."""
    print("\n--- Basic Types ---")

    data = {
        "string": "Hello",
        "integer": 42,
        "float": 3.14,
        "boolean_true": True,
        "boolean_false": False,
        "null": None
    }

    print("\nOriginal types:")
    for key, value in data.items():
        print(f"  {key}: {type(value).__name__} = {value}")

    # Encode and decode
    toon_str = toon.encode(data)
    decoded = toon.decode(toon_str)

    print("\nDecoded types:")
    for key, value in decoded.items():
        print(f"  {key}: {type(value).__name__} = {value}")

    print(f"\nTypes preserved: {all(type(data[k]) == type(decoded[k]) for k in data)}")


def example_datetime_types():
    """DateTime type handling."""
    print("\n--- DateTime Types ---")

    data = {
        "datetime": datetime(2025, 1, 15, 10, 30, 0),
        "date": date(2025, 1, 15),
        "timestamp": "2025-01-15T10:30:00"
    }

    print("\nOriginal:")
    for key, value in data.items():
        print(f"  {key}: {type(value).__name__} = {value}")

    # Encode
    toon_str = toon.encode(data)
    print(f"\nTOON:\n{toon_str}")

    # Decode
    decoded = toon.decode(toon_str)
    print("\nDecoded:")
    for key, value in decoded.items():
        print(f"  {key}: {type(value).__name__} = {value}")


def example_numeric_precision():
    """Numeric precision handling."""
    print("\n--- Numeric Precision ---")

    data = {
        "integer": 123456789,
        "float": 3.141592653589793,
        "scientific": 1.23e-4,
        "large": 1000000000000
    }

    print("\nOriginal values:")
    for key, value in data.items():
        print(f"  {key}: {value}")

    # Encode and decode
    toon_str = toon.encode(data)
    decoded = toon.decode(toon_str)

    print("\nDecoded values:")
    for key, value in decoded.items():
        print(f"  {key}: {value}")

    print("\nPrecision maintained:", all(abs(data[k] - decoded[k]) < 1e-10 for k in data))


def example_type_annotations():
    """Using type annotations."""
    print("\n--- Type Annotations ---")

    from toonverter import Encoder

    data = {
        "count": 100,
        "price": 19.99,
        "active": True
    }

    # Encode with type annotations
    encoder = Encoder(use_type_annotations=True)
    toon_str = encoder.encode(data)

    print("\nWith type annotations:")
    print(toon_str)

    # Decode
    decoded = toon.decode(toon_str)
    print("\nDecoded with correct types:")
    for key, value in decoded.items():
        print(f"  {key}: {type(value).__name__} = {value}")


def main():
    print("=" * 60)
    print("Example 11: Type Preservation")
    print("=" * 60)

    example_basic_types()
    example_datetime_types()
    example_numeric_precision()
    example_type_annotations()


if __name__ == "__main__":
    main()
