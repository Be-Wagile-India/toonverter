"""
Schema Tools Example
===================

This example demonstrates how to use TOON Converter's schema tools:
1. Inference: Generating a schema from data
2. Validation: Checking data against a schema
3. Merging: Combining multiple schemas into a unified one
"""

import json
from toonverter import infer_schema, validate_schema

def main():
    # 1. Infer Schema from Data
    print("--- 1. Schema Inference ---")
    user_data = {
        "id": 123,
        "username": "jdoe",
        "is_active": True,
        "roles": ["admin", "editor"],
        "metadata": {"last_login": "2023-01-01"}
    }
    
    schema = infer_schema(user_data)
    print("Inferred Schema:")
    print(json.dumps(schema.to_dict(), indent=2))
    
    # 2. Validate Data
    print("\n--- 2. Schema Validation ---")
    valid_data = {
        "id": 456,
        "username": "alice",
        "is_active": False,
        "roles": ["viewer"],
        "metadata": {"last_login": "2023-02-01"}
    }
    
    invalid_data = {
        "id": "not-an-int", # Error: type mismatch
        "username": "bob",
        # Missing 'is_active' (required by default)
        "roles": "not-a-list" # Error: type mismatch
    }
    
    errors = validate_schema(valid_data, schema)
    if not errors:
        print("valid_data is Valid!")
        
    errors = validate_schema(invalid_data, schema)
    if errors:
        print(f"invalid_data has {len(errors)} errors:")
        for e in errors:
            print(f" - {e}")

    # 3. Schema Merging
    print("\n--- 3. Schema Merging ---")
    # Schema 1: Object with 'name' (string)
    data1 = {"name": "Product A", "price": 10}
    schema1 = infer_schema(data1)
    
    # Schema 2: Object with 'name' (string) and optional 'tags' (list)
    # and 'price' is float here
    data2 = {"name": "Product B", "price": 12.50, "tags": ["sale"]}
    schema2 = infer_schema(data2)
    
    # Merge them
    merged_schema = schema1.merge(schema2)
    
    print("Merged Schema:")
    print(json.dumps(merged_schema.to_dict(), indent=2))
    
    # Notice: 
    # - 'price' should be float (widened from int)
    # - 'tags' should be present but not required (since it was missing in data1)

if __name__ == "__main__":
    main()
