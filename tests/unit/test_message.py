import time

import pytest

from toonverter.core.message import Message, MessageRole


class TestMessageCreation:
    """Test suite for Message creation."""

    def test_message_creation_with_required_fields(self):
        """Test creating a message with only required fields."""
        msg = Message(role="user", content="Hello")

        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg.timestamp, float)
        assert msg.priority == 5
        assert msg.token_count > 0

    def test_message_creation_with_all_fields(self):
        """Test creating a message with all fields."""
        timestamp = time.time()
        msg = Message(role="assistant", content="Hello back", timestamp=timestamp, priority=8)

        assert msg.role == "assistant"
        assert msg.content == "Hello back"
        assert msg.timestamp == timestamp
        assert msg.priority == 8
        assert msg.token_count > 0

    def test_message_creation_user_role(self):
        """Test creating a message with user role."""
        msg = Message(role="user", content="Test")
        assert msg.role == "user"

    def test_message_creation_assistant_role(self):
        """Test creating a message with assistant role."""
        msg = Message(role="assistant", content="Test")
        assert msg.role == "assistant"

    def test_message_creation_system_role(self):
        """Test creating a message with system role."""
        msg = Message(role="system", content="Test")
        assert msg.role == "system"

    def test_message_creation_tool_role(self):
        """Test creating a message with tool role."""
        msg = Message(role="tool", content="Test")
        assert msg.role == "tool"

    def test_message_with_empty_content(self):
        """Test creating a message with empty content."""
        msg = Message(role="user", content="")
        assert msg.content == ""
        assert msg.token_count >= 0

    def test_message_with_long_content(self):
        """Test creating a message with long content."""
        long_content = "word " * 1000
        msg = Message(role="user", content=long_content)
        assert msg.content == long_content
        assert msg.token_count > 100

    def test_message_with_special_characters(self):
        """Test creating a message with special characters."""
        content = "Hello! @#$%^&*() 你好 😊"
        msg = Message(role="user", content=content)
        assert msg.content == content
        assert msg.token_count > 0

    def test_message_with_zero_priority(self):
        """Test creating a message with priority 0."""
        msg = Message(role="user", content="Test", priority=0)
        assert msg.priority == 0

    def test_message_with_high_priority(self):
        """Test creating a message with high priority."""
        msg = Message(role="user", content="Test", priority=100)
        assert msg.priority == 100

    def test_message_with_negative_priority(self):
        """Test creating a message with negative priority."""
        msg = Message(role="user", content="Test", priority=-5)
        assert msg.priority == -5

    def test_message_timestamp_auto_generated(self):
        """Test that timestamp is auto-generated if not provided."""
        before = time.time()
        msg = Message(role="user", content="Test")
        after = time.time()

        assert before <= msg.timestamp <= after

    def test_message_timestamp_custom(self):
        """Test setting custom timestamp."""
        custom_time = 1234567890.5
        msg = Message(role="user", content="Test", timestamp=custom_time)
        assert msg.timestamp == custom_time


class TestMessageImmutability:
    """Test suite for Message immutability."""

    def test_message_role_immutable(self):
        """Test that role cannot be changed."""
        msg = Message(role="user", content="Test")

        with pytest.raises((AttributeError, TypeError)):
            msg.role = "assistant"

    def test_message_content_immutable(self):
        """Test that content cannot be changed."""
        msg = Message(role="user", content="Test")

        with pytest.raises((AttributeError, TypeError)):
            msg.content = "Changed"

    def test_message_timestamp_immutable(self):
        """Test that timestamp cannot be changed."""
        msg = Message(role="user", content="Test")

        with pytest.raises((AttributeError, TypeError)):
            msg.timestamp = 999.999

    def test_message_priority_immutable(self):
        """Test that priority cannot be changed."""
        msg = Message(role="user", content="Test")

        with pytest.raises((AttributeError, TypeError)):
            msg.priority = 10

    def test_message_token_count_immutable(self):
        """Test that token_count cannot be changed."""
        msg = Message(role="user", content="Test")

        with pytest.raises((AttributeError, TypeError)):
            msg.token_count = 999


class TestMessageTokenCount:
    """Test suite for Message token count calculation."""

    def test_token_count_automatically_calculated(self):
        """Test that token_count is automatically calculated."""
        msg = Message(role="user", content="Test")
        assert msg.token_count > 0

    def test_token_count_increases_with_content_length(self):
        """Test that longer content has higher token count."""
        msg1 = Message(role="user", content="Short")
        msg2 = Message(role="user", content="This is a much longer message with more tokens")

        assert msg2.token_count > msg1.token_count

    def test_token_count_consistent_for_same_content(self):
        """Test that token count is consistent for same content."""
        msg1 = Message(role="user", content="Test message")
        msg2 = Message(role="user", content="Test message")

        assert msg1.token_count == msg2.token_count

    def test_token_count_with_empty_content(self):
        """Test token count with empty content."""
        msg = Message(role="user", content="")
        assert msg.token_count >= 0

    def test_token_count_includes_role(self):
        """Test that token count accounts for role."""
        msg = Message(role="user", content="Test")
        assert msg.token_count > 0


class TestMessageToDict:
    """Test suite for Message.to_dict() method."""

    def test_to_dict_includes_all_fields(self):
        """Test that to_dict includes all fields."""
        timestamp = time.time()
        msg = Message(role="user", content="Test", timestamp=timestamp, priority=7)

        result = msg.to_dict()

        assert "role" in result
        assert "content" in result
        assert "timestamp" in result
        assert "priority" in result
        assert "token_count" in result

    def test_to_dict_correct_values(self):
        """Test that to_dict returns correct values."""
        timestamp = 1234567890.5
        msg = Message(role="assistant", content="Hello", timestamp=timestamp, priority=9)

        result = msg.to_dict()

        assert result["role"] == "assistant"
        assert result["content"] == "Hello"
        assert result["timestamp"] == timestamp
        assert result["priority"] == 9
        assert result["token_count"] == msg.token_count

    def test_to_dict_returns_new_dict(self):
        """Test that to_dict returns a new dictionary."""
        msg = Message(role="user", content="Test")

        dict1 = msg.to_dict()
        dict2 = msg.to_dict()

        assert dict1 is not dict2
        assert dict1 == dict2

    def test_to_dict_with_special_characters(self):
        """Test to_dict with special characters in content."""
        msg = Message(role="user", content="Test 你好 😊")
        result = msg.to_dict()

        assert result["content"] == "Test 你好 😊"


class TestMessageToApiPayload:
    """Test suite for Message.to_api_payload() method."""

    def test_to_api_payload_only_role_and_content(self):
        """Test that to_api_payload only includes role and content."""
        msg = Message(role="user", content="API test", timestamp=123.456, priority=7)

        result = msg.to_api_payload()

        assert "role" in result
        assert "content" in result
        assert "timestamp" not in result
        assert "priority" not in result
        assert "token_count" not in result
        assert len(result) == 2

    def test_to_api_payload_correct_values(self):
        """Test that to_api_payload returns correct values."""
        msg = Message(role="assistant", content="Response")
        result = msg.to_api_payload()

        assert result == {"role": "assistant", "content": "Response"}

    def test_to_api_payload_with_system_role(self):
        """Test to_api_payload with system role."""
        msg = Message(role="system", content="System prompt")
        result = msg.to_api_payload()

        assert result == {"role": "system", "content": "System prompt"}

    def test_to_api_payload_with_tool_role(self):
        """Test to_api_payload with tool role."""
        msg = Message(role="tool", content="Tool output")
        result = msg.to_api_payload()

        assert result == {"role": "tool", "content": "Tool output"}


class TestMessageFromDict:
    """Test suite for Message.from_dict() factory method."""

    def test_from_dict_minimal_data(self):
        """Test creating message from dictionary with minimal data."""
        data = {"role": "user", "content": "From dict"}
        msg = Message.from_dict(data)

        assert msg.role == "user"
        assert msg.content == "From dict"
        assert isinstance(msg.timestamp, float)
        assert msg.priority == 5

    def test_from_dict_complete_data(self):
        """Test creating message from dictionary with all data."""
        data = {
            "role": "assistant",
            "content": "Complete data",
            "timestamp": 999.999,
            "priority": 3,
        }
        msg = Message.from_dict(data)

        assert msg.role == "assistant"
        assert msg.content == "Complete data"
        assert msg.timestamp == 999.999
        assert msg.priority == 3

    def test_from_dict_with_extra_fields(self):
        """Test from_dict ignores extra fields."""
        data = {"role": "user", "content": "Test", "extra_field": "ignored"}
        msg = Message.from_dict(data)

        assert msg.role == "user"
        assert msg.content == "Test"

    def test_from_dict_missing_role(self):
        """Test error handling when role is missing."""
        data = {"content": "No role"}

        with pytest.raises(KeyError, match="role"):
            Message.from_dict(data)

    def test_from_dict_missing_content(self):
        """Test error handling when content is missing."""
        data = {"role": "user"}

        with pytest.raises(KeyError, match="content"):
            Message.from_dict(data)

    def test_from_dict_missing_both_required_fields(self):
        """Test error handling when both required fields are missing."""
        data = {"timestamp": 123.456}

        with pytest.raises(KeyError):
            Message.from_dict(data)

    def test_from_dict_invalid_role(self):
        """Test error handling for invalid role."""
        data = {"role": "invalid_role", "content": "Test"}

        with pytest.raises(ValueError, match="Invalid role"):
            Message.from_dict(data)

    def test_from_dict_empty_role(self):
        """Test error handling for empty role string."""
        data = {"role": "", "content": "Test"}

        with pytest.raises(ValueError, match="Invalid role"):
            Message.from_dict(data)

    def test_from_dict_with_token_count_ignored(self):
        """Test that token_count in dict is ignored and recalculated."""
        data = {"role": "user", "content": "Test", "token_count": 9999}
        msg = Message.from_dict(data)

        assert msg.token_count != 9999

    def test_from_dict_all_valid_roles(self):
        """Test that all valid MessageRole values work."""
        roles: list[MessageRole] = ["user", "assistant", "system", "tool"]

        for role in roles:
            data = {"role": role, "content": "Test"}
            msg = Message.from_dict(data)
            assert msg.role == role

    def test_from_dict_with_zero_timestamp(self):
        """Test from_dict with timestamp of 0."""
        data = {"role": "user", "content": "Test", "timestamp": 0}
        msg = Message.from_dict(data)

        assert msg.timestamp == 0

    def test_from_dict_with_negative_priority(self):
        """Test from_dict with negative priority."""
        data = {"role": "user", "content": "Test", "priority": -5}
        msg = Message.from_dict(data)

        assert msg.priority == -5


class TestMessageRoundTrip:
    """Test suite for round-trip conversions."""

    def test_to_dict_from_dict_roundtrip(self):
        """Test that to_dict -> from_dict preserves data."""
        original = Message(
            role="user", content="Roundtrip test", timestamp=1234567890.5, priority=7
        )

        dict_form = original.to_dict()
        restored = Message.from_dict(dict_form)

        assert restored.role == original.role
        assert restored.content == original.content
        assert restored.timestamp == original.timestamp
        assert restored.priority == original.priority

    def test_multiple_messages_conversion(self):
        """Test converting multiple messages to and from dict."""
        messages = [
            Message(role="user", content="First", timestamp=1),
            Message(role="assistant", content="Second", timestamp=2),
            Message(role="user", content="Third", timestamp=3),
        ]

        dicts = [msg.to_dict() for msg in messages]
        restored = [Message.from_dict(d) for d in dicts]

        for original, restored_msg in zip(messages, restored, strict=True):
            assert original.role == restored_msg.role
            assert original.content == restored_msg.content
            assert original.timestamp == restored_msg.timestamp
