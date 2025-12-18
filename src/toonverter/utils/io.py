"""File I/O utilities."""

import json
import warnings
from collections.abc import Generator
from pathlib import Path
from typing import Any

from toonverter.core.exceptions import FileOperationError


def read_file(file_path: str) -> str:
    """Read file content.

    Args:
        file_path: Path to file

    Returns:
        File content as string

    Raises:
        FileOperationError: If reading fails
    """
    try:
        path = Path(file_path)
        return path.read_text(encoding="utf-8")
    except Exception as e:
        msg = f"Failed to read file {file_path}: {e}"
        raise FileOperationError(msg) from e


def write_file(file_path: str, content: str) -> None:
    """Write content to file.

    Args:
        file_path: Path to file
        content: Content to write

    Raises:
        FileOperationError: If writing fails
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except Exception as e:
        msg = f"Failed to write file {file_path}: {e}"
        raise FileOperationError(msg) from e


def _read_json_stream(file_path: str) -> Generator[Any, None, None]:
    """Stream JSON objects from a file (JSONL or JSON Array).





    Args:


        file_path: Path to input file





    Yields:


        Parsed JSON objects





    Raises:


        FileOperationError: If reading fails


    """

    path = Path(file_path)

    if not path.exists():
        msg = f"File not found: {file_path}"

        raise FileOperationError(msg)

    # Strategy 1: Attempt ijson for standard JSON arrays (robust)

    try:
        import ijson  # type: ignore # noqa: PLC0415

        with path.open("rb") as f:
            # Check first byte to see if it's an array

            first_byte = f.read(1)

            f.seek(0)

            if first_byte == b"[":
                # Standard JSON Array

                yield from ijson.items(f, "item")

                return

    except ImportError:
        pass

    # Strategy 2: Line-based reading (JSONL / NDJSON)

    # Also works as a fallback for simple pretty-printed JSON arrays if ijson is missing

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            clean_line = line.strip()

            if not clean_line:
                continue

            # Skip array brackets for pretty-printed JSON fallback

            if clean_line in ("[", "]"):
                continue

            # Remove trailing comma for pretty-printed JSON

            if clean_line.endswith(","):
                clean_line = clean_line[:-1]

            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                warnings.warn(f"Skipping malformed JSON line in {file_path}: {e}", stacklevel=2)


def load_stream(file_path: str, format: str | None = None) -> Generator[Any, None, None]:
    """Stream objects from a file.





    Args:


        file_path: Path to input file


        format: Format (json, jsonl, etc.). inferred from extension if None.





    Yields:


        Parsed objects





    Raises:


        FileOperationError: If reading fails or format not supported for streaming


    """

    if format is None:
        ext = Path(file_path).suffix.lower()

        format = ext[1:] if ext.startswith(".") else ext

    if format in ("json", "jsonl", "ndjson"):
        yield from _read_json_stream(file_path)

    else:
        # TODO: Add support for CSV streaming, etc.

        msg = f"Streaming not supported for format: {format}"

        raise FileOperationError(msg)
