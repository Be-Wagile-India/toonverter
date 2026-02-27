"""Integration tests for panic safety in the Rust extension."""

import pytest


try:
    from toonverter import _toonverter_core
except ImportError:
    _toonverter_core = None

from toonverter.core.exceptions import InternalError


# Skip all tests if Rust core is not available
pytestmark = pytest.mark.skipif(_toonverter_core is None, reason="Rust extension not available")


def test_rust_panic_is_caught():
    """Verify that a Rust panic is caught and converted to InternalError."""
    panic_msg = "Test Panic Safety"

    with pytest.raises(InternalError) as excinfo:
        _toonverter_core.trigger_panic(panic_msg)

    # Check that the exception message contains the panic message
    assert "Panic" in str(excinfo.value)
    assert panic_msg in str(excinfo.value)
