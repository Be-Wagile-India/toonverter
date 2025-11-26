from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """
    Represents a semantically meaningful chunk of data.

    Attributes:
        content: The actual text/data content of the chunk.
        path: The hierarchical path to this chunk (e.g., ["users", "0", "profile"]).
        metadata: Additional context (e.g., source filename, original keys).
        token_count: The estimated number of tokens in this chunk.
    """

    content: str
    path: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    token_count: int = 0

    @property
    def path_string(self) -> str:
        """Returns the path as a dot-notation string."""
        return ".".join(self.path)
