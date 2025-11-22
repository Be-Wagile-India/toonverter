from unittest.mock import patch

import pytest

from toonverter.utils.context_helpers import (
    _count_tokens_tiktoken,
    count_tokens,
    get_priority_key,
    optimize_context_window,
)


class TestCountTokens:
    """Test suite for count_tokens function."""

    def test_count_tokens_with_string(self):
        """Test counting tokens for a plain string."""
        text = "Hello, world!"
        result = count_tokens(text)
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_with_dict(self):
        """Test counting tokens for a dictionary."""
        data = {"role": "user", "content": "Hello"}
        result = count_tokens(data)
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_with_list(self):
        """Test counting tokens for a list."""
        data = ["item1", "item2", "item3"]
        result = count_tokens(data)
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_with_empty_string(self):
        """Test counting tokens for empty string."""
        result = count_tokens("")
        assert result >= 0

    def test_count_tokens_with_empty_dict(self):
        """Test counting tokens for empty dictionary."""
        result = count_tokens({})
        assert result >= 0

    def test_count_tokens_with_nested_structure(self):
        """Test counting tokens for nested data structures."""
        data = {"user": {"name": "John", "messages": ["Hello", "World"]}}
        result = count_tokens(data)
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_serialization_error(self):
        """Test handling of non-serializable objects."""

        class NonSerializable:
            pass

        result = count_tokens(NonSerializable())
        assert result == 0

    def test_count_tokens_with_special_characters(self):
        """Test counting tokens with special characters."""
        text = "Hello! @#$%^&*() 你好"
        result = count_tokens(text)
        assert isinstance(result, int)
        assert result > 0

    @patch("toonverter.utils.context_helpers._ENCODER", None)
    def test_count_tokens_fallback_without_tiktoken(self):
        """Test fallback when tiktoken is not available."""
        text = "Hello, world!"
        result = _count_tokens_tiktoken(text)
        assert result == len(text) // 4

    def test_count_tokens_with_long_text(self):
        """Test counting tokens for long text."""
        text = "word " * 1000
        result = count_tokens(text)
        assert isinstance(result, int)
        assert result > 100


class TestGetPriorityKey:
    """Test suite for get_priority_key function."""

    def test_recency_policy(self):
        """Test recency policy returns correct key function."""
        key_func = get_priority_key("recency")
        record1 = {"timestamp": 100}
        record2 = {"timestamp": 200}

        assert key_func(record1) == (-100,)
        assert key_func(record2) == (-200,)
        assert key_func(record2) < key_func(record1)

    def test_priority_then_recency_policy(self):
        """Test priority_then_recency policy."""
        key_func = get_priority_key("priority_then_recency")
        record1 = {"priority": 5, "timestamp": 100}
        record2 = {"priority": 10, "timestamp": 50}

        key1 = key_func(record1)
        key2 = key_func(record2)

        assert key2 < key1
        assert len(key1) == 2
        assert len(key2) == 2

    def test_priority_then_recency_with_same_priority(self):
        """Test priority_then_recency breaks ties by recency."""
        key_func = get_priority_key("priority_then_recency")
        record1 = {"priority": 5, "timestamp": 100}
        record2 = {"priority": 5, "timestamp": 200}

        key1 = key_func(record1)
        key2 = key_func(record2)

        assert key2 < key1

    def test_size_then_recency_policy(self):
        """Test size_then_recency policy."""
        key_func = get_priority_key("size_then_recency")
        record1 = {"token_count": 50, "timestamp": 100}
        record2 = {"token_count": 100, "timestamp": 50}

        key1 = key_func(record1)
        key2 = key_func(record2)

        assert key2 < key1

    def test_size_then_recency_with_same_size(self):
        """Test size_then_recency breaks ties by recency."""
        key_func = get_priority_key("size_then_recency")
        record1 = {"token_count": 50, "timestamp": 100}
        record2 = {"token_count": 50, "timestamp": 200}

        key1 = key_func(record1)
        key2 = key_func(record2)

        assert key2 < key1

    def test_unknown_policy_defaults_to_recency(self):
        """Test that unknown policy defaults to recency."""
        key_func = get_priority_key("unknown_policy")
        record = {"timestamp": 100}

        assert key_func(record) == (-100,)

    def test_missing_timestamp_field(self):
        """Test that missing timestamp defaults to 0."""
        key_func = get_priority_key("recency")
        record = {}

        assert key_func(record) == (0,)

    def test_missing_priority_field(self):
        """Test that missing priority defaults to 0."""
        key_func = get_priority_key("priority_then_recency")
        record = {"timestamp": 100}

        key = key_func(record)
        assert key == (0, -100)

    def test_missing_token_count_field(self):
        """Test that missing token_count defaults to 0."""
        key_func = get_priority_key("size_then_recency")
        record = {"timestamp": 100}

        key = key_func(record)
        assert key == (0, -100)


class TestOptimizeContextWindow:
    """Test suite for optimize_context_window function."""

    def test_empty_records_list(self):
        """Test with empty records list."""
        result = optimize_context_window([], max_tokens=1000)
        assert result == []

    def test_all_records_fit_within_budget(self):
        """Test when all records fit within token budget."""
        records = [
            {"content": "msg1", "timestamp": 1, "token_count": 10},
            {"content": "msg2", "timestamp": 2, "token_count": 15},
            {"content": "msg3", "timestamp": 3, "token_count": 20},
        ]

        result = optimize_context_window(records, max_tokens=100)
        assert len(result) == 3
        assert sum(r["token_count"] for r in result) == 45

    def test_records_exceed_budget(self):
        """Test when records exceed token budget."""
        records = [
            {"content": "msg1", "timestamp": 1, "token_count": 30},
            {"content": "msg2", "timestamp": 2, "token_count": 40},
            {"content": "msg3", "timestamp": 3, "token_count": 50},
        ]

        result = optimize_context_window(records, max_tokens=80, policy="recency")
        assert len(result) < 3
        assert sum(r["token_count"] for r in result) <= 80

    def test_recency_policy_keeps_most_recent(self):
        """Test that recency policy keeps the most recent messages."""
        records = [
            {"content": "old", "timestamp": 1, "token_count": 20},
            {"content": "recent", "timestamp": 3, "token_count": 20},
            {"content": "middle", "timestamp": 2, "token_count": 20},
        ]

        result = optimize_context_window(records, max_tokens=50, policy="recency")
        timestamps = [r["timestamp"] for r in result]

        assert 3 in timestamps
        assert len(result) == 2

    def test_priority_policy(self):
        """Test priority_then_recency policy."""
        records = [
            {"content": "low", "timestamp": 3, "priority": 1, "token_count": 20},
            {"content": "high", "timestamp": 1, "priority": 10, "token_count": 20},
            {"content": "medium", "timestamp": 2, "priority": 5, "token_count": 20},
        ]

        result = optimize_context_window(records, max_tokens=50, policy="priority_then_recency")

        priorities = [r["priority"] for r in result]
        assert 10 in priorities
        assert len(result) == 2

    def test_size_policy(self):
        """Test size_then_recency policy."""
        records = [
            {"content": "small", "timestamp": 3, "token_count": 10},
            {"content": "large", "timestamp": 1, "token_count": 50},
            {"content": "medium", "timestamp": 2, "token_count": 30},
        ]

        result = optimize_context_window(records, max_tokens=70, policy="size_then_recency")

        token_counts = [r["token_count"] for r in result]
        assert 50 in token_counts

    def test_records_without_token_count(self):
        """Test that token_count is calculated for records without it."""
        records = [
            {"role": "user", "content": "Hello", "timestamp": 1},
            {"role": "assistant", "content": "Hi there", "timestamp": 2},
        ]

        result = optimize_context_window(records, max_tokens=1000)

        assert all("token_count" in r for r in result)
        assert all(r["token_count"] > 0 for r in result)

    def test_single_record_exceeds_budget(self):
        """Test handling of individual record exceeding max_tokens."""
        records = [
            {"content": "huge message", "timestamp": 1, "token_count": 200},
            {"content": "small", "timestamp": 2, "token_count": 10},
        ]

        result = optimize_context_window(records, max_tokens=50, policy="recency")

        assert len(result) == 1
        assert result[0]["content"] == "small"

    def test_all_records_exceed_budget(self):
        """Test when all individual records exceed budget."""
        records = [
            {"content": "huge1", "timestamp": 1, "token_count": 200},
            {"content": "huge2", "timestamp": 2, "token_count": 300},
        ]

        result = optimize_context_window(records, max_tokens=50)
        assert len(result) == 0

    def test_result_sorted_by_timestamp(self):
        """Test that result is sorted by timestamp."""
        records = [
            {"content": "msg3", "timestamp": 3, "token_count": 10},
            {"content": "msg1", "timestamp": 1, "token_count": 10},
            {"content": "msg2", "timestamp": 2, "token_count": 10},
        ]

        result = optimize_context_window(records, max_tokens=100)
        timestamps = [r["timestamp"] for r in result]

        assert timestamps == sorted(timestamps)

    def test_exact_budget_match(self):
        """Test when records exactly match the budget."""
        records = [
            {"content": "msg1", "timestamp": 1, "token_count": 25},
            {"content": "msg2", "timestamp": 2, "token_count": 25},
            {"content": "msg3", "timestamp": 3, "token_count": 25},
            {"content": "msg4", "timestamp": 4, "token_count": 25},
        ]

        result = optimize_context_window(records, max_tokens=100)
        assert len(result) == 4
        assert sum(r["token_count"] for r in result) == 100

    def test_invalid_max_tokens_zero(self):
        """Test with max_tokens of zero."""
        records = [{"content": "test", "timestamp": 1, "token_count": 10}]

        with pytest.raises(ValueError, match="max_context_tokens must be positive"):
            optimize_context_window(records, max_tokens=0)

    def test_invalid_max_tokens_negative(self):
        """Test with negative max_tokens."""
        records = [{"content": "test", "timestamp": 1, "token_count": 10}]

        with pytest.raises(ValueError, match="max_context_tokens must be positive"):
            optimize_context_window(records, max_tokens=-100)

    def test_token_count_persistence(self):
        """Test that calculated token_count is persisted in records."""
        records = [
            {"role": "user", "content": "Test", "timestamp": 1},
        ]

        result = optimize_context_window(records, max_tokens=1000)

        assert "token_count" in records[0]
        assert records[0]["token_count"] == result[0]["token_count"]

    def test_mixed_records_with_and_without_token_count(self):
        """Test with some records having token_count and others not."""
        records = [
            {"content": "msg1", "timestamp": 1, "token_count": 20},
            {"role": "user", "content": "msg2", "timestamp": 2},
            {"content": "msg3", "timestamp": 3, "token_count": 15},
        ]

        result = optimize_context_window(records, max_tokens=100)

        assert all("token_count" in r for r in result)
        assert all("token_count" in r for r in records)
