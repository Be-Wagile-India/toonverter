"""Input validation utilities."""

from pathlib import Path
from typing import Any

from toonverter.core.exceptions import ValidationError


def validate_file_exists(file_path: str) -> Path:
    """Validate that file exists.

    Args:
        file_path: Path to file

    Returns:
        Path object

    Raises:
        ValidationError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {file_path}"
        raise ValidationError(msg)
    if not path.is_file():
        msg = f"Path is not a file: {file_path}"
        raise ValidationError(msg)
    return path


def validate_format_name(format_name: str) -> str:
    """Validate format name.

    Args:
        format_name: Format identifier

    Returns:
        Normalized format name

    Raises:
        ValidationError: If format name is invalid
    """
    if not format_name:
        msg = "Format name cannot be empty"
        raise ValidationError(msg)
    return format_name.lower().strip()


def validate_data_not_empty(data: Any) -> None:
    """Validate that data is not empty.

    Args:
        data: Data to validate

    Raises:
        ValidationError: If data is empty
    """
    if data is None:
        msg = "Data cannot be None"
        raise ValidationError(msg)
    if isinstance(data, (str, list, dict)) and not data:
        msg = "Data cannot be empty"
        raise ValidationError(msg)
