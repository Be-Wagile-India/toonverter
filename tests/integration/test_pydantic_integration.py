"""Integration tests for Pydantic model support."""

import pytest


# Skip if pydantic not installed
pytest.importorskip("pydantic")


from pydantic import BaseModel

from toonverter.integrations.pydantic_integration import pydantic_to_toon, toon_to_pydantic


class User(BaseModel):
    """Test User model."""

    id: int
    name: str
    age: int
    active: bool = True
    email: str | None = None


class Post(BaseModel):
    """Test Post model."""

    id: int
    title: str
    content: str
    author: User
    tags: list[str] = []


class TestPydanticModelSerialization:
    """Test Pydantic model serialization."""

    def test_simple_model_pydantic_to_toon(self):
        """Test converting Pydantic model to TOON."""
        user = User(id=1, name="Alice", age=30, active=True)

        toon = pydantic_to_toon(user)

        assert "Alice" in toon
        assert "30" in toon
        assert "true" in toon

    def test_model_roundtrip(self):
        """Test Pydantic model roundtrip."""
        user_original = User(id=1, name="Bob", age=25, active=False, email="bob@example.com")

        toon = pydantic_to_toon(user_original)
        user_result = toon_to_pydantic(toon, model=User)

        assert user_result.name == "Bob"
        assert user_result.age == 25
        assert user_result.active is False
        assert user_result.email == "bob@example.com"

    def test_nested_model(self):
        """Test nested Pydantic models."""
        user = User(id=1, name="Alice", age=30)
        post = Post(
            id=1, title="My Post", content="Content here", author=user, tags=["python", "toon"]
        )

        toon = pydantic_to_toon(post)

        assert "My Post" in toon
        assert "Alice" in toon
        assert "python" in toon

    def test_list_of_models(self):
        """Test list of Pydantic models."""
        users = [
            User(id=1, name="Alice", age=30),
            User(id=2, name="Bob", age=25),
            User(id=3, name="Carol", age=35),
        ]

        toon = pydantic_to_toon(users)

        # Should use tabular or list format
        assert "Alice" in toon
        assert "Bob" in toon
        assert "Carol" in toon

    def test_optional_fields(self):
        """Test models with optional fields."""
        user_with_email = User(id=1, name="Alice", age=30, email="alice@example.com")
        user_without_email = User(id=2, name="Bob", age=25)

        toon1 = pydantic_to_toon(user_with_email)
        toon2 = pydantic_to_toon(user_without_email)

        assert "alice@example.com" in toon1
        assert "null" in toon2 or "email" not in toon2


class TestPydanticValidation:
    """Test Pydantic validation during deserialization."""

    def test_invalid_data_raises_error(self):
        """Test that invalid data raises validation error."""
        toon = "name: Alice\nage: invalid"

        with pytest.raises(Exception):  # ValidationError or similar
            toon_to_pydantic(toon, model=User)

    def test_missing_required_field(self):
        """Test missing required field."""
        toon = "name: Alice"  # Missing id and age

        with pytest.raises(Exception):
            toon_to_pydantic(toon, model=User)
