"""Integration tests for Instructor support."""

import pytest


# Skip if instructor not installed
pytest.importorskip("instructor")

from pydantic import BaseModel

from toonverter.integrations.instructor_integration import response_to_toon, toon_to_response


class UserResponse(BaseModel):
    """Test response model."""

    name: str
    age: int
    email: str


class TestInstructorResponses:
    """Test Instructor response handling."""

    def test_response_to_toon(self):
        """Test converting Instructor response to TOON."""
        response = UserResponse(name="Alice", age=30, email="alice@example.com")

        toon = response_to_toon(response)

        assert "Alice" in toon
        assert "30" in toon
        assert "alice@example.com" in toon

    def test_response_roundtrip(self):
        """Test response roundtrip."""
        response_original = UserResponse(name="Bob", age=25, email="bob@example.com")

        toon = response_to_toon(response_original)
        response_result = toon_to_response(toon, model_class=UserResponse)

        assert response_result.name == "Bob"
        assert response_result.age == 25
        assert response_result.email == "bob@example.com"

    def test_batch_responses(self):
        """Test batch of responses."""
        responses = [
            UserResponse(name="User1", age=20, email="user1@example.com"),
            UserResponse(name="User2", age=30, email="user2@example.com"),
            UserResponse(name="User3", age=40, email="user3@example.com"),
        ]

        toon = response_to_toon(responses)

        assert "User1" in toon
        assert "User2" in toon
        assert "User3" in toon
