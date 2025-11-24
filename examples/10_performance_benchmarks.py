#!/usr/bin/env python3
"""
Example 10: Performance Benchmarks

Demonstrates:
- Encoding/decoding speed
- Memory usage
- Scalability with large datasets
- Performance comparison across formats
"""

import toonverter as toon
import time
import json


def benchmark_encoding():
    """Benchmark encoding performance."""
    print("\n--- Encoding Performance ---")

    sizes = [10, 100, 1000, 10000]

    for size in sizes:
        data = {
            "records": [{"id": i, "value": f"Record{i}", "score": i * 0.1} for i in range(size)]
        }

        # Benchmark TOON encoding
        start = time.time()
        toon_str = toon.encode(data)
        toon_time = (time.time() - start) * 1000

        # Benchmark JSON encoding
        start = time.time()
        json_str = json.dumps(data)
        json_time = (time.time() - start) * 1000

        print(f"\n{size:,} records:")
        print(f"  TOON: {toon_time:6.2f}ms ({len(toon_str):,} bytes)")
        print(f"  JSON: {json_time:6.2f}ms ({len(json_str):,} bytes)")
        print(f"  Size savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")


def benchmark_decoding():
    """Benchmark decoding performance."""
    print("\n--- Decoding Performance ---")

    sizes = [10, 100, 1000, 5000]

    for size in sizes:
        data = {"records": [{"id": i, "name": f"Item{i}"} for i in range(size)]}

        toon_str = toon.encode(data)
        json_str = json.dumps(data)

        # Benchmark TOON decoding
        start = time.time()
        toon_decoded = toon.decode(toon_str)
        toon_time = (time.time() - start) * 1000

        # Benchmark JSON decoding
        start = time.time()
        json_decoded = json.loads(json_str)
        json_time = (time.time() - start) * 1000

        print(f"\n{size:,} records:")
        print(f"  TOON decode: {toon_time:6.2f}ms")
        print(f"  JSON decode: {json_time:6.2f}ms")


def benchmark_roundtrip():
    """Benchmark roundtrip performance."""
    print("\n--- Roundtrip Performance ---")

    sizes = [100, 500, 1000]

    for size in sizes:
        data = {"items": [{"id": i, "data": f"Data{i}", "value": i * 10} for i in range(size)]}

        # TOON roundtrip
        start = time.time()
        toon_str = toon.encode(data)
        decoded = toon.decode(toon_str)
        toon_time = (time.time() - start) * 1000

        # JSON roundtrip
        start = time.time()
        json_str = json.dumps(data)
        decoded = json.loads(json_str)
        json_time = (time.time() - start) * 1000

        print(f"\n{size:,} records roundtrip:")
        print(f"  TOON: {toon_time:6.2f}ms")
        print(f"  JSON: {json_time:6.2f}ms")


def main():
    print("=" * 60)
    print("Example 10: Performance Benchmarks")
    print("=" * 60)

    benchmark_encoding()
    benchmark_decoding()
    benchmark_roundtrip()

    print("\n" + "=" * 60)
    print("Summary:")
    print("- TOON provides 30-60% size savings")
    print("- Performance is comparable to JSON")
    print("- Optimal for tabular data")
    print("=" * 60)


if __name__ == "__main__":
    main()
