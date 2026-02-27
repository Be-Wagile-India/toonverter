"Extended tests for semantic deduplication to increase coverage."

import sys
from unittest.mock import patch

import numpy as np
import pytest

from toonverter.analysis.deduplication import ExactDeduplicator, SemanticDeduplicator


def test_exact_deduplicator_key_selector():
    """Test ExactDeduplicator with a key selector."""
    data = [
        {"id": 1, "metadata": "a"},
        {"id": 1, "metadata": "b"},  # Duplicate based on ID
        {"id": 2, "metadata": "a"},  # Unique
    ]

    # Select only the 'id' field for deduplication
    deduplicator = ExactDeduplicator(key_selector=lambda x: x["id"])
    result = deduplicator.process(data)

    assert len(result.unique_items) == 2
    assert result.unique_items[0]["id"] == 1
    assert result.unique_items[1]["id"] == 2
    assert result.duplicate_count == 1


def test_exact_deduplicator_canonicalize_complex():
    """Test _canonicalize with various types including sets and tuples."""
    deduplicator = ExactDeduplicator()

    data = {
        "set": {3, 1, 2},
        "tuple": (1, 2),
        "list": [3, 2, 1, {"inner": (4, 5)}],
        "dict": {"b": 2, "a": 1},
        "other": 123,
    }

    canonical = deduplicator._canonicalize(data)

    assert canonical["set"] == [1, 2, 3]  # Sets become sorted lists
    assert canonical["tuple"] == [1, 2]  # Tuples become lists
    assert canonical["list"][0] == 3
    assert canonical["list"][3]["inner"] == [4, 5]
    assert list(canonical["dict"].keys()) == ["a", "b"]  # Dicts are sorted
    assert canonical["other"] == 123


def test_exact_deduplicator_extract_text_varied():
    """Test _extract_text with non-string/non-dict types."""
    deduplicator = ExactDeduplicator()

    assert deduplicator._extract_text("hello") == "hello"
    assert deduplicator._extract_text(123) == "123"
    assert deduplicator._extract_text(None) == "None"

    # Dict with key selector
    deduplicator_ks = ExactDeduplicator(key_selector=lambda x: x.get("text"))
    assert deduplicator_ks._extract_text({"text": "extracted", "other": "ignored"}) == "extracted"


@pytest.fixture
def mock_deps():
    with (
        patch("sentence_transformers.SentenceTransformer") as mock_st,
        patch("sklearn.metrics.pairwise.cosine_similarity") as mock_cs,
    ):
        yield mock_st, mock_cs


def test_exact_deduplicator_large_list_path(mock_deps):
    """Test the large list (> 1000 items) path in ExactDeduplicator."""
    mock_st, mock_cs = mock_deps

    # Create 1001 unique items
    data = [f"item_{i}" for i in range(1001)]

    mock_model_instance = mock_st.return_value
    # Mock embeddings
    mock_model_instance.encode.return_value = np.zeros((1001, 10))

    def side_effect(c, r):
        res = np.zeros((1, len(r)))
        if len(r) == 1000:  # i=0, items 1..1000
            res[0, 999] = 1.0  # item 1000 is dup of 0
        return res

    mock_cs.side_effect = side_effect

    deduplicator = ExactDeduplicator(mode="semantic", threshold=0.9)
    result = deduplicator.process(data)

    assert len(result.unique_items) == 1000
    assert mock_cs.call_count > 1


def test_exact_deduplicator_semantic_duplicates_skipping(mock_deps):
    """Test skipping already identified duplicates in _process_semantic."""
    mock_st, mock_cs = mock_deps

    data = ["A", "B", "C"]

    mock_model_instance = mock_st.return_value
    mock_model_instance.encode.return_value = np.zeros((3, 10))

    # 1 is dup of 0. 2 is dup of 1.
    mock_cs.return_value = np.array([[1.0, 0.95, 0.0], [0.95, 1.0, 0.95], [0.0, 0.95, 1.0]])

    deduplicator = ExactDeduplicator(mode="semantic", threshold=0.9)
    result = deduplicator.process(data)

    assert result.unique_items == ["A", "C"]
    assert result.duplicate_count == 1


def test_exact_deduplicator_semantic_edge_cases(mock_deps):
    """Test edge cases in _process_semantic."""
    _mock_st, _mock_cs = mock_deps

    deduplicator = ExactDeduplicator(mode="semantic")
    # Empty candidates
    assert deduplicator._process_semantic([]) == ([], [])

    # One candidate
    assert deduplicator._process_semantic(["A"]) == (["A"], [])

    # No valid texts
    with patch.object(ExactDeduplicator, "_extract_text", return_value=None):
        assert deduplicator._process_semantic(["A", "B"]) == (["A", "B"], [])


def test_semantic_deduplicator_large_list_path(mock_deps):
    """Test the large list (> 1000 items) path in SemanticDeduplicator."""
    mock_st, mock_cs = mock_deps

    data = [f"item_{i}" for i in range(1001)]

    mock_model_instance = mock_st.return_value
    mock_model_instance.encode.return_value = np.zeros((1001, 10))

    def side_effect(c, r):
        res = np.zeros((1, len(r)))
        if len(r) == 1000:  # First row check (i=0)
            res[0, 0] = 1.0  # item 1 is dup of 0
            res[0, 1] = 1.0  # item 2 is dup of 0
        return res

    mock_cs.side_effect = side_effect

    deduplicator = SemanticDeduplicator(threshold=0.9)
    result = deduplicator.optimize(data)

    assert len(result) == 999
    assert mock_cs.call_count > 1


def test_semantic_deduplicator_extract_text_no_description():
    """Test _extract_text_for_embedding when 'description' is missing."""
    deduplicator = SemanticDeduplicator()

    # Dict without description
    data = {"name": "Alice", "title": "Developer", "age": 30}
    text = deduplicator._extract_text_for_embedding(data)
    assert "Alice" in text
    assert "Developer" in text
    assert "30" not in text

    # Non-dict/non-string should return None
    assert deduplicator._extract_text_for_embedding(123) is None


def test_semantic_deduplicator_nested_traversal(mock_deps):
    """Test deep nested traversal in _visit."""
    mock_st, mock_cs = mock_deps

    data = {
        "level1": {"level2": ["item1", "item2"]},
        "list1": [{"inner_list": ["a", "b"]}],
        "primitive": "value",
    }

    mock_model_instance = mock_st.return_value
    mock_model_instance.encode.return_value = np.zeros((2, 10))
    mock_cs.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])

    deduplicator = SemanticDeduplicator()
    deduplicator.optimize(data)

    assert mock_model_instance.encode.call_count == 2


def test_semantic_deduplicator_model_property_error():
    """Test model property when sentence_transformers is missing."""
    with patch.dict("sys.modules", {"sentence_transformers": None}):
        deduplicator = SemanticDeduplicator()
        with pytest.raises(ImportError, match="sentence-transformers is required"):
            _ = deduplicator.model


def test_semantic_deduplicator_missing_sklearn(mock_deps):
    """Test _deduplicate_list when sklearn is missing."""
    mock_st, _ = mock_deps

    with patch.dict("sys.modules", {"sklearn.metrics.pairwise": None}):
        deduplicator = SemanticDeduplicator()
        data = ["a", "b"]
        deduplicator.optimize(data)
        mock_st.return_value.encode.assert_not_called()


def test_exact_deduplicator_empty_items():
    """Test ExactDeduplicator with empty data."""
    deduplicator = ExactDeduplicator()
    result = deduplicator.process([])
    assert result.unique_items == []
    assert result.duplicate_count == 0
    assert result.reduction_percentage == 0.0


def test_semantic_deduplicator_cached_embeddings(mock_deps):
    """Test using cached embeddings."""
    mock_st, mock_cs = mock_deps

    mock_model_instance = mock_st.return_value
    # Initial uncached texts: "A", "B"
    mock_model_instance.encode.return_value = np.zeros((2, 10))
    mock_cs.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])

    deduplicator = SemanticDeduplicator()
    deduplicator.optimize(["A", "B"])

    mock_model_instance.encode.reset_mock()
    mock_model_instance.encode.return_value = np.zeros((1, 10))
    deduplicator.optimize(["A", "C"])
    args, _ = mock_model_instance.encode.call_args
    assert "A" not in args[0]
    assert "C" in args[0]

    mock_model_instance.encode.reset_mock()
    deduplicator.optimize(["A", "B"])
    mock_model_instance.encode.assert_not_called()


def test_semantic_deduplicator_empty_list_visit():
    """Test _visit with empty structures."""
    deduplicator = SemanticDeduplicator()
    assert deduplicator.optimize({}) == {}
    assert deduplicator.optimize([]) == []


def test_exact_deduplicator_init_model_import_error():
    """Test _init_model ImportError path in ExactDeduplicator."""
    # Ensure it's not already in sys.modules
    old_mod = sys.modules.get("sentence_transformers")
    try:
        if "sentence_transformers" in sys.modules:
            del sys.modules["sentence_transformers"]

        with patch.dict("sys.modules", {"sentence_transformers": None}):
            deduplicator = ExactDeduplicator(mode="semantic")
            deduplicator._init_model()
            assert deduplicator.mode == "exact"
    finally:
        if old_mod:
            sys.modules["sentence_transformers"] = old_mod


def test_exact_deduplicator_extract_text_dict_heuristic():
    """Test _extract_text dictionary heuristic."""
    deduplicator = ExactDeduplicator()
    data = {"a": "val1", "b": 123, "c": [1, 2]}
    text = deduplicator._extract_text(data)
    assert "val1" in text
    assert "123" in text
    assert "[1, 2]" not in text
