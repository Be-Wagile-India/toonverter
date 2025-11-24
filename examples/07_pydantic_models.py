#!/usr/bin/env python3
"""
Example 7: Pydantic Model Integration

Demonstrates:
- Serializing Pydantic models to TOON
- Deserializing TOON back to Pydantic
- Validation with TOON
- Nested models
"""

try:
    from pydantic import BaseModel, Field, validator
    from typing import List, Optional
    from datetime import datetime
    from toonverter.integrations import pydantic_to_toon, toon_to_pydantic

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("Install pydantic: pip install toonverter[pydantic]")

import toonverter as toon


# Define Pydantic models
class Address(BaseModel):
    """Address model."""

    street: str
    city: str
    zip_code: str
    country: str = "USA"


class User(BaseModel):
    """User model with validation."""

    id: int
    name: str
    email: str
    age: int = Field(ge=0, le=150)
    active: bool = True
    address: Address | None = None
    tags: list[str] = []

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v


class Project(BaseModel):
    """Project model."""

    name: str
    description: str
    members: list[User]
    created: datetime
    budget: float


def example_simple_model():
    """Convert simple Pydantic model."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- Simple Model Conversion ---")

    # Create user
    user = User(id=1, name="Alice", email="alice@example.com", age=30, tags=["python", "ai", "ml"])

    print("\nOriginal Pydantic model:")
    print(user)

    # Serialize to TOON
    toon_str = pydantic_to_toon(user)
    print("\nTOON representation:")
    print(toon_str)

    # Deserialize back to Pydantic
    restored_user = toon_to_pydantic(toon_str, User)
    print("\nRestored Pydantic model:")
    print(restored_user)

    # Verify equality
    print(f"\nRoundtrip successful: {user == restored_user}")


def example_nested_models():
    """Convert nested Pydantic models."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- Nested Models ---")

    # Create user with address
    user = User(
        id=1,
        name="Alice",
        email="alice@example.com",
        age=30,
        address=Address(street="123 Main St", city="NYC", zip_code="10001"),
        tags=["python", "ai"],
    )

    print("\nNested Pydantic model:")
    print(user.model_dump())

    # Serialize to TOON
    toon_str = pydantic_to_toon(user)
    print("\nTOON representation:")
    print(toon_str)

    # Deserialize
    restored_user = toon_to_pydantic(toon_str, User)
    print("\nRestored model:")
    print(restored_user.model_dump())


def example_list_of_models():
    """Convert list of Pydantic models."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- List of Models ---")

    # Create multiple users
    users = [
        User(id=1, name="Alice", email="alice@example.com", age=30),
        User(id=2, name="Bob", email="bob@example.com", age=25),
        User(id=3, name="Charlie", email="charlie@example.com", age=35),
    ]

    print(f"\nCreated {len(users)} users")

    # Serialize list
    users_dict = {"users": [u.model_dump() for u in users]}
    toon_str = toon.encode(users_dict)
    print("\nTOON representation:")
    print(toon_str)

    # Token analysis
    import json

    json_str = json.dumps(users_dict)
    print(f"\nJSON size: {len(json_str)} bytes")
    print(f"TOON size: {len(toon_str)} bytes")
    print(f"Savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")


def example_validation():
    """Test validation with TOON."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- Validation ---")

    # Valid user
    valid_user = User(id=1, name="Alice", email="alice@example.com", age=30)

    toon_str = pydantic_to_toon(valid_user)
    print("\nValid user TOON:")
    print(toon_str)

    # Try to deserialize with validation
    try:
        restored = toon_to_pydantic(toon_str, User)
        print("\nValidation passed!")
        print(f"Restored: {restored}")
    except Exception as e:
        print(f"\nValidation failed: {e}")

    # Invalid TOON (invalid email)
    invalid_toon = """
    id: 1
    name: Alice
    email: invalid-email-without-at
    age: 30
    active: true
    tags[0]:
    """

    print("\nTrying invalid TOON (bad email):")
    try:
        restored = toon_to_pydantic(invalid_toon, User)
        print(f"Restored: {restored}")
    except Exception as e:
        print(f"Validation failed as expected: {type(e).__name__}")


def example_complex_model():
    """Complex model with all features."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- Complex Model ---")

    # Create project with multiple users
    project = Project(
        name="AI Platform",
        description="Next-generation AI platform",
        members=[
            User(id=1, name="Alice", email="alice@example.com", age=30),
            User(id=2, name="Bob", email="bob@example.com", age=25),
        ],
        created=datetime(2025, 1, 15, 10, 30, 0),
        budget=500000.00,
    )

    print("\nComplex Pydantic model:")
    print(project.model_dump())

    # Serialize to TOON
    project_dict = project.model_dump()
    toon_str = toon.encode(project_dict)
    print("\nTOON representation:")
    print(toon_str)

    # Token analysis
    import json

    json_str = json.dumps(project_dict, default=str)
    report = toon.analyze(project_dict, compare_formats=["json", "toon"])

    print(f"\nToken savings: {report.max_savings_percentage:.1f}%")


def example_api_response():
    """API response optimization."""
    if not PYDANTIC_AVAILABLE:
        return

    print("\n--- API Response Optimization ---")

    # Simulate API response
    users = [
        User(id=i, name=f"User{i}", email=f"user{i}@example.com", age=20 + i) for i in range(1, 101)
    ]

    response = {
        "users": [u.model_dump() for u in users],
        "total": len(users),
        "page": 1,
        "per_page": 100,
    }

    print(f"\nAPI response: {len(users)} users")

    # Compare formats
    import json

    json_str = json.dumps(response)
    toon_str = toon.encode(response)

    print(f"\nJSON size: {len(json_str):,} bytes")
    print(f"TOON size: {len(toon_str):,} bytes")
    print(f"Bandwidth savings: {((len(json_str) - len(toon_str)) / len(json_str) * 100):.1f}%")

    # Token analysis
    report = toon.analyze(response, compare_formats=["json", "toon"])
    print(f"Token savings: {report.max_savings_percentage:.1f}%")


def main():
    print("=" * 60)
    print("Example 7: Pydantic Model Integration")
    print("=" * 60)

    if not PYDANTIC_AVAILABLE:
        print("\nPlease install: pip install toonverter[pydantic]")
        return

    example_simple_model()
    example_nested_models()
    example_list_of_models()
    example_validation()
    example_complex_model()
    example_api_response()


if __name__ == "__main__":
    main()
