import json

import pytest

from toonverter.core.context_formatter import ContextConverter
from toonverter.core.message import Message


class TestContextConverterInitialization:
    """Test suite for ContextConverter initialization."""

    def test_initialization_with_defaults(self):
        """Test ContextConverter initialization with default values."""
        converter = ContextConverter(max_context_tokens=1000)

        assert converter.max_context_tokens == 1000
        assert converter.context_policy == "priority_then_recency"
        assert converter.reserved_tokens == 100
        assert converter.history_budget == 900
        assert converter.system_prompt == ContextConverter.DEFAULT_SYSTEM_PROMPT

    def test_initialization_with_custom_values(self):
        """Test ContextConverter initialization with custom values."""
        converter = ContextConverter(
            max_context_tokens=2000,
            context_policy="recency",
            reserved_tokens=200,
            system_prompt="Custom prompt",
        )

        assert converter.max_context_tokens == 2000
        assert converter.context_policy == "recency"
        assert converter.reserved_tokens == 200
        assert converter.history_budget == 1800
        assert converter.system_prompt == "Custom prompt"

    def test_initialization_with_size_policy(self):
        """Test initialization with size_then_recency policy."""
        converter = ContextConverter(max_context_tokens=1000, context_policy="size_then_recency")

        assert converter.context_policy == "size_then_recency"

    def test_initialization_minimal_budget(self):
        """Test initialization with minimal token budget."""
        converter = ContextConverter(max_context_tokens=150, reserved_tokens=50)

        assert converter.history_budget == 100

    def test_initialization_large_budget(self):
        """Test initialization with large token budget."""
        converter = ContextConverter(max_context_tokens=100000)

        assert converter.history_budget == 99900

    def test_initialization_custom_system_prompt(self):
        """Test initialization with custom system prompt."""
        custom_prompt = "You are a specialized AI assistant for coding."
        converter = ContextConverter(max_context_tokens=1000, system_prompt=custom_prompt)

        assert converter.system_prompt == custom_prompt

    def test_initialization_empty_system_prompt(self):
        """Test initialization with empty system prompt."""
        converter = ContextConverter(max_context_tokens=1000, system_prompt="")

        assert converter.system_prompt == ""

    def test_initialization_none_system_prompt_uses_default(self):
        """Test that None system_prompt uses default."""
        converter = ContextConverter(max_context_tokens=1000, system_prompt=None)

        assert converter.system_prompt == ContextConverter.DEFAULT_SYSTEM_PROMPT


class TestContextConverterValidation:
    """Test suite for ContextConverter input validation."""

    def test_invalid_max_tokens_zero(self):
        """Test error handling for max_context_tokens of zero."""
        with pytest.raises(ValueError, match="max_context_tokens must be positive"):
            ContextConverter(max_context_tokens=0)

    def test_invalid_max_tokens_negative(self):
        """Test error handling for negative max_context_tokens."""
        with pytest.raises(ValueError, match="max_context_tokens must be positive"):
            ContextConverter(max_context_tokens=-100)

    def test_invalid_reserved_tokens_negative(self):
        """Test error handling for negative reserved_tokens."""
        with pytest.raises(ValueError, match="reserved_tokens cannot be negative"):
            ContextConverter(max_context_tokens=1000, reserved_tokens=-50)

    def test_reserved_equals_max(self):
        """Test error handling when reserved_tokens equals max_context_tokens."""
        with pytest.raises(ValueError, match=r"reserved_tokens.*must be less than"):
            ContextConverter(max_context_tokens=1000, reserved_tokens=1000)

    def test_reserved_exceeds_max(self):
        """Test error handling when reserved_tokens exceeds max_context_tokens."""
        with pytest.raises(ValueError, match=r"reserved_tokens.*must be less than"):
            ContextConverter(max_context_tokens=1000, reserved_tokens=1500)

    def test_reserved_tokens_zero_allowed(self):
        """Test that reserved_tokens of 0 is allowed."""
        converter = ContextConverter(max_context_tokens=1000, reserved_tokens=0)

        assert converter.reserved_tokens == 0
        assert converter.history_budget == 1000


class TestConvertHistoryToApiPayload:
    """Test suite for _convert_history_to_api_payload static method."""

    def test_convert_empty_history(self):
        """Test converting empty history."""
        result = ContextConverter._convert_history_to_api_payload([])
        assert result == []

    def test_convert_single_message(self):
        """Test converting single message."""
        messages = [Message(role="user", content="Hello")]
        result = ContextConverter._convert_history_to_api_payload(messages)

        assert len(result) == 1
        assert result[0] == {"role": "user", "content": "Hello"}

    def test_convert_multiple_messages(self):
        """Test converting multiple messages."""
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi there"),
            Message(role="user", content="How are you?"),
        ]

        result = ContextConverter._convert_history_to_api_payload(messages)

        assert len(result) == 3
        assert result[0] == {"role": "user", "content": "Hello"}
        assert result[1] == {"role": "assistant", "content": "Hi there"}
        assert result[2] == {"role": "user", "content": "How are you?"}

    def test_convert_removes_metadata(self):
        """Test that metadata is removed from converted messages."""
        messages = [Message(role="user", content="Test", timestamp=123.456, priority=10)]

        result = ContextConverter._convert_history_to_api_payload(messages)

        assert "timestamp" not in result[0]
        assert "priority" not in result[0]
        assert "token_count" not in result[0]

    def test_convert_all_role_types(self):
        """Test converting all message role types."""
        messages = [
            Message(role="user", content="User msg"),
            Message(role="assistant", content="Assistant msg"),
            Message(role="system", content="System msg"),
            Message(role="tool", content="Tool msg"),
        ]

        result = ContextConverter._convert_history_to_api_payload(messages)

        assert len(result) == 4
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"
        assert result[2]["role"] == "system"
        assert result[3]["role"] == "tool"


class TestGenerateToonPayload:
    """Test suite for generate_toon_payload method."""

    def test_generate_basic_payload(self):
        """Test basic TOON payload generation."""
        converter = ContextConverter(max_context_tokens=1000)

        history = [
            Message(role="user", content="Previous message"),
            Message(role="assistant", content="Previous response"),
        ]
        new_message = Message(role="user", content="New message")

        result = converter.generate_toon_payload(history, new_message)

        assert isinstance(result, str)
        payload = json.loads(result)

        assert "version" in payload
        assert "messages" in payload
        assert isinstance(payload["messages"], list)

    def test_generate_payload_with_empty_history(self):
        """Test payload generation with no conversation history."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="First message")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["content"] == "First message"

    def test_generate_payload_includes_system_prompt(self):
        """Test that system prompt is included as first message."""
        converter = ContextConverter(max_context_tokens=1000, system_prompt="Test system prompt")

        history = []
        new_message = Message(role="user", content="Hello")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][0]["content"] == "Test system prompt"

    def test_generate_payload_with_tool_outputs(self):
        """Test TOON payload generation with tool outputs."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Check weather")
        tool_outputs = [{"tool": "weather", "result": "sunny"}]

        result = converter.generate_toon_payload(history, new_message, tool_outputs)
        payload = json.loads(result)

        assert "tool_results" in payload
        assert payload["tool_results"] == tool_outputs

    def test_generate_payload_without_tool_outputs(self):
        """Test that tool_results is not included when no tools."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Hello")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert "tool_results" not in payload

    def test_generate_payload_with_multiple_tool_outputs(self):
        """Test with multiple tool outputs."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Test")
        tool_outputs = [
            {"tool": "weather", "result": "sunny"},
            {"tool": "time", "result": "12:00 PM"},
        ]

        result = converter.generate_toon_payload(history, new_message, tool_outputs)
        payload = json.loads(result)

        assert len(payload["tool_results"]) == 2

    def test_generate_payload_invalid_new_message_role(self):
        """Test error when new_message doesn't have 'user' role."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="assistant", content="Wrong role")

        with pytest.raises(ValueError, match="new_user_message must have role 'user'"):
            converter.generate_toon_payload(history, new_message)

    def test_generate_payload_system_role_error(self):
        """Test error when new_message has 'system' role."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="system", content="System message")

        with pytest.raises(ValueError, match="new_user_message must have role 'user'"):
            converter.generate_toon_payload(history, new_message)

    def test_generate_payload_tool_role_error(self):
        """Test error when new_message has 'tool' role."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="tool", content="Tool message")

        with pytest.raises(ValueError, match="new_user_message must have role 'user'"):
            converter.generate_toon_payload(history, new_message)


class TestPayloadOptimization:
    """Test suite for context optimization in payload generation."""

    def test_payload_optimizes_long_history(self):
        """Test that history is optimized when exceeding budget."""
        converter = ContextConverter(max_context_tokens=500, reserved_tokens=100)

        # Ensure history exceeds the 400 token budget (500 - 100).
        # Use a long string to guarantee high token count per message.
        long_text = "word " * 50
        history = [
            Message(role="user", content=f"Message {i} {long_text}", timestamp=i) for i in range(20)
        ]
        new_message = Message(role="user", content="Final message")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        # Assert that the resulting payload has fewer messages than the full set would
        # Full set: 20 history + 1 system + 1 user = 22
        # If optimization works, it should be significantly less than 22.
        assert len(payload["messages"]) < len(history) + 2

    def test_payload_keeps_all_when_within_budget(self):
        """Test that all messages kept when within budget."""
        converter = ContextConverter(max_context_tokens=10000)

        history = [Message(role="user", content=f"Message {i}", timestamp=i) for i in range(5)]
        new_message = Message(role="user", content="Final")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert len(payload["messages"]) == len(history) + 2

    def test_payload_uses_configured_policy(self):
        """Test that configured policy is used for optimization."""
        # Budget small enough to force trimming
        converter = ContextConverter(max_context_tokens=300, context_policy="recency")

        history = [
            Message(role="user", content="Old" * 20, timestamp=1),
            Message(role="assistant", content="Response" * 20, timestamp=2),
            Message(role="user", content="Recent" * 20, timestamp=3),
        ]
        new_message = Message(role="user", content="New")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert "messages" in payload

    def test_payload_with_priority_policy(self):
        """Test optimization with priority policy."""
        converter = ContextConverter(max_context_tokens=500, context_policy="priority_then_recency")

        history = [
            Message(role="user", content="Low priority" * 10, timestamp=1, priority=1),
            Message(role="user", content="High priority" * 10, timestamp=2, priority=10),
            Message(role="user", content="Medium priority" * 10, timestamp=3, priority=5),
        ]
        new_message = Message(role="user", content="New")

        result = converter.generate_toon_payload(history, new_message)
        assert json.loads(result)


class TestPayloadFormat:
    """Test suite for TOON payload format."""

    def test_payload_is_valid_json(self):
        """Test that output is valid JSON."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Test")

        result = converter.generate_toon_payload(history, new_message)

        payload = json.loads(result)
        assert isinstance(payload, dict)

    def test_payload_is_compact_json(self):
        """Test that output JSON is compact (no whitespace)."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Test")

        result = converter.generate_toon_payload(history, new_message)

        assert ", " not in result
        assert ": " not in result

    def test_payload_has_version_field(self):
        """Test that payload includes version field."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Test")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert "version" in payload
        assert payload["version"] == converter.TOON_VERSION

    def test_payload_has_messages_field(self):
        """Test that payload includes messages field."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []
        new_message = Message(role="user", content="Test")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert "messages" in payload
        assert isinstance(payload["messages"], list)

    def test_payload_messages_are_dicts(self):
        """Test that messages are dictionaries."""
        converter = ContextConverter(max_context_tokens=1000)

        history = [Message(role="user", content="Test")]
        new_message = Message(role="user", content="New")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        for msg in payload["messages"]:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg


class TestPayloadMessageOrder:
    """Test suite for message ordering in payload."""

    def test_payload_system_message_first(self):
        """Test that system message is always first."""
        converter = ContextConverter(max_context_tokens=1000)

        history = [
            Message(role="user", content="First"),
            Message(role="assistant", content="Second"),
        ]
        new_message = Message(role="user", content="Third")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert payload["messages"][0]["role"] == "system"

    def test_payload_preserves_conversation_order(self):
        """Test that conversation order is preserved."""
        converter = ContextConverter(max_context_tokens=2000)

        history = [
            Message(role="user", content="First", timestamp=1),
            Message(role="assistant", content="Second", timestamp=2),
            Message(role="user", content="Third", timestamp=3),
        ]
        new_message = Message(role="user", content="Fourth")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        messages = payload["messages"][1:]
        contents = [m["content"] for m in messages]

        assert "First" in contents
        assert "Fourth" in contents

    def test_payload_new_message_is_last(self):
        """Test that new message appears at the end."""
        converter = ContextConverter(max_context_tokens=2000)

        history = [
            Message(role="user", content="Old1"),
            Message(role="assistant", content="Old2"),
        ]
        new_message = Message(role="user", content="NewMessage")

        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert payload["messages"][-1]["content"] == "NewMessage"


class TestIntegration:
    """Integration tests for ContextConverter."""

    def test_full_conversation_workflow(self):
        """Test a complete conversation workflow."""
        converter = ContextConverter(max_context_tokens=1000)

        history = []

        msg1 = Message(role="user", content="What is Python?")
        payload1 = converter.generate_toon_payload(history, msg1)
        assert json.loads(payload1)

        history.append(msg1)
        history.append(Message(role="assistant", content="Python is a programming language."))

        msg2 = Message(role="user", content="Tell me more")
        payload2 = converter.generate_toon_payload(history, msg2)
        payload_dict = json.loads(payload2)

        assert len(payload_dict["messages"]) >= 4

    def test_multi_turn_conversation_with_optimization(self):
        """Test multi-turn conversation with optimization."""
        converter = ContextConverter(max_context_tokens=500)

        history = []

        # Create significantly larger messages to ensure we hit the 400 token budget
        # "word " * 50 is roughly 50 tokens + overhead.
        # 20 messages * 50 tokens = 1000 tokens >> 400 budget.
        long_content_suffix = " word" * 50

        for i in range(10):
            user_msg = Message(role="user", content=f"Question {i}{long_content_suffix}")
            assistant_msg = Message(role="assistant", content=f"Answer {i}{long_content_suffix}")
            history.extend([user_msg, assistant_msg])

        new_message = Message(role="user", content="Final question")
        result = converter.generate_toon_payload(history, new_message)
        payload = json.loads(result)

        assert "messages" in payload
        # Ensure the history was actually trimmed
        assert len(payload["messages"]) < len(history) + 2
