"""Basic usage examples for TOON Converter."""

import toonverter as toon

# Example 1: Simple encoding and decoding
print("=" * 60)
print("Example 1: Basic Encode/Decode")
print("=" * 60)

data = {"name": "Alice", "age": 30, "city": "NYC", "active": True}

# Encode to TOON format
toon_str = toon.encode(data)
print(f"Original data: {data}")
print(f"TOON encoded: {toon_str}")

# Decode back
decoded = toon.decode(toon_str)
print(f"Decoded data: {decoded}")
print()

# Example 2: Token analysis
print("=" * 60)
print("Example 2: Token Analysis")
print("=" * 60)

report = toon.analyze(data, compare_formats=["json", "toon"])
print(f"Best format: {report.best_format}")
print(f"Maximum savings: {report.max_savings_percentage:.1f}%")
print("\nToken counts:")
for analysis in sorted(report.analyses, key=lambda a: a.token_count):
    print(f"  {analysis.format}: {analysis.token_count} tokens")
print()

# Example 3: Tabular data (most efficient)
print("=" * 60)
print("Example 3: Tabular Data Encoding")
print("=" * 60)

tabular_data = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"},
    {"name": "Charlie", "age": 35, "city": "SF"},
]

toon_tabular = toon.encode(tabular_data)
print("Tabular TOON format:")
print(toon_tabular)
print()

# Example 4: Using OOP API
print("=" * 60)
print("Example 4: OOP API")
print("=" * 60)

encoder = toon.Encoder(format="toon", compact=True)
encoded = encoder.encode({"status": "success", "count": 42})
print(f"Encoded with OOP API: {encoded}")

decoder = toon.Decoder(format="toon")
decoded = decoder.decode(encoded)
print(f"Decoded: {decoded}")
print()

# Example 5: Format conversion
print("=" * 60)
print("Example 5: List Available Formats")
print("=" * 60)

formats = toon.list_formats()
print(f"Supported formats: {', '.join(formats)}")

for fmt in formats:
    print(f"  {fmt}: {'✓ supported' if toon.is_supported(fmt) else '✗ not supported'}")
