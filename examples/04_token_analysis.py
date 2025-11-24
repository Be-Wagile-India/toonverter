#!/usr/bin/env python3
"""
Example 4: Token Analysis and Comparison

Demonstrates:
- Analyzing token usage across formats
- Comparing JSON, YAML, TOON
- Finding the most efficient format
- Understanding token savings
"""

import toonverter as toon
import json


def analyze_simple_object():
    """Analyze token usage for simple object."""
    print("\n--- Simple Object Analysis ---")

    data = {"name": "Alice", "age": 30, "city": "NYC", "active": True}

    # Analyze across all formats
    report = toon.analyze(data, compare_formats=["json", "yaml", "toon"])

    print("\nData:", data)
    print("\nToken counts by format:")
    for fmt, result in report.format_results.items():
        print(f"  {fmt:6s}: {result.token_count:3d} tokens ({result.byte_size:4d} bytes)")

    print(f"\nBest format: {report.best_format}")
    print(f"Max savings: {report.max_savings_percentage:.1f}%")


def analyze_tabular_data():
    """Analyze token usage for tabular data."""
    print("\n--- Tabular Data Analysis ---")

    data = {
        "users": [
            {"id": i, "name": f"User{i}", "value": i * 10}
            for i in range(1, 101)  # 100 rows
        ]
    }

    print(f"\nDataset: {len(data['users'])} rows, 3 columns")

    # Analyze
    report = toon.analyze(data, compare_formats=["json", "yaml", "toon"])

    print("\nToken counts by format:")
    for fmt, result in report.format_results.items():
        savings = (
            0
            if fmt == "json"
            else (
                (report.format_results["json"].token_count - result.token_count)
                / report.format_results["json"].token_count
                * 100
            )
        )
        print(f"  {fmt:6s}: {result.token_count:5d} tokens ({savings:5.1f}% savings)")

    print(f"\nBest format: {report.best_format}")
    print(f"TOON saves {report.max_savings_percentage:.1f}% tokens vs JSON")


def analyze_nested_structure():
    """Analyze token usage for nested structure."""
    print("\n--- Nested Structure Analysis ---")

    data = {
        "company": "TechCorp",
        "departments": [
            {
                "name": "Engineering",
                "employees": [
                    {"id": 1, "name": "Alice", "role": "Engineer"},
                    {"id": 2, "name": "Bob", "role": "Senior Engineer"},
                ],
            },
            {"name": "Sales", "employees": [{"id": 3, "name": "Charlie", "role": "Sales Rep"}]},
        ],
        "metadata": {"created": "2025-01-15", "version": "1.0"},
    }

    # Analyze
    report = toon.analyze(data, compare_formats=["json", "yaml", "toon"])

    print("\nToken counts by format:")
    for fmt, result in report.format_results.items():
        print(f"  {fmt:6s}: {result.token_count:4d} tokens ({result.byte_size:4d} bytes)")

    print(
        f"\nRecommendation: Use {report.best_format} for {report.max_savings_percentage:.1f}% savings"
    )


def compare_with_different_tokenizers():
    """Compare token counts using different tokenizer models."""
    print("\n--- Different Tokenizer Models ---")

    data = {
        "message": "The quick brown fox jumps over the lazy dog",
        "tags": ["example", "demo", "test"],
        "count": 42,
    }

    print("\nData:", json.dumps(data))

    # Try different tokenizer models
    for model in ["gpt-4", "gpt-3.5-turbo"]:
        try:
            from toonverter import Analyzer

            analyzer = Analyzer(model=model)
            report = analyzer.analyze_multi_format(data, formats=["json", "toon"])

            print(f"\nTokenizer: {model}")
            print(f"  JSON: {report.format_results['json'].token_count} tokens")
            print(f"  TOON: {report.format_results['toon'].token_count} tokens")
            print(f"  Savings: {report.max_savings_percentage:.1f}%")
        except Exception as e:
            print(f"\nTokenizer {model}: Error - {e}")


def real_world_example():
    """Real-world example: LLM context optimization."""
    print("\n--- Real-World: LLM Context Optimization ---")

    # Simulate a dataset for RAG system
    documents = {
        "documents": [
            {
                "id": i,
                "content": f"This is document {i} containing important information about topic {i % 5}.",
                "metadata": {"source": f"doc{i}.pdf", "page": i % 100},
            }
            for i in range(1, 51)  # 50 documents
        ]
    }

    print(f"\nScenario: RAG system with {len(documents['documents'])} documents")

    # Analyze
    report = toon.analyze(documents, compare_formats=["json", "toon"])

    json_tokens = report.format_results["json"].token_count
    toon_tokens = report.format_results["toon"].token_count
    tokens_saved = json_tokens - toon_tokens

    print(f"\nJSON format: {json_tokens} tokens")
    print(f"TOON format: {toon_tokens} tokens")
    print(f"Tokens saved: {tokens_saved} ({report.max_savings_percentage:.1f}%)")

    # Calculate cost impact (example: GPT-4 pricing)
    gpt4_input_cost_per_1k = 0.03  # $0.03 per 1K tokens
    cost_json = (json_tokens / 1000) * gpt4_input_cost_per_1k
    cost_toon = (toon_tokens / 1000) * gpt4_input_cost_per_1k
    cost_saved = cost_json - cost_toon

    print(f"\nCost impact (GPT-4 pricing):")
    print(f"  JSON: ${cost_json:.4f}")
    print(f"  TOON: ${cost_toon:.4f}")
    print(f"  Saved: ${cost_saved:.4f} per request")
    print(f"  Annual savings (1M requests): ${cost_saved * 1000000:.2f}")


def main():
    print("=" * 60)
    print("Example 4: Token Analysis and Comparison")
    print("=" * 60)

    analyze_simple_object()
    analyze_tabular_data()
    analyze_nested_structure()
    compare_with_different_tokenizers()
    real_world_example()


if __name__ == "__main__":
    main()
