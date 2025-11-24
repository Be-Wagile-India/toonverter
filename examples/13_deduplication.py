"""
Semantic Deduplication Example
=============================

This example demonstrates how to use the semantic deduplication feature
to identify and remove duplicate items from lists based on their meaning,
not just their exact byte structure.
"""

import toonverter as toon
from toonverter.analysis.deduplication import SemanticDeduplicator

def main():
    # Sample data with semantic duplicates
    # "Software Engineer" vs "Software Developer" vs "Programmer"
    # "AI Researcher" vs "Artificial Intelligence Scientist"
    data = {
        "company": "TechCorp",
        "employees": [
            {"id": 1, "role": "Software Engineer", "skills": ["Python", "Rust"]},
            {"id": 2, "role": "HR Manager", "skills": ["Recruiting", "Communication"]},
            {"id": 3, "role": "Software Developer", "skills": ["Python", "C++"]},  # Duplicate of 1
            {"id": 4, "role": "AI Researcher", "skills": ["PyTorch", "TensorFlow"]},
            {"id": 5, "role": "Programmer", "skills": ["Java", "Kotlin"]},         # Duplicate of 1
            {"id": 6, "role": "Artificial Intelligence Scientist", "skills": ["JAX"]}, # Duplicate of 4
        ]
    }

    print("--- Original Data ---")
    for emp in data["employees"]:
        print(f"ID: {emp['id']}, Role: {emp['role']}")

    print("\n--- Running Semantic Deduplication ---")
    # Optimize using default settings (all-MiniLM-L6-v2 model)
    # Threshold 0.7 is relatively loose to catch "Programmer" vs "Software Engineer"
    optimized_data = toon.deduplicate(
        data, 
        model_name="all-MiniLM-L6-v2", 
        threshold=0.7
    )

    print("\n--- Deduplicated Data ---")
    for emp in optimized_data["employees"]:
        print(f"ID: {emp['id']}, Role: {emp['role']}")
        
    # You can also use the class directly for more control
    print("\n--- Using SemanticDeduplicator Class directly ---")
    deduplicator = SemanticDeduplicator(threshold=0.85)
    # Note: With a higher threshold, "Programmer" might not match "Software Engineer"
    # but "Software Engineer" and "Software Developer" likely will.
    
    optimized_strict = deduplicator.optimize(data)
    print(f"Items remaining with 0.85 threshold: {len(optimized_strict['employees'])}")

if __name__ == "__main__":
    main()
