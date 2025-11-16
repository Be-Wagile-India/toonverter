"""Input validation utilities."""

from pathlib import Path
from typing import Any

from ..core.exceptions import ValidationError


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
        raise ValidationError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValidationError(f"Path is not a file: {file_path}")
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
        raise ValidationError("Format name cannot be empty")
    return format_name.lower().strip()


def validate_data_not_empty(data: Any) -> None:
    """Validate that data is not empty.

    Args:
        data: Data to validate

    Raises:
        ValidationError: If data is empty
    """
    if data is None:
        raise ValidationError("Data cannot be None")
    if isinstance(data, (str, list, dict)) and not data:
        raise ValidationError("Data cannot be empty")
