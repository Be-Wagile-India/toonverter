"""Tests for Redis integration."""

from unittest.mock import MagicMock, Mock

import pytest


try:
    import redis  # noqa: F401

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from toonverter.integrations.redis_integration import RedisToonWrapper


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = MagicMock()
    # Mock json interface
    mock.json.return_value = Mock()
    return mock


class TestRedisIntegration:
    def test_get_json_success(self, mock_redis):
        """Test retrieving a single JSON object."""
        wrapper = RedisToonWrapper(mock_redis)

        # Setup mock return
        data = {"id": 1, "name": "Test"}
        mock_redis.json.return_value.get.return_value = data

        result = wrapper.get_json("key:1")

        assert "id" in result
        assert "Test" in result
        assert ":" in result  # Check for TOON syntax roughly
        mock_redis.json.return_value.get.assert_called_with("key:1")

    def test_get_json_missing(self, mock_redis):
        """Test retrieving a missing key."""
        wrapper = RedisToonWrapper(mock_redis)
        mock_redis.json.return_value.get.return_value = None

        result = wrapper.get_json("missing")
        assert result is None

    def test_mget_json_tabular(self, mock_redis):
        """Test retrieving multiple JSONs that form a table."""
        wrapper = RedisToonWrapper(mock_redis)

        data = [{"id": 1, "role": "admin"}, {"id": 2, "role": "user"}, {"id": 3, "role": "user"}]
        # Mock mget
        mock_redis.json.return_value.mget.return_value = data

        result = wrapper.mget_json(["k1", "k2", "k3"])

        # Verify it used tabular format (header with fields)
        assert "{id,role}" in result or "{role,id}" in result
        assert "admin" in result

    def test_mget_fallback_pipeline(self, mock_redis):
        """Test fallback to pipeline when mget fails."""
        wrapper = RedisToonWrapper(mock_redis)

        # Simulate mget not existing or failing
        mock_redis.json.return_value.mget.side_effect = AttributeError

        # Setup pipeline mock
        pipeline = MagicMock()
        mock_redis.pipeline.return_value = pipeline
        pipeline.execute.return_value = [{"a": 1}, {"a": 2}]

        result = wrapper.mget_json(["k1", "k2"])

        assert "[2]{a}:" in result or "a: 1" in result  # Depending on format decision
        assert pipeline.json.return_value.get.call_count == 2

    def test_hgetall_decoding(self, mock_redis):
        """Test hash retrieval with byte decoding."""
        wrapper = RedisToonWrapper(mock_redis)

        # Return bytes like real Redis
        mock_redis.hgetall.return_value = {b"field1": b"value1", b"count": b"10"}

        result = wrapper.hgetall("hash:1")

        assert "field1" in result
        assert "value1" in result

    def test_hgetall_missing(self, mock_redis):
        """Test missing hash."""
        wrapper = RedisToonWrapper(mock_redis)
        mock_redis.hgetall.return_value = {}

        assert wrapper.hgetall("missing") is None

    def test_search_results_optimization(self, mock_redis):
        """Test optimizing search results list."""
        wrapper = RedisToonWrapper(mock_redis)

        results = [
            {"id": 1, "score": 0.9, "extra": "ignore"},
            {"id": 2, "score": 0.8, "extra": "ignore"},
        ]

        # Project only specific fields
        result = wrapper.search_results(results, fields=["id", "score"])

        assert "extra" not in result
        assert "id" in result
        assert "score" in result
        # Should be compact
        assert "\n" not in result or " " not in result  # rough check for compact

    def test_search_results_objects(self, mock_redis):
        """Test search results passed as objects."""
        wrapper = RedisToonWrapper(mock_redis)

        class ResultObj:
            def __init__(self, i):
                self.id = i

        results = [ResultObj(1), ResultObj(2)]

        result = wrapper.search_results(results)
        assert "id" in result
        assert "1" in result

        def test_empty_results(self, mock_redis):
            """Test empty result sets."""
            wrapper = RedisToonWrapper(mock_redis)

            # Mock mget to return an empty list when called with an empty list of keys
            mock_redis.json.return_value.mget.return_value = []

            assert wrapper.mget_json([]) == "[]"

            # Also test search_results with empty input
            assert wrapper.search_results([]) == "[]"
