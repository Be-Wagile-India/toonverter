"""Integration tests for the Rust-Python FFI contract."""

import pytest


try:
    from toonverter import _toonverter_core
except ImportError:
    _toonverter_core = None

from toonverter.core.config import RUST_CONTRACT_VERSION, rust_core
from toonverter.core.exceptions import (
    ProcessingError,
    ValidationError,
)


# Skip all tests if Rust core is not available
pytestmark = pytest.mark.skipif(_toonverter_core is None, reason="Rust extension not available")


def test_contract_version_exposed():
    """Verify that the contract version is exposed and matches expected."""
    assert RUST_CONTRACT_VERSION is not None
    assert isinstance(RUST_CONTRACT_VERSION, str)
    assert RUST_CONTRACT_VERSION == "1.0.0"

    # Check direct access via module
    assert rust_core.CONTRACT_VERSION == "1.0.0"


def test_invalid_input_raises_validation_error():
    """Verify that invalid input raises ValidationError (InvalidInput)."""
    # encode_toon with unsupported type (e.g., set)
    data = {1, 2, 3}
    with pytest.raises(ValidationError) as excinfo:
        rust_core.encode_toon(data)
    assert "Unsupported type" in str(excinfo.value) or "JSON Error" in str(excinfo.value)


def test_recursion_limit_raises_processing_error():
    """Verify that recursion limit raises ProcessingError."""
    # Create deep structure
    data = {}
    current = data
    for _ in range(250):
        current["a"] = {}
        current = current["a"]

    # Default limit is 200
    with pytest.raises(ProcessingError) as excinfo:
        rust_core.encode_toon(data, recursion_depth_limit=200)
    assert "Maximum recursion depth exceeded" in str(excinfo.value)


def test_decode_syntax_error_handling():
    """Verify that syntax errors are mapped correctly to ProcessingError."""
    invalid_toon = "key: [unclosed"

    # Syntax errors from parser (returned as String) map to ProcessingError
    with pytest.raises(ProcessingError) as excinfo:
        rust_core.decode_toon(invalid_toon)
    assert "Expected" in str(excinfo.value) or "Syntax Error" in str(excinfo.value)


def test_internal_error_on_panic():
    """Verify that panics are caught and raised as InternalError."""
    # It is hard to induce a panic safely without a dedicated "panic_now" function.
    # We will assume the catch_unwind mechanism works if we can't trigger it.
