"""Pandas DataFrame integration example."""

try:
    import pandas as pd
    from toonverter.integrations import pandas_to_toon, toon_to_pandas
    import toonverter as toon

    print("=" * 60)
    print("Pandas DataFrame Integration Example")
    print("=" * 60)

    # Create a DataFrame
    df = pd.DataFrame(
        {
            "product": ["Widget", "Gadget", "Gizmo", "Doohickey"],
            "price": [19.99, 29.99, 39.99, 49.99],
            "stock": [100, 50, 75, 30],
            "available": [True, True, False, True],
        }
    )

    print("\nOriginal DataFrame:")
    print(df)
    print()

    # Convert to TOON (extremely efficient for tabular data)
    toon_str = pandas_to_toon(df)
    print("TOON format:")
    print(toon_str)
    print()

    # Analyze token savings
    json_str = df.to_json()
    toon_tokens = toon.count_tokens(toon_str)
    json_tokens = toon.count_tokens(json_str)
    savings = ((json_tokens - toon_tokens) / json_tokens) * 100

    print(f"JSON tokens: {json_tokens}")
    print(f"TOON tokens: {toon_tokens}")
    print(f"Token savings: {savings:.1f}%")
    print()

    # Convert back to DataFrame
    restored_df = toon_to_pandas(toon_str)
    print("Restored DataFrame:")
    print(restored_df)
    print()

    print("✓ Round-trip successful!")

except ImportError:
    print("This example requires pandas.")
    print("Install with: pip install toonverter[integrations]")
