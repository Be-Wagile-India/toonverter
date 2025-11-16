"""File I/O utilities."""

from pathlib import Path

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
