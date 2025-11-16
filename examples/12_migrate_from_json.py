#!/usr/bin/env python3
"""
Example 12: Migrating from JSON to TOON

Demonstrates:
- Step-by-step migration guide
- Backward compatibility
- Gradual adoption
- Best practices
"""

import toonverter as toon
import json
import tempfile
import os


def step1_simple_replacement():
    """Step 1: Simple JSON.dumps/loads replacement."""
    print("\n--- Step 1: Simple Replacement ---")

    data = {"name": "Alice", "age": 30}

    # Before (JSON)
    json_str = json.dumps(data)
    decoded_json = json.loads(json_str)

    print(f"JSON: {json_str}")
    print(f"Decoded: {decoded_json}")

    # After (TOON)
    toon_str = toon.encode(data)
    decoded_toon = toon.decode(toon_str)

    print(f"\nTOON: {toon_str}")
    print(f"Decoded: {decoded_toon}")


def step2_file_migration():
    """Step 2: Migrate JSON files to TOON."""
    print("\n--- Step 2: File Migration ---")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Original JSON file
        json_file = os.path.join(tmpdir, "config.json")
        data = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"ttl": 3600}
        }

        # Save as JSON (old way)
        with open(json_file, 'w') as f:
            json.dump(data, f)

        print(f"JSON file: {json_file}")

        # Migrate to TOON
        toon_file = os.path.join(tmpdir, "config.toon")
        toon.convert(source=json_file, target=toon_file, from_format='json', to_format='toon')

        print(f"TOON file: {toon_file}")

        # Load from TOON (new way)
        loaded = toon.load(toon_file)
        print(f"Loaded: {loaded}")


def step3_backward_compatibility():
    """Step 3: Maintain backward compatibility."""
    print("\n--- Step 3: Backward Compatibility ---")

    # Support both formats
    def load_config(filepath):
        """Load config from JSON or TOON."""
        if filepath.endswith('.toon'):
            return toon.load(filepath, format='toon')
        elif filepath.endswith('.json'):
            return toon.load(filepath, format='json')
        else:
            # Auto-detect
            with open(filepath) as f:
                content = f.read()
                try:
                    return toon.decode(content, format='toon')
                except:
                    return json.loads(content)

    print("Unified config loader supports both JSON and TOON")


def step4_api_migration():
    """Step 4: Migrate API responses."""
    print("\n--- Step 4: API Response Migration ---")

    # Before: JSON response
    def get_users_json():
        users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        return json.dumps(users)

    # After: TOON response (optional)
    def get_users_toon():
        users = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        return toon.encode(users)

    json_response = get_users_json()
    toon_response = get_users_toon()

    print(f"JSON response: {json_response}")
    print(f"TOON response: {toon_response}")
    print(f"Savings: {((len(json_response) - len(toon_response)) / len(json_response) * 100):.1f}%")


def step5_best_practices():
    """Step 5: Best practices for TOON adoption."""
    print("\n--- Step 5: Best Practices ---")

    print("""
    1. Start with new features/services
    2. Use TOON for internal APIs first
    3. Maintain JSON for public APIs initially
    4. Add Content-Type negotiation (application/toon)
    5. Monitor token usage and savings
    6. Use strict mode in production
    7. Include TOON in CI/CD pipelines
    8. Document migration in API versioning
    """)


def migration_checklist():
    """Migration checklist."""
    print("\n--- Migration Checklist ---")

    checklist = [
        "☐ Install toonverter library",
        "☐ Replace json.dumps() with toon.encode()",
        "☐ Replace json.loads() with toon.decode()",
        "☐ Convert config files to TOON format",
        "☐ Update file loading logic",
        "☐ Add backward compatibility layer",
        "☐ Update API endpoints (optional)",
        "☐ Add Content-Type negotiation",
        "☐ Enable strict mode for validation",
        "☐ Monitor token usage metrics",
        "☐ Update documentation",
        "☐ Train team on TOON format"
    ]

    print("\nMigration Checklist:")
    for item in checklist:
        print(f"  {item}")


def main():
    print("=" * 60)
    print("Example 12: Migrating from JSON to TOON")
    print("=" * 60)

    step1_simple_replacement()
    step2_file_migration()
    step3_backward_compatibility()
    step4_api_migration()
    step5_best_practices()
    migration_checklist()

    print("\n" + "=" * 60)
    print("Migration complete! Enjoy 30-60% token savings! 🚀")
    print("=" * 60)


if __name__ == "__main__":
    main()
