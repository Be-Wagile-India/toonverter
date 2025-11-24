"""Data models for ToonDiff."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChangeType(str, Enum):
    """Type of change detected."""

    ADD = "add"
    REMOVE = "remove"
    CHANGE = "change"
    TYPE_CHANGE = "type_change"


@dataclass
class DiffChange:
    """Represents a single difference between two data structures.

    Attributes:
        path: The JSON path to the difference (e.g., "users[0].name")
        type: The type of change (add, remove, change, type_change)
        old_value: The value in the original object (if applicable)
        new_value: The value in the new object (if applicable)
    """

    path: str
    type: ChangeType
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "path": self.path,
            "type": self.type.value,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class DiffResult:
    """Result of a diff operation.

    Attributes:
        changes: List of changes detected
        match: True if no changes found
    """

    changes: list[DiffChange] = field(default_factory=list)

    @property
    def match(self) -> bool:
        """Check if objects match."""
        return len(self.changes) == 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "match": self.match,
            "changes": [c.to_dict() for c in self.changes],
        }
