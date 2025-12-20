"""Tests for semantic deduplication."""

from unittest.mock import patch

import pytest

from toonverter.analysis.deduplication import ExactDeduplicator, SemanticDeduplicator


def test_simple_deduplication():
    """Test deduplication of simple types."""
    data = [1, 2, 3, 2, 1, 4]
    deduplicator = ExactDeduplicator()
    result = deduplicator.process(data)

    assert result.unique_items == [1, 2, 3, 4]
    assert result.duplicate_count == 2
    assert result.reduction_percentage == (2 / 6) * 100

    # Check duplicate details (sorted by index)
    assert result.duplicates[0].duplicate_index == 3
    assert result.duplicates[0].item == 2
    assert result.duplicates[1].duplicate_index == 4
    assert result.duplicates[1].item == 1


def test_semantic_dict_equivalence():
    """Test that dicts with different key orders are treated as duplicates."""
    data = [
        {"a": 1, "b": 2},
        {"b": 2, "a": 1},  # Duplicate of first
        {"a": 1, "b": 3},  # Unique
    ]

    deduplicator = ExactDeduplicator()
    result = deduplicator.process(data)
    assert len(result.unique_items) == 2
    assert result.unique_items[0] == {"a": 1, "b": 2}
    assert result.unique_items[1] == {"a": 1, "b": 3}


def test_stream_processing():
    """Test streaming deduplication."""
    data = iter([1, 2, 1, 3, 2])
    deduplicator = ExactDeduplicator()

    unique_stream = deduplicator.stream_unique(data)
    result = list(unique_stream)

    assert result == [1, 2, 3]


# --- Tests for Advanced Semantic Mode ---


@pytest.fixture
def mock_sentence_transformer():
    # Patch the library directly since it is imported lazily
    with patch("sentence_transformers.SentenceTransformer") as mock_lib:
        yield mock_lib


@pytest.fixture
def mock_cosine_similarity():
    # Patch the library directly
    with patch("sklearn.metrics.pairwise.cosine_similarity") as mock_lib:
        yield mock_lib


def test_semantic_mode_fallback_if_missing_deps():
    """Test fallback to exact mode if modules missing."""
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        deduplicator = ExactDeduplicator(mode="semantic")
        # Trigger explicit lazy load
        deduplicator._init_model()
        assert deduplicator.mode == "exact"


def test_semantic_clustering(mock_sentence_transformer, mock_cosine_similarity):
    """Test that semantically similar items are deduplicated."""

    # Mock embeddings: 3 items.
    # Item 0 and 1 are similar. Item 2 is different.
    # We simulate this by mocking cosine_similarity matrix

    # Input Data: ["The cat sat", "A feline sat", "The dog ran"]
    data = ["The cat sat", "A feline sat", "The dog ran"]

    mock_model_instance = mock_sentence_transformer.return_value
    mock_model_instance.encode.return_value = [[1, 0], [0.99, 0.01], [0, 1]]  # Dummy embeddings

    # Matrix:
    #      0    1    2
    # 0: [1.0, 0.99, 0.0]
    # 1: [0.99, 1.0, 0.0]
    # 2: [0.0, 0.0, 1.0]
    mock_cosine_similarity.return_value = [[1.0, 0.99, 0.0], [0.99, 1.0, 0.0], [0.0, 0.0, 1.0]]

    deduplicator = ExactDeduplicator(mode="semantic", threshold=0.9)
    result = deduplicator.process(data)

    assert len(result.unique_items) == 2
    # Should keep first ("The cat sat") and third ("The dog ran")
    # "A feline sat" is removed as duplicate of "The cat sat"
    assert "The cat sat" in result.unique_items
    assert "The dog ran" in result.unique_items
    assert "A feline sat" not in result.unique_items
    assert result.duplicate_count == 1


def test_hybrid_processing(mock_sentence_transformer, mock_cosine_similarity):
    """Test that exact duplicates are removed first, then semantic."""

    # Data:
    # 0: "A"
    # 1: "A" (Exact duplicate)
    # 2: "B" (Semantically similar to A)
    # 3: "C" (Different)
    data = ["A", "A", "B", "C"]

    mock_model_instance = mock_sentence_transformer.return_value
    # Encode will be called only for unique candidates from exact phase: ["A", "B", "C"]
    mock_model_instance.encode.return_value = [[1], [0.95], [0]]

    # Sim matrix for A, B, C
    # A vs B = 0.95 (Dup)
    mock_cosine_similarity.return_value = [[1.0, 0.95, 0.0], [0.95, 1.0, 0.0], [0.0, 0.0, 1.0]]

    deduplicator = ExactDeduplicator(mode="semantic", threshold=0.9)
    result = deduplicator.process(data)

    # Expect:
    # "A" (idx 1) removed by Exact Dedup
    # "B" (idx 2) removed by Semantic Dedup (similar to "A")
    # Remaining: "A" (idx 0), "C" (idx 3)

    assert len(result.unique_items) == 2
    assert "A" in result.unique_items
    assert "C" in result.unique_items
    assert result.duplicate_count == 2


# --- Tests for SemanticDeduplicator ---


def test_semantic_deduplicator_list_deduplication(
    mock_sentence_transformer, mock_cosine_similarity
):
    """Test SemanticDeduplicator on a simple list."""
    data = ["item1", "item1_similar", "item2"]

    mock_model_instance = mock_sentence_transformer.return_value
    mock_model_instance.encode.return_value = [[1, 0], [0.99, 0.01], [0, 1]]

    mock_cosine_similarity.return_value = [[1.0, 0.99, 0.0], [0.99, 1.0, 0.0], [0.0, 0.0, 1.0]]

    deduplicator = SemanticDeduplicator(threshold=0.9)
    result = deduplicator.optimize(data)

    assert len(result) == 2
    assert "item1" in result
    assert "item2" in result
    assert "item1_similar" not in result


def test_semantic_deduplicator_nested_structure(mock_sentence_transformer, mock_cosine_similarity):
    """Test SemanticDeduplicator on a nested structure."""
    data = {"group1": ["A", "A_dup"], "group2": {"subgroup": ["B", "B_dup", "C"]}}

    mock_model_instance = mock_sentence_transformer.return_value

    embed1 = [[1], [0.99]]
    sim1 = [[1.0, 0.99], [0.99, 1.0]]

    embed2 = [[1], [0.99], [0]]
    sim2 = [[1.0, 0.99, 0.0], [0.99, 1.0, 0.0], [0.0, 0.0, 1.0]]

    mock_model_instance.encode.side_effect = [embed1, embed2]
    mock_cosine_similarity.side_effect = [sim1, sim2]

    deduplicator = SemanticDeduplicator(threshold=0.9)
    result = deduplicator.optimize(data)

    assert len(result["group1"]) == 1
    assert result["group1"][0] == "A"

    assert len(result["group2"]["subgroup"]) == 2
    assert "B" in result["group2"]["subgroup"]
    assert "C" in result["group2"]["subgroup"]


def test_semantic_deduplicator_text_extraction(mock_sentence_transformer, mock_cosine_similarity):
    """Test custom text extraction."""
    data = [{"text": "hello"}, {"text": "hello world"}]

    def extractor(item):
        return item["text"]

    mock_model_instance = mock_sentence_transformer.return_value
    mock_model_instance.encode.return_value = [[1], [0]]
    mock_cosine_similarity.return_value = [[1.0, 0.0], [0.0, 1.0]]

    deduplicator = SemanticDeduplicator(text_extraction_func=extractor)
    deduplicator.optimize(data)

    args, _ = mock_model_instance.encode.call_args
    assert args[0] == ["hello", "hello world"]


def test_semantic_deduplicator_default_extraction(
    mock_sentence_transformer, mock_cosine_similarity
):
    """Test default text extraction logic."""
    data = [
        {"description": "desc1", "other": "ignored"},
        {"val1": "part1", "val2": "part2"},
        "string_item",
        123,
    ]

    mock_model_instance = mock_sentence_transformer.return_value
    mock_model_instance.encode.return_value = [[1], [0], [0]]
    mock_cosine_similarity.return_value = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    deduplicator = SemanticDeduplicator()
    result = deduplicator.optimize(data)

    args, _ = mock_model_instance.encode.call_args
    assert args[0] == ["desc1", "part1 part2", "string_item"]
    assert 123 in result


def test_semantic_deduplicator_short_list(mock_sentence_transformer, mock_cosine_similarity):
    """Test that lists with < 2 items are ignored."""
    data = ["A"]
    deduplicator = SemanticDeduplicator()
    result = deduplicator.optimize(data)

    assert result == ["A"]
    mock_sentence_transformer.return_value.encode.assert_not_called()


def test_semantic_deduplicator_no_valid_texts(mock_sentence_transformer, mock_cosine_similarity):
    """Test that lists with no valid texts are ignored."""
    data = [1, 2, 3]  # Integers return None in default extractor
    deduplicator = SemanticDeduplicator()
    result = deduplicator.optimize(data)

    assert result == [1, 2, 3]
    mock_sentence_transformer.return_value.encode.assert_not_called()
