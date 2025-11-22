import json
import logging
from typing import Any

from toonverter.core.message import ContextHistory, Message
from toonverter.core.spec import TOON_SPEC_URL, TOON_SPEC_VERSION
from toonverter.utils.context_helpers import ContextPolicyType, optimize_context_window


logger = logging.getLogger(__name__)


class ContextConverter:
    """
    Manages the conversion of an arbitrary-length conversation history
    into a token-optimized, structured TOON format payload ready for LLM submission.

    The TOON format is a compact JSON structure designed for maximum context
    delivery within a limited token window.
    """

    TOON_VERSION: str = TOON_SPEC_VERSION
    TOON_SPEC_URL: str = TOON_SPEC_URL
    DEFAULT_SYSTEM_PROMPT: str = "You are a helpful and concise AI assistant."

    def __init__(
        self,
        max_context_tokens: int,
        context_policy: ContextPolicyType = ContextPolicyType.PRIORITY_THEN_RECENCY,
        reserved_tokens: int = 100,
        system_prompt: str | None = None,
    ) -> None:
        """
        Initializes the converter with core configuration parameters.

        Args:
            max_context_tokens: The absolute token limit imposed by the target LLM.
            context_policy: The strategy for trimming history.
            reserved_tokens: Tokens reserved for final user prompt and system message (default: 100).
            system_prompt: Global instruction to prepend to the conversation.

        Raises:
            ValueError: If max_context_tokens or reserved_tokens are invalid.
        """
        if max_context_tokens <= 0:
            msg = f"max_context_tokens must be positive, got {max_context_tokens}"
            raise ValueError(msg)

        if reserved_tokens < 0:
            msg = f"reserved_tokens cannot be negative, got {reserved_tokens}"
            raise ValueError(msg)

        if reserved_tokens >= max_context_tokens:
            msg = (
                f"reserved_tokens ({reserved_tokens}) must be less than "
                f"max_context_tokens ({max_context_tokens})"
            )
            raise ValueError(msg)

        self.max_context_tokens: int = max_context_tokens
        self.context_policy: ContextPolicyType = context_policy
        self.reserved_tokens: int = reserved_tokens
        self.system_prompt: str = (
            system_prompt if system_prompt is not None else self.DEFAULT_SYSTEM_PROMPT
        )

        self.history_budget: int = self.max_context_tokens - self.reserved_tokens

        logger.info(
            "ContextConverter initialized. Max tokens: %s, Reserved: %s, History budget: %s",
            self.max_context_tokens,
            self.reserved_tokens,
            self.history_budget,
        )

    @staticmethod
    def _convert_history_to_api_payload(history: ContextHistory) -> list[dict[str, str]]:
        """
        Converts Message objects into the simplified list-of-dicts format
        required for API payload structure.
        """
        return [message.to_api_payload() for message in history]

    def generate_toon_payload(
        self,
        conversation_history: ContextHistory,
        new_user_message: Message,
        tool_outputs: list[dict[str, Any]] | None = None,
    ) -> str:
        """
        Generates the final token-optimized TOON payload string.

        Args:
            conversation_history: Existing messages in the conversation (excluding new turn).
            new_user_message: The latest message from the user (always included).
            tool_outputs: Structured results from any pre-executed tools.

        Returns:
            The optimized, JSON-serialized TOON payload string.

        Raises:
            ValueError: If new_user_message role is not 'user'.
        """
        if new_user_message.role != "user":
            msg = f"new_user_message must have role 'user', got '{new_user_message.role}'"
            raise ValueError(msg)

        logger.debug(
            "Starting payload generation. Original history length: %s",
            len(conversation_history),
        )

        # Convert Messages to Dicts for the optimizer
        history_dicts: list[dict[str, Any]] = [m.to_dict() for m in conversation_history]

        # Optimize
        optimized_dicts: list[dict[str, Any]] = optimize_context_window(
            context_records=history_dicts,
            max_tokens=self.history_budget,
            policy=self.context_policy,
        )

        # Convert back to Message objects
        optimized_history: ContextHistory = [Message.from_dict(d) for d in optimized_dicts]

        logger.info(
            "Context optimization complete. %s/%s messages retained",
            len(optimized_history),
            len(conversation_history),
        )

        full_context: ContextHistory = [*optimized_history, new_user_message]

        system_message = Message(role="system", content=self.system_prompt)

        final_api_messages: list[dict[str, str]] = self._convert_history_to_api_payload(
            [system_message, *full_context]
        )

        toon_payload_dict: dict[str, Any] = {
            "version": self.TOON_VERSION,
            "messages": final_api_messages,
        }

        if tool_outputs:
            toon_payload_dict["tool_results"] = tool_outputs
            logger.debug("Including %s tool results in payload", len(tool_outputs))

        return json.dumps(toon_payload_dict, separators=(",", ":"), sort_keys=True)
