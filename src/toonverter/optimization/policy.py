from dataclasses import dataclass, field
from enum import Enum


class PriorityLevel(Enum):
    CRITICAL = 1.0  # Never drop (e.g., ID, primary keys)
    HIGH = 0.8  # Compress last
    NORMAL = 0.5  # Standard data
    LOW = 0.2  # Logs, debug info
    TRIVIAL = 0.0  # Drop first


@dataclass
class OptimizationPolicy:
    """
    Configuration for the Context Optimizer.
    """

    # Key names that are considered CRITICAL (case-insensitive)
    critical_keys: set[str] = field(default_factory=lambda: {"id", "uuid", "guid", "_id", "pk"})

    # Key names that are LOW priority
    low_priority_keys: set[str] = field(
        default_factory=lambda: {"log", "debug", "trace", "history", "comments"}
    )

    # Max length for strings before truncation (0 = no limit)
    max_string_length: int = 500

    # Precision for floats (None = no change)
    float_precision: int | None = 2

    def get_priority(self, key: str, depth: int) -> float:
        """Calculate priority score for a given key/context."""
        key_lower = key.lower()

        if key_lower in self.critical_keys:
            return PriorityLevel.CRITICAL.value
        if key_lower in self.low_priority_keys:
            return PriorityLevel.LOW.value

        # Depth penalty: Deeper nodes are slightly less important
        depth_penalty = min(0.1, depth * 0.01)
        return max(0.1, PriorityLevel.NORMAL.value - depth_penalty)
