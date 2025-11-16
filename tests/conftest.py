"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_dict():
    """Sample dictionary for testing."""
    return {"name": "Alice", "age": 30, "city": "NYC"}


@pytest.fixture
def sample_list():
    """Sample list for testing."""
    return [1, 2, 3, 4, 5]


@pytest.fixture
def sample_tabular():
    """Sample tabular data for testing."""
    return [
        {"name": "Alice", "age": 30, "city": "NYC"},
        {"name": "Bob", "age": 25, "city": "LA"},
        {"name": "Charlie", "age": 35, "city": "SF"},
    ]


@pytest.fixture
def sample_nested():
    """Sample nested data for testing."""
    return {
        "user": {"name": "Alice", "age": 30},
        "tags": ["python", "llm", "optimization"],
        "active": True,
    }
