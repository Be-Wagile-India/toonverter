"""Example of Smart Dictionary Compression (SDC).

This example demonstrates how to use SDC to compress repetitive data structures
while maintaining a JSON-serializable format.
"""

import json
import toonverter as toon
from toonverter.optimization import SmartCompressor


def run_compression_example():
    """Run compression example."""
    print("--- Smart Dictionary Compression (SDC) Example ---\n")

    # 1. Create repetitive data
    # A list of objects with same keys and repeated values
    data = {
        "users": [
            {
                "id": 1,
                "name": "Alice",
                "role": "admin",
                "department": "engineering",
                "active": True,
                "preferences": {"theme": "dark", "notifications": True}
            },
            {
                "id": 2,
                "name": "Bob",
                "role": "user",
                "department": "sales",
                "active": True,
                "preferences": {"theme": "light", "notifications": True}
            },
            {
                "id": 3,
                "name": "Charlie",
                "role": "user",
                "department": "engineering",
                "active": False,
                "preferences": {"theme": "dark", "notifications": False}
            },
            # Repeat pattern to show benefits
            {
                "id": 4,
                "name": "Dave",
                "role": "user",
                "department": "sales",
                "active": True,
                "preferences": {"theme": "light", "notifications": True}
            }
        ] * 5  # Multiply to simulate larger dataset
    }

    print(f"Original Items: {len(data['users'])}")

    # 2. Compress the data
    print("\nCompressing data...")
    compressed = toon.compress(data)

    # Show compressed structure structure
    print("\nCompressed Structure Keys:", compressed.keys())
    # Keys will be: '_sdc_schema', '_sdc_table', etc.

    # 3. Compare sizes (serialized JSON)
    original_json = json.dumps(data)
    compressed_json = json.dumps(compressed)
    
    orig_size = len(original_json)
    comp_size = len(compressed_json)
    
    print(f"\nOriginal JSON Size: {orig_size} chars")
    print(f"Compressed JSON Size: {comp_size} chars")
    print(f"Reduction: {(orig_size - comp_size) / orig_size * 100:.1f}%")

    # 4. Decompress back to original
    print("\nDecompressing...")
    restored = toon.decompress(compressed)

    # Verify integrity
    if restored == data:
        print("SUCCESS: Data restored perfectly!")
    else:
        print("ERROR: Data mismatch!")

    # 5. Using the Class directly for advanced options
    print("\n--- Advanced Usage ---")
    compressor = SmartCompressor()
    
    # Analyze potential savings without compressing
    if compressor.should_compress(data):
        print("Analyzer suggests compression is beneficial.")
    else:
        print("Analyzer suggests compression is NOT beneficial.")


if __name__ == "__main__":
    run_compression_example()
