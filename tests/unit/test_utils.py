"""Comprehensive tests for utility modules."""

from pathlib import Path

import pytest

from toonverter.core.exceptions import FileOperationError, ValidationError
from toonverter.utils.io import read_file, write_file
from toonverter.utils.validation import (
    validate_data_not_empty,
    validate_file_exists,
    validate_format_name,
)


class TestFileIO:
    """Test file I/O utilities."""

    def test_write_and_read_file(self, tmp_path):
        """Test writing and reading a file."""
        file_path = tmp_path / "test.txt"
        content = "Hello, World!"

        write_file(str(file_path), content)
        result = read_file(str(file_path))

        assert result == content

    def test_write_file_creates_directories(self, tmp_path):
        """Test write_file creates parent directories."""
        file_path = tmp_path / "subdir" / "nested" / "test.txt"
        content = "Test content"

        write_file(str(file_path), content)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_write_file_unicode_content(self, tmp_path):
        """Test writing unicode content."""
        file_path = tmp_path / "unicode.txt"
        content = "Hello 世界 🌍"

        write_file(str(file_path), content)
        result = read_file(str(file_path))

        assert result == content

    def test_read_nonexistent_file_raises_error(self):
        """Test reading nonexistent file raises error."""
        with pytest.raises(FileOperationError, match="Failed to read file"):
            read_file("/nonexistent/file.txt")

    def test_write_to_invalid_path_raises_error(self):
        """Test writing to invalid path raises error."""
        # Use a path that cannot be created (e.g., under /dev/null)
        with pytest.raises(FileOperationError, match="Failed to write file"):
            write_file("/dev/null/impossible/file.txt", "content")

    def test_read_file_empty_content(self, tmp_path):
        """Test reading file with empty content."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")

        result = read_file(str(file_path))
        assert result == ""

    def test_write_file_multiline(self, tmp_path):
        """Test writing multiline content."""
        file_path = tmp_path / "multiline.txt"
        content = "Line 1\nLine 2\nLine 3"

        write_file(str(file_path), content)
        result = read_file(str(file_path))

        assert result == content


class TestFileValidation:
    """Test file validation utilities."""

    def test_validate_file_exists_valid_file(self, tmp_path):
        """Test validating existing file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")

        result = validate_file_exists(str(file_path))
        assert isinstance(result, Path)
        assert result.exists()

    def test_validate_file_exists_nonexistent_raises_error(self):
        """Test validating nonexistent file raises error."""
        with pytest.raises(ValidationError, match="File not found"):
            validate_file_exists("/nonexistent/file.txt")

    def test_validate_file_exists_directory_raises_error(self, tmp_path):
        """Test validating directory raises error."""
        with pytest.raises(ValidationError, match="not a file"):
            validate_file_exists(str(tmp_path))


class TestFormatNameValidation:
    """Test format name validation."""

    def test_validate_format_name_valid(self):
        """Test validating valid format name."""
        assert validate_format_name("json") == "json"
        assert validate_format_name("YAML") == "yaml"
        assert validate_format_name("  XML  ") == "xml"

    def test_validate_format_name_normalizes_case(self):
        """Test format name is normalized to lowercase."""
        assert validate_format_name("JSON") == "json"
        assert validate_format_name("YaML") == "yaml"

    def test_validate_format_name_strips_whitespace(self):
        """Test format name strips whitespace."""
        assert validate_format_name("  json  ") == "json"
        assert validate_format_name("\tyaml\n") == "yaml"

    def test_validate_format_name_empty_raises_error(self):
        """Test empty format name raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_format_name("")


class TestDataValidation:
    """Test data validation utilities."""

    def test_validate_data_not_empty_valid_data(self):
        """Test validating non-empty data."""
        validate_data_not_empty({"key": "value"})
        validate_data_not_empty([1, 2, 3])
        validate_data_not_empty("text")
        validate_data_not_empty(42)
        validate_data_not_empty(0)  # Zero is not empty
        validate_data_not_empty(False)  # False is not empty

    def test_validate_data_not_empty_none_raises_error(self):
        """Test None data raises error."""
        with pytest.raises(ValidationError, match="cannot be None"):
            validate_data_not_empty(None)

    def test_validate_data_not_empty_empty_string_raises_error(self):
        """Test empty string raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_data_not_empty("")

    def test_validate_data_not_empty_empty_list_raises_error(self):
        """Test empty list raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_data_not_empty([])

    def test_validate_data_not_empty_empty_dict_raises_error(self):
        """Test empty dict raises error."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_data_not_empty({})
