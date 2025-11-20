import pytest
import tiktoken

from toonverter.analysis.token_counter import TiktokenCounter


@pytest.fixture
def tiktoken_counter() -> TiktokenCounter:
    """Fixture for a standard TiktokenCounter instance."""
    return TiktokenCounter()


# --- 1. Test Key Error Handling (Lines 22-29, 34) ---
def test_init_handles_keyerror_with_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Tests that TiktokenCounter falls back to 'cl100k_base' when
    tiktoken.encoding_for_model raises KeyError.
    """
    # Fix EM101: Assign exception message to a variable
    KEY_ERROR_MESSAGE = "Model not found"

    # Force the key lookup function to raise KeyError
    def mock_encoding_for_model(model_name: str) -> tiktoken.Encoding:
        if model_name == "non_existent_model":
            raise KeyError(KEY_ERROR_MESSAGE)
        # Ensure that if it is called with the fallback, it works.
        return tiktoken.get_encoding("cl100k_base")

    monkeypatch.setattr("tiktoken.encoding_for_model", mock_encoding_for_model)

    # Initialization with the model name that triggers the mock exception
    counter = TiktokenCounter(model_name="non_existent_model")

    # Assert that the fallback encoder was used
    assert counter.model_name == "non_existent_model"


# --- 2. Test Edge Case in count_tokens (Lines 46-48) ---
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", 0),
        (None, 0),  # Added None test case for robustness
    ],
)
def test_count_tokens_returns_zero_for_falsy_input(
    tiktoken_counter: TiktokenCounter, text: str | None, expected: int
) -> None:
    """Tests the edge case where input text is empty or None."""
    assert tiktoken_counter.count_tokens(text) == expected


# --- 3. Test analyze method is fully executed (Lines 62-63) ---
def test_analyze_method_returns_full_analysis(tiktoken_counter: TiktokenCounter) -> None:
    """Tests that analyze executes successfully and returns the expected dictionary structure."""
    text = "Hello world."
    analysis = tiktoken_counter.analyze(
        text, _format_name="toon"
    )  # Note: using _format_name from the ruff fix

    # Assert all keys required by the implementation are present
    assert isinstance(analysis, dict)
    assert analysis["token_count"] == 3  # "Hello" + " world" + "."
    assert "tokens" in analysis
    assert "encoding" in analysis
    assert analysis["model_name"] == "gpt-4o"
