import pytest

from toonverter.analysis.diff import ToonDiffer, ToonDiffResult


# Mock data dictionary used across tests
DATA_A = {
    "name": "Project Alpha",
    "version": 1.0,
    "active": True,
    "metrics": [10, 20, 30],
    "config": {"timeout": 5000, "mode": "safe"},
}

DATA_B = {
    "name": "Project Beta",  # Changed value
    "version": 1.0,  # Unchanged
    "active": "false",  # Changed type and value
    "metrics": [10, 20, 30, 40],  # Added item
    "config": {
        "timeout": 5000,
        "mode": "aggressive",  # Changed value
        "retries": 3,  # Added key
    },
    "new_key": 100,  # Added key at root
}

DATA_C = {
    "name": "Project Alpha",
    "version": 1.0,
    "active": True,
    "metrics": [10, 20, 30],
    "config": {"timeout": 5000, "mode": "safe"},
}  # Identical to DATA_A


@pytest.fixture
def differ() -> ToonDiffer:
    """Fixture to provide a ToonDiffer instance."""
    # Note: Using a fixed model for token counting stability, e.g., 'gpt-3.5-turbo'
    # Ensure a token counter is mocked or available in a real environment.
    return ToonDiffer(model="cl100k_base")  # Use an existing tokenizer model name


# --- Structural Comparison Tests ---


def test_compare_structures_identical(differ: ToonDiffer) -> None:
    """Test structural comparison when data is identical."""
    diffs = differ._compare_structures(DATA_A, DATA_C)
    assert diffs == {}


def test_compare_structures_changes(differ: ToonDiffer) -> None:
    """Test structural comparison for multiple differences between DATA_A and DATA_B."""
    diffs = differ._compare_structures(DATA_A, DATA_B)

    assert "name" in diffs
    assert "active" in diffs
    assert "metrics.length" in diffs  # List length change
    assert "config.mode" in diffs
    assert "config.retries" in diffs  # Key added
    assert "new_key" in diffs  # Key added at root
    assert "version" not in diffs  # Should be unchanged


def test_compare_structures_key_removed(differ: ToonDiffer) -> None:
    """Test structural comparison when a key is removed."""
    data_b_subset = DATA_B.copy()
    data_b_subset.pop("new_key")

    # Compare B to a subset of B (removing 'new_key')
    diffs = differ._compare_structures(DATA_B, data_b_subset)
    assert "new_key" in diffs
    assert "Key removed." in diffs["new_key"]


def test_compare_structures_base_types(differ: ToonDiffer) -> None:
    """Test comparison for simple differing types."""
    diffs = differ._compare_structures(123, "123")
    assert "root" in diffs
    assert "Value changed/Type mismatch" in diffs["root"]


# --- Functional Comparison Tests (diff_data) ---


def test_diff_data_identical(differ: ToonDiffer) -> None:
    """Test the main diff_data function with identical data."""
    # Assuming the TOON encoder produces identical strings for identical dicts
    result = differ.diff_data(DATA_A, DATA_C)

    assert isinstance(result, ToonDiffResult)
    assert result.identical is True
    assert result.token_diff == 0
    assert result.structural_diffs == {}


def test_diff_data_differences(differ: ToonDiffer) -> None:
    """Test the main diff_data function with data that has structural differences."""
    # Note: Token changes depend heavily on your TOON encoder's output.
    # We mainly test that the result indicates a difference and captures structure.

    result = differ.diff_data(DATA_A, DATA_B)

    assert isinstance(result, ToonDiffResult)
    assert result.identical is False
    assert result.token_diff != 0  # Token counts should change due to structural changes
    assert len(result.structural_diffs) > 0

    # Check that structural changes match the expectations from the previous test
    assert "name" in result.structural_diffs
    assert "config.retries" in result.structural_diffs


def test_diff_data_token_count_only(differ: ToonDiffer) -> None:
    """Test case where structures are identical but encoding might result in different tokens (e.g., formatting options).
    For simplicity, we simulate a structural difference that only changes tokens."""
    data_d = {"key": "short_string"}
    data_e = {"key": "long_string_that_uses_more_tokens"}

    result = differ.diff_data(data_d, data_e)

    assert result.identical is False
    assert result.token_diff > 0
    # The structural diff should report the value change
    assert "key" in result.structural_diffs


def test_toon_diff_result_summary() -> None:
    """Test the human-readable summary output."""
    mock_result = ToonDiffResult(
        identical=False,
        token_diff=15,
        structural_diffs={"key.path": "Value changed"},
        metadata={},
    )
    summary = mock_result.summary()
    assert "DIFFERENT" in summary
    assert "1 item" in summary
    assert "+15 tokens" in summary
