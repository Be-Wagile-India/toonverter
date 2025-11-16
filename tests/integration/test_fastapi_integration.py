"""Integration tests for FastAPI support."""

import pytest

# Skip if fastapi not installed
pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from toonverter.integrations.fastapi_integration import TOONResponse


class User(BaseModel):
    """Test User model."""
    id: int
    name: str


app = FastAPI()


@app.get("/user", response_class=TOONResponse)
def get_user():
    """Test endpoint returning TOON."""
    return {"id": 1, "name": "Alice"}


@app.get("/users", response_class=TOONResponse)
def get_users():
    """Test endpoint returning list as TOON."""
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]


class TestFastAPIIntegration:
    """Test FastAPI TOON response."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_toon_response_single_object(self):
        """Test TOON response for single object."""
        response = self.client.get("/user")

        assert response.status_code == 200
        content = response.text

        assert 'Alice' in content
        assert '1' in content

    def test_toon_response_array(self):
        """Test TOON response for array."""
        response = self.client.get("/users")

        assert response.status_code == 200
        content = response.text

        assert '[2]' in content
        assert 'Alice' in content and 'Bob' in content
