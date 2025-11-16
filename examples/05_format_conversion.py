#!/usr/bin/env python3
"""
Example 5: Format Conversion

Demonstrates:
- Converting between different formats
- File-based conversion
- Batch conversion
- Format detection
"""

import toonverter as toon
import tempfile
import os


def example_direct_conversion():
    """Convert between formats directly."""
    print("\n--- Direct Format Conversion ---")

    data = {
        "users": [
            {"name": "Alice", "age": 30, "city": "NYC"},
            {"name": "Bob", "age": 25, "city": "LA"}
        ]
    }

    # Convert to different formats
    formats = ['json', 'yaml', 'toon']

    print("\nOriginal data:")
    print(data)

    for fmt in formats:
        encoded = toon.encode(data, format=fmt)
        print(f"\n{fmt.upper()} format:")
        print(encoded[:200] + ("..." if len(encoded) > 200 else ""))


def example_file_conversion():
    """Convert files between formats."""
    print("\n--- File-Based Conversion ---")

    data = {
        "config": {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "mydb"
            },
            "cache": {
                "enabled": True,
                "ttl": 3600
            }
        }
    }

    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save as JSON
        json_file = os.path.join(tmpdir, "config.json")
        toon.save(data, json_file, format='json')
        print(f"\nSaved JSON: {json_file}")

        # Convert JSON -> TOON
        toon_file = os.path.join(tmpdir, "config.toon")
        toon.convert(source=json_file, target=toon_file, from_format='json', to_format='toon')
        print(f"Converted to TOON: {toon_file}")

        # Load TOON file
        loaded_data = toon.load(toon_file, format='toon')
        print(f"\nLoaded from TOON:")
        print(loaded_data)

        # Verify roundtrip
        print(f"\nRoundtrip verification: {data == loaded_data}")

        # Show file sizes
        json_size = os.path.getsize(json_file)
        toon_size = os.path.getsize(toon_file)
        print(f"\nFile sizes:")
        print(f"  JSON: {json_size} bytes")
        print(f"  TOON: {toon_size} bytes")
        print(f"  Savings: {((json_size - toon_size) / json_size * 100):.1f}%")


def example_batch_conversion():
    """Batch convert multiple files."""
    print("\n--- Batch Conversion ---")

    datasets = {
        "users": {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        },
        "products": {
            "products": [
                {"id": 101, "name": "Widget", "price": 19.99},
                {"id": 102, "name": "Gadget", "price": 29.99}
            ]
        },
        "orders": {
            "orders": [
                {"id": 1001, "user_id": 1, "product_id": 101},
                {"id": 1002, "user_id": 2, "product_id": 102}
            ]
        }
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\nConverting {len(datasets)} files...")

        for name, data in datasets.items():
            # Save as JSON
            json_file = os.path.join(tmpdir, f"{name}.json")
            toon.save(data, json_file, format='json')

            # Convert to TOON
            toon_file = os.path.join(tmpdir, f"{name}.toon")
            toon.convert(source=json_file, target=toon_file, from_format='json', to_format='toon')

            json_size = os.path.getsize(json_file)
            toon_size = os.path.getsize(toon_file)
            savings = ((json_size - toon_size) / json_size * 100)

            print(f"  {name:10s}: {json_size:4d} bytes -> {toon_size:4d} bytes ({savings:5.1f}% savings)")


def example_format_detection():
    """Demonstrate format detection."""
    print("\n--- Format Detection ---")

    # TOON Converter can detect format from content
    data = {"test": "value", "count": 42}

    # Different format strings
    json_str = '{"test": "value", "count": 42}'
    toon_str = "test: value\ncount: 42"

    print("\nAutomatic format detection:")

    # Decode without specifying format (auto-detection)
    print(f"\nJSON string: {json_str}")
    decoded_json = toon.decode(json_str, format='json')
    print(f"Decoded: {decoded_json}")

    print(f"\nTOON string: {toon_str}")
    decoded_toon = toon.decode(toon_str, format='toon')
    print(f"Decoded: {decoded_toon}")


def example_streaming_large_files():
    """Handle large files efficiently."""
    print("\n--- Streaming Large Files ---")

    # Create a large dataset
    large_data = {
        "records": [
            {"id": i, "value": f"Record {i}", "category": f"Cat{i % 10}"}
            for i in range(10000)  # 10,000 records
        ]
    }

    print(f"\nDataset size: {len(large_data['records'])} records")

    with tempfile.TemporaryDirectory() as tmpdir:
        import time

        # Save as JSON
        json_file = os.path.join(tmpdir, "large.json")
        start = time.time()
        toon.save(large_data, json_file, format='json')
        json_time = time.time() - start

        # Convert to TOON
        toon_file = os.path.join(tmpdir, "large.toon")
        start = time.time()
        toon.convert(source=json_file, target=toon_file, from_format='json', to_format='toon')
        convert_time = time.time() - start

        # Compare
        json_size = os.path.getsize(json_file)
        toon_size = os.path.getsize(toon_file)

        print(f"\nPerformance:")
        print(f"  JSON save time: {json_time*1000:.2f}ms")
        print(f"  Convert time:   {convert_time*1000:.2f}ms")

        print(f"\nFile sizes:")
        print(f"  JSON: {json_size:,} bytes")
        print(f"  TOON: {toon_size:,} bytes")
        print(f"  Savings: {((json_size - toon_size) / json_size * 100):.1f}%")


def main():
    print("=" * 60)
    print("Example 5: Format Conversion")
    print("=" * 60)

    # Check available formats
    print("\nAvailable formats:", toon.list_formats())

    example_direct_conversion()
    example_file_conversion()
    example_batch_conversion()
    example_format_detection()
    example_streaming_large_files()


if __name__ == "__main__":
    main()
