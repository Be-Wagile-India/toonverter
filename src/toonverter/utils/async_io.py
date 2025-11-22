import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any  # <-- ADD Union for flexible Path type hint


# ... (rest of _run_in_thread remains the same)


def _run_in_thread(func: Callable, *args: Any, **kwargs: Any) -> Any:
    # ... (content remains the same)
    try:
        asyncio.get_running_loop()
        return asyncio.to_thread(func, *args, **kwargs)
    except RuntimeError:
        return func(*args, **kwargs)


async def async_read_file(path: str | Path) -> str:  # <-- Use Union[str, Path]
    """Reads a file asynchronously."""
    # 1. Create Path object (Fixes the _accessor issue and enables instance method)
    path_obj = Path(path)

    # 2. Define the synchronous operation to run in the thread
    def sync_read():
        # 3. Use the instance method and run the reading operation
        with path_obj.open(encoding="utf-8") as f:
            return f.read()

    return await _run_in_thread(sync_read)


async def async_write_file(path: str | Path, content: str) -> None:  # <-- Use Union[str, Path]
    """Writes content to a file asynchronously."""
    # 1. Create Path object
    path_obj = Path(path)

    # 2. Define the synchronous operation to run in the thread
    def sync_write():
        # 3. Use the instance method and run the writing operation
        with path_obj.open("w", encoding="utf-8") as f:
            f.write(content)

    await _run_in_thread(sync_write)
