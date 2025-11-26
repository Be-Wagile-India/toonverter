"""Example of using the structural diff tool.

This example demonstrates how to find semantic differences between complex
data structures, which is useful for version control, change tracking, and debugging.
"""

import toonverter as toon
from toonverter.differ import DiffChange


def run_diff_example():
    """Run diff example."""
    print("--- Structural Diff Example ---\n")

    # 1. Define two versions of a dataset
    version1 = {
        "app_name": "ToonApp",
        "version": "1.0.0",
        "features": ["encoding", "decoding"],
        "config": {
            "timeout": 30,
            "retries": 3,
            "debug": False
        },
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }

    version2 = {
        "app_name": "ToonApp Pro",           # Changed value
        "version": "1.1.0",                  # Changed value
        "features": ["encoding", "decoding", "analysis"], # Added item
        "config": {
            "timeout": 60,                   # Changed value
            "retries": 3,                    # Same
            # "debug": False                 # Removed key
            "logging": True                  # Added key
        },
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Robert"}      # Changed nested value
        ]
    }

    # 2. Calculate Diff
    print("Calculating differences...")
    diff_result = toon.diff(version1, version2)

    print(f"\nMatch: {diff_result.match}")
    print(f"Total Changes: {len(diff_result.changes)}")

    # 3. Inspect changes
    print("\nDetailed Changes:")
    for change in diff_result.changes:
        print_change(change)

    # 4. Textual Report
    # Note: You would typically use a formatter here, but we can print manually
    print("\n--- Summary Report ---")
    adds = sum(1 for c in diff_result.changes if c.type.value == "added")
    removes = sum(1 for c in diff_result.changes if c.type.value == "removed")
    mods = sum(1 for c in diff_result.changes if c.type.value == "modified")
    
    print(f"Added: {adds}, Removed: {removes}, Modified: {mods}")


def print_change(change: DiffChange):
    """Helper to print a change object nicely."""
    path_str = ".".join(str(p) for p in change.path)
    if not path_str:
        path_str = "(root)"
        
    action = change.type.value.upper()
    
    if action == "MODIFIED":
        print(f"[{action}] {path_str}: {change.old_value} -> {change.new_value}")
    elif action == "ADDED":
        print(f"[{action}] {path_str}: {change.new_value}")
    elif action == "REMOVED":
        print(f"[{action}] {path_str}: (was {change.old_value})")


if __name__ == "__main__":
    run_diff_example()
