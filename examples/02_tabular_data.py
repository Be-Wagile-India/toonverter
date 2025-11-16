#!/usr/bin/env python3
"""
Example 2: Tabular Data Optimization

Demonstrates TOON's exceptional efficiency for tabular data:
- Pandas DataFrame conversion
- Tabular array format
- 40-60% token savings for uniform data
"""

import toonverter as toon

try:
    import pandas as pd
    from toonverter.integrations import pandas_to_toon, toon_to_pandas
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Note: Install pandas with 'pip install toonverter[pandas]' for full functionality")


def example_with_pandas():
    """Example using Pandas integration."""
    print("\n--- Using Pandas Integration ---")

    # Create a DataFrame
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'age': [30, 25, 35, 28, 32],
        'city': ['NYC', 'LA', 'SF', 'Boston', 'Seattle'],
        'salary': [75000, 65000, 85000, 70000, 80000]
    })

    print("\nOriginal DataFrame:")
    print(df)

    # Convert to TOON (uses optimal tabular format)
    toon_str = pandas_to_toon(df)
    print("\nTOON representation:")
    print(toon_str)

    # Convert back to DataFrame
    restored_df = toon_to_pandas(toon_str)
    print("\nRestored DataFrame:")
    print(restored_df)

    # Token analysis
    import json
    json_str = df.to_json(orient='records')

    print(f"\nJSON length: {len(json_str)} chars")
    print(f"TOON length: {len(toon_str)} chars")
    print(f"Savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")


def example_with_dict():
    """Example using plain Python dict (no pandas required)."""
    print("\n--- Using Plain Python Dict ---")

    # Create tabular data as list of dicts
    data = {
        "users": [
            {"id": 1, "name": "Alice", "age": 30, "city": "NYC"},
            {"id": 2, "name": "Bob", "age": 25, "city": "LA"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "SF"},
            {"id": 4, "name": "Diana", "age": 28, "city": "Boston"},
            {"id": 5, "name": "Eve", "age": 32, "city": "Seattle"}
        ]
    }

    print("\nOriginal data:")
    import json
    print(json.dumps(data, indent=2))

    # Encode to TOON (automatically detects tabular format)
    toon_str = toon.encode(data)
    print("\nTOON representation:")
    print(toon_str)

    # Decode back
    decoded = toon.decode(toon_str)
    print("\nDecoded data:")
    print(json.dumps(decoded, indent=2))

    # Token analysis
    report = toon.analyze(data, compare_formats=['json', 'toon'])
    print(f"\nToken savings: {report.max_savings_percentage:.1f}%")


def example_large_dataset():
    """Example with larger dataset to show scalability."""
    print("\n--- Large Dataset Example ---")

    # Create large dataset (1000 rows)
    data = {
        "records": [
            {"id": i, "value": i * 10, "category": f"Cat{i % 5}"}
            for i in range(1, 1001)
        ]
    }

    print(f"\nDataset size: {len(data['records'])} records")

    # Encode to TOON
    import time
    start = time.time()
    toon_str = toon.encode(data)
    elapsed = time.time() - start

    print(f"Encoding time: {elapsed*1000:.2f}ms")

    # Size comparison
    import json
    json_str = json.dumps(data)

    print(f"\nJSON size: {len(json_str):,} chars")
    print(f"TOON size: {len(toon_str):,} chars")
    print(f"Savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")

    # Token analysis
    report = toon.analyze(data, compare_formats=['json', 'toon'])
    print(f"Token savings: {report.max_savings_percentage:.1f}%")


def main():
    print("=" * 60)
    print("Example 2: Tabular Data Optimization")
    print("=" * 60)

    if PANDAS_AVAILABLE:
        example_with_pandas()

    example_with_dict()
    example_large_dataset()


if __name__ == "__main__":
    main()
