from typing import Any

import pytest

from toonverter.core.interfaces import FormatAdapter, TokenCounter
from toonverter.core.registry import registry
from toonverter.rag.chunking import ToonChunker


# --- Test Mocks/Fixtures (For predictable and reliable unit tests) ---


class DummyTokenCounter(TokenCounter):
    """Mock TokenCounter for predictable test behavior (using word count + 1)."""

    def __init__(self, model_name: str = "test") -> None:
        """Initialize the dummy counter."""
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        """Return the dummy model name."""
        return self._model_name

    def count_tokens(self, text: str) -> int:
        """Count tokens based on word count plus one (for simple, predictable testing)."""
        return max(1, len(text.split()) + 1) if text else 0

    def analyze(self, text: str, format_name: str) -> Any:
        """Analyze tokens (not implemented)."""
        return {}


@pytest.fixture(autouse=True)
def monkeypatch_token_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replaces the production TiktokenCounter with the predictable DummyTokenCounter."""
    monkeypatch.setattr("toonverter.rag.chunking.TiktokenCounter", DummyTokenCounter)


class DummyToonAdapter(FormatAdapter):
    """Mock FormatAdapter for predictable TOON encoding in tests."""

    @property
    def format_name(self) -> str:
        """Return the format name."""
        return "toon"

    def encode(self, data: Any, options: Any | None = None) -> str:
        """Encode data (used for token counting calculations)."""
        if isinstance(data, dict):
            items = "\n".join(f"  {k}: {v}" for k, v in data.items())
            return f"{items}"
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            header_keys = ",".join(data[0].keys())
            rows = "\n".join(f'  {item["id"]},"{item["text"]}"' for item in data)
            return f"[{len(data)}]{{{header_keys}}}:\n{rows}"

        return str(data)

    def decode(self, data_str: str, options: Any | None = None) -> Any:
        """Decode (not implemented)."""
        raise NotImplementedError

    def validate(self, data_str: str) -> bool:
        """Validate (not implemented)."""
        raise NotImplementedError


@pytest.fixture(scope="session", autouse=True)
def setup_dummy_registry() -> None:
    """Ensure a DummyToonAdapter is registered for the chunker to retrieve."""
    try:
        if not registry.is_supported("toon"):
            registry.register("toon", DummyToonAdapter())
    except Exception:
        pass


@pytest.fixture
def chunker_20() -> ToonChunker:
    """Returns a chunker with a tight limit of 20 tokens (max_tokens=20, context_tokens=2)."""
    return ToonChunker(max_tokens=20, context_tokens=2, model="gpt-4o")


@pytest.fixture
def data_list_items() -> list[dict[str, Any]]:
    """Data where items have varying token lengths."""
    return [
        {"id": 1, "text": "item one two"},
        {"id": 2, "text": "item three four five"},
        {
            "id": 3,
            "text": "item six seven eight nine is very long",
        },
        {"id": 4, "text": "item ten"},
    ]


@pytest.fixture
def data_complex() -> dict[str, Any]:
    """Data with nested dicts and a list for full testing."""
    return {
        "user_data": {"id": 101, "name": "Alice"},
        "settings": {
            "theme": "dark",
            "layout": "full",
            "font": "small",
        },
        "permissions": {
            "read": True,
            "write": False,
            "admin": False,
            "export": True,
        },
        "documents": [
            {"title": "Doc A", "len": 1},
            {"title": "Doc B", "len": 1},
        ],
    }


def get_tokens(chunker: ToonChunker, chunk: str) -> int:
    """Helper to get token count using the chunker's counter."""
    return chunker.counter.count_tokens(chunk)


# --- Test Cases ---


def test_chunker_initializes_with_correct_budget(chunker_20: ToonChunker) -> None:
    """Verify that the effective max tokens is set correctly."""
    assert chunker_20.max_tokens == 20
    assert chunker_20.effective_max_tokens == 18
    assert chunker_20._min_header_cost == 3
    assert chunker_20.effective_max_tokens - chunker_20._min_header_cost == 15


def test_single_object_fits_and_has_header(chunker_20: ToonChunker) -> None:
    """Test that a small object is not split and contains the contextual header."""
    data = {"key": "small value"}

    chunks = list(chunker_20.chunk(data))

    assert len(chunks) == 1
    assert "Context_Path: root" in chunks[0]
    assert get_tokens(chunker_20, chunks[0]) == 6
    assert get_tokens(chunker_20, chunks[0]) <= chunker_20.max_tokens


def test_dict_splits_into_batches_correctly(
    chunker_20: ToonChunker, data_complex: dict[str, Any]
) -> None:
    """Test that the dictionary keys are grouped into token-optimized batches."""

    chunks = list(chunker_20.chunk(data_complex))

    assert len(chunks) == 3

    # Chunk 1: Dictionary Batch 1 (user_data + settings)
    assert "Context_Path: root" in chunks[0]
    assert "user_data" in chunks[0]
    assert "settings" in chunks[0]
    assert "permissions" not in chunks[0]
    assert get_tokens(chunker_20, chunks[0]) == 15

    # Chunk 2: Dictionary Batch 2 (permissions)
    assert "Context_Path: root" in chunks[1]
    assert "permissions" in chunks[1]
    assert get_tokens(chunker_20, chunks[1]) == 12

    # Chunk 3: List Batch (documents)
    assert "Context_Path: root" in chunks[2]
    assert "documents" in chunks[2]
    # Final observed value: 8
    assert get_tokens(chunker_20, chunks[2]) == 8


def test_list_splits_by_index_path_and_batches(
    chunker_20: ToonChunker, data_list_items: list[dict[str, Any]]
) -> None:
    """Test that a list is batched based on token size, and the path reflects the indices."""

    list_chunks = list(
        chunker_20._chunk_list(
            data_list_items,
            chunker_20.effective_max_tokens - chunker_20._min_header_cost,
            "root.list_data",
        )
    )

    assert len(list_chunks) == 2

    # Chunk 1: First batch of the list (items 0 and 1)
    assert "Context_Path: root.list_data[0-1]" in list_chunks[0]
    assert get_tokens(chunker_20, list_chunks[0]) == 11

    # Chunk 2: Second batch of the list (items 2 and 3)
    assert "Context_Path: root.list_data[2-3]" in list_chunks[1]
    # Final observed value: 14
    assert get_tokens(chunker_20, list_chunks[1]) == 14

    for chunk in list_chunks:
        assert get_tokens(chunker_20, chunk) <= chunker_20.max_tokens


def test_oversized_single_list_item_triggers_recursion(chunker_20: ToonChunker) -> None:
    """Test that a single list item too large for the payload limit triggers recursion on the item."""

    giant_string = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z"

    data = [giant_string]

    chunks = list(chunker_20.chunk(data))

    assert len(chunks) == 1

    assert "Context_Path: root[0]" in chunks[0]
    assert get_tokens(chunker_20, chunks[0]) == 29
    assert get_tokens(chunker_20, chunks[0]) > chunker_20.max_tokens


def test_dict_item_too_large_triggers_recursion(chunker_20: ToonChunker) -> None:
    """Test that a single key-value pair too large for the batch limit triggers recursion on the value."""

    giant_string = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z"

    data = {
        "small": "s1 s2",
        "huge": giant_string,
    }

    chunks = list(chunker_20.chunk(data))

    assert len(chunks) == 2

    # Chunk 1: The batch that started with "small"
    assert "Context_Path: root" in chunks[0]
    assert "small" in chunks[0]
    assert get_tokens(chunker_20, chunks[0]) == 6

    # Chunk 2: The recursive chunk for the "huge" value.
    assert "Context_Path: root.huge" in chunks[1]
    assert get_tokens(chunker_20, chunks[1]) == 29
