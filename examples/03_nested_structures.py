#!/usr/bin/env python3
"""
Example 3: Nested Structures

Demonstrates TOON's handling of:
- Nested objects
- Nested arrays
- Mixed nested structures
- Complex real-world data
"""

import toonverter as toon
import json


def example_nested_objects():
    """Example with nested objects."""
    print("\n--- Nested Objects ---")

    data = {
        "user": {
            "name": "Alice",
            "age": 30,
            "address": {
                "street": "123 Main St",
                "city": "NYC",
                "zip": "10001",
                "coordinates": {"lat": 40.7128, "lon": -74.0060},
            },
        }
    }

    print("\nOriginal JSON:")
    print(json.dumps(data, indent=2))

    # Encode to TOON
    toon_str = toon.encode(data)
    print("\nTOON representation:")
    print(toon_str)

    # Decode back
    decoded = toon.decode(toon_str)
    print("\nRoundtrip successful:", data == decoded)


def example_nested_arrays():
    """Example with nested arrays."""
    print("\n--- Nested Arrays ---")

    data = {
        "users": [
            {
                "name": "Alice",
                "tags": ["python", "ai", "ml"],
                "projects": [
                    {"name": "Project1", "status": "active"},
                    {"name": "Project2", "status": "completed"},
                ],
            },
            {
                "name": "Bob",
                "tags": ["javascript", "web", "react"],
                "projects": [{"name": "Project3", "status": "active"}],
            },
        ]
    }

    print("\nOriginal JSON:")
    print(json.dumps(data, indent=2))

    # Encode to TOON
    toon_str = toon.encode(data)
    print("\nTOON representation:")
    print(toon_str)

    # Token analysis
    report = toon.analyze(data, compare_formats=["json", "toon"])
    print(f"\nToken savings: {report.max_savings_percentage:.1f}%")


def example_complex_structure():
    """Example with complex real-world structure."""
    print("\n--- Complex Real-World Structure ---")

    data = {
        "company": "TechCorp",
        "departments": [
            {
                "name": "Engineering",
                "employees": [
                    {
                        "id": 1,
                        "name": "Alice",
                        "skills": ["Python", "Go", "Rust"],
                        "projects": ["API", "Database"],
                    },
                    {
                        "id": 2,
                        "name": "Bob",
                        "skills": ["JavaScript", "React"],
                        "projects": ["Frontend"],
                    },
                ],
                "budget": 500000,
            },
            {
                "name": "Sales",
                "employees": [
                    {
                        "id": 3,
                        "name": "Charlie",
                        "skills": ["Negotiation", "CRM"],
                        "projects": ["Q1-Campaign"],
                    }
                ],
                "budget": 300000,
            },
        ],
        "metadata": {"created": "2025-01-15", "version": "1.0", "active": True},
    }

    print("\nOriginal JSON:")
    print(json.dumps(data, indent=2))

    # Encode to TOON
    toon_str = toon.encode(data)
    print("\nTOON representation:")
    print(toon_str)

    # Decode back
    decoded = toon.decode(toon_str)

    # Verify structure
    print("\nStructure verification:")
    print(f"Company: {decoded['company']}")
    print(f"Departments: {len(decoded['departments'])}")
    print(f"Total employees: {sum(len(d['employees']) for d in decoded['departments'])}")

    # Token analysis
    json_str = json.dumps(data)
    print(f"\nJSON size: {len(json_str)} chars")
    print(f"TOON size: {len(toon_str)} chars")
    print(f"Savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")


def example_array_forms():
    """Example showing different array forms in TOON."""
    print("\n--- Different Array Forms ---")

    data = {
        # Inline array (primitives)
        "tags": ["python", "llm", "ai"],
        # Tabular array (uniform objects with primitives)
        "users": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35},
        ],
        # List array (complex structures)
        "projects": [
            {
                "name": "Project1",
                "members": ["Alice", "Bob"],
                "metadata": {"status": "active", "priority": 1},
            },
            {
                "name": "Project2",
                "members": ["Charlie"],
                "metadata": {"status": "completed", "priority": 2},
            },
        ],
    }

    print("\nOriginal JSON:")
    print(json.dumps(data, indent=2))

    # Encode to TOON
    toon_str = toon.encode(data)
    print("\nTOON representation (note different array forms):")
    print(toon_str)

    print("\nArray form explanation:")
    print("- 'tags': Inline array [3]: python,llm,ai")
    print("- 'users': Tabular array [3]{name,age}: (CSV-like)")
    print("- 'projects': List array [2]: (with dash markers)")


def main():
    print("=" * 60)
    print("Example 3: Nested Structures")
    print("=" * 60)

    example_nested_objects()
    example_nested_arrays()
    example_complex_structure()
    example_array_forms()


if __name__ == "__main__":
    main()
