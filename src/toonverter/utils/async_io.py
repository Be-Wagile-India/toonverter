import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any


# Use 'anyio' or similar library for production code, but for standard
# library asyncio, we use run_in_executor for blocking I/O operations.
# Note: For simplicity and portability, we'll use standard file handling
# with asyncio.to_thread, available in Python 3.9+.


def _run_in_thread(func: Callable, *args: Any, **kwargs: Any) -> Any:
    """Helper to run a synchronous blocking function in a separate thread."""
    # asyncio.to_thread is preferred for simple I/O in Python 3.9+
    try:
        # Check if we are already in an async loop
        asyncio.get_running_loop()
        return asyncio.to_thread(func, *args, **kwargs)
    except RuntimeError:
        # If not in an event loop, run synchronously
        return func(*args, **kwargs)


async def async_read_file(path: str) -> str:
    """Reads a file asynchronously."""
    with Path.open(path, encoding="utf-8") as f:
        return await _run_in_thread(f.read)


async def async_write_file(path: str, content: str) -> None:
    """Writes content to a file asynchronously."""
    with Path.open(path, "w", encoding="utf-8") as f:
        await _run_in_thread(f.write, content)
