import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from toonverter.core.types import ContextPolicyType


try:
    import tiktoken

    _ENCODER = tiktoken.get_encoding("cl100k_base")
except ImportError:
    logging.warning(
        "tiktoken not found. Using character count as an approximate fallback. "
        "Install tiktoken for accurate token counting."
    )
    _ENCODER = None

logger = logging.getLogger(__name__)


def _count_tokens_tiktoken(text: str) -> int:
    """Counts tokens using the cached tiktoken encoder."""
    if _ENCODER:
        return len(_ENCODER.encode(text))
    return len(text) // 4


def count_tokens(data: Any) -> int:
    """
    Calculates the token count for a Python object by serializing it
    to compact JSON, or counts tokens for an already serialized string.

    Args:
        data: The Python object (e.g., dict, list) or string to count tokens for.

    Returns:
        The estimated token count as an integer.
    """
    if isinstance(data, str):
        text_to_count = data
    else:
        try:
            text_to_count = json.dumps(data, separators=(",", ":"), sort_keys=True)
        except Exception:
            logger.exception("Failed to serialize data for token counting")
            return 0

    return _count_tokens_tiktoken(text_to_count)


def get_priority_key(
    policy: ContextPolicyType,
) -> Callable[[Any], tuple[int | float, ...]]:
    """
    Returns a key function for sorting context records based on the policy.

    Returns:
        A function that returns a tuple for consistent sorting behavior.
    """
    # Updated logic to handle Enum comparisons or strings

    # Fix PLR1714: Merge multiple comparisons into set membership check
    if policy in {ContextPolicyType.RECENCY, "recency"}:
        # Access via .get() handles both Dicts and Objects (if they implement get)
        # For mixed compatibility, we assume dict-like access or getattr
        return lambda record: (-record.get("timestamp", 0),)

    if policy in {ContextPolicyType.PRIORITY_THEN_RECENCY, "priority_then_recency"}:
        return lambda record: (-record.get("priority", 0), -record.get("timestamp", 0))

    if policy in {ContextPolicyType.SIZE_THEN_RECENCY, "size_then_recency"}:
        return lambda record: (-record.get("token_count", 0), -record.get("timestamp", 0))

    # Handling generic/long conversation policies by mapping them to logic
    if policy in {ContextPolicyType.LONG_CONVERSATION, ContextPolicyType.MULTI_AGENT}:
        # These prioritize 'priority' score first
        return lambda record: (-record.get("priority", 0), -record.get("timestamp", 0))

    logger.warning("Unknown policy '%s', defaulting to 'recency'", policy)
    return lambda record: (-record.get("timestamp", 0),)


T = TypeVar("T", bound=dict)  # Bound to dict because context_formatter passes dicts


def optimize_context_window(
    context_records: list[T],
    max_tokens: int,
    policy: ContextPolicyType = ContextPolicyType.RECENCY,
) -> list[T]:
    """
    Trims the list of context records to fit within max_tokens budget,
    using the specified prioritization policy.

    Args:
        context_records: A list of context items (Dictionaries).
        max_tokens: The maximum allowable token budget.
        policy: The strategy for prioritization.

    Returns:
        A list of records that fit within the token budget, sorted by timestamp.

    Raises:
        ValueError: If max_tokens is not positive.
    """
    if max_tokens <= 0:
        msg = f"max_context_tokens must be positive, got {max_tokens}"
        raise ValueError(msg)

    if not context_records:
        return []

    sort_key = get_priority_key(policy)

    # Ensure tokens are counted
    for record in context_records:
        if "token_count" not in record:
            record["token_count"] = count_tokens(record)

    sorted_records = sorted(context_records, key=sort_key)

    current_token_sum = 0
    optimized_context: list[T] = []

    for record in sorted_records:
        record_tokens = record["token_count"]

        if record_tokens > max_tokens:
            logger.warning(
                "Record with timestamp %s (%s tokens) exceeds max_tokens (%s), skipping",
                record.get("timestamp", "unknown"),
                record_tokens,
                max_tokens,
            )
            continue

        if current_token_sum + record_tokens <= max_tokens:
            optimized_context.append(record)
            current_token_sum += record_tokens
        else:
            break

    # Sort back by timestamp (chronological) for the final context window
    return sorted(optimized_context, key=lambda r: r.get("timestamp", 0))
