import time
from dataclasses import dataclass, field
from typing import Any, Literal

from toonverter.utils.context_helpers import count_tokens


MessageRole = Literal["user", "assistant", "system", "tool"]
ContextHistory = list["Message"]


@dataclass(slots=True, frozen=True)
class Message:
    """
    An immutable data model representing a single message turn in a conversation.
    Includes content, role, optimization metadata, and pre-calculated token count.

    Attributes:
        role: The speaker of the message (e.g., 'user', 'assistant').
        content: The text content of the message.
        timestamp: UNIX timestamp of when the message was created.
        priority: A numerical rank for context optimization (higher is more important).
        token_count: The calculated number of tokens consumed by this message.
    """

    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    priority: int = 5
    token_count: int = field(init=False, repr=True)

    def __post_init__(self):
        """Calculates token count after initialization."""
        core_data = {"role": self.role, "content": self.content}
        calculated_tokens = count_tokens(core_data)
        object.__setattr__(self, "token_count", calculated_tokens)

    def to_dict(self) -> dict[str, Any]:
        """
        Returns a complete dictionary representation including all metadata,
        suitable for persistence.
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "priority": self.priority,
            "token_count": self.token_count,
        }

    def to_api_payload(self) -> dict[str, str]:
        """
        Returns the simplified dictionary required for submission to most
        Generative AI APIs. Only includes 'role' and 'content'.
        """
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """
        Factory method to create a Message instance from a dictionary.

        Args:
            data: Dictionary containing message data.

        Returns:
            A new Message instance.

        Raises:
            KeyError: If required keys ('role', 'content') are missing.
            ValueError: If role is not a valid MessageRole.
        """
        if "role" not in data or "content" not in data:
            msg = "Message dictionary must contain 'role' and 'content' keys."
            raise KeyError(msg)

        role = data["role"]
        valid_roles = {"user", "assistant", "system", "tool"}
        if role not in valid_roles:
            msg = f"Invalid role '{role}'. Must be one of {valid_roles}"
            raise ValueError(msg)

        return cls(
            role=role,
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            priority=data.get("priority", 5),
        )
