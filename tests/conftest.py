"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the format registry before each test to avoid singleton state issues."""
    from toonverter.core.registry import registry

    # Clear registry before test
    registry.clear()

    # Re-register default formats
    from toonverter.formats import register_default_formats

    register_default_formats()

    yield

    # Clear after test
    registry.clear()


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
