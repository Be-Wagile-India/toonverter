from pathlib import Path

import pytest

from toonverter import async_convert, async_decode, async_encode, async_read_file, async_write_file


# --- Fixtures and Setup ---


# This fixture creates a temporary dummy file for testing I/O
@pytest.fixture
def dummy_file(tmp_path: Path) -> Path:
    """Creates a temporary file with sample data."""
    file_path = tmp_path / "test_input.json"
    content = '{"user": "Zaphod", "id": 42}'
    file_path.write_text(content)
    return file_path


# This fixture creates a temporary output path
@pytest.fixture
def output_path(tmp_path: Path) -> Path:
    """Creates a path for the output file."""
    return tmp_path / "test_output.toon"


# --- Tests for Async Utilities (async_io) ---


@pytest.mark.asyncio
async def test_async_read_write(tmp_path: Path) -> None:
    """Test async reading and writing of files."""
    test_path = tmp_path / "temp_async.txt"
    test_content = "This content should be written and read asynchronously."

    await async_write_file(str(test_path), test_content)
    assert test_path.exists()

    read_content = await async_read_file(str(test_path))
    assert read_content == test_content


# --- Tests for Async API (async_api) ---


@pytest.mark.asyncio
async def test_async_encode_decode() -> None:
    """Test that async encode and decode functions work."""
    data = {"project": "Toonverter", "version": 2}

    # Use standard JSON adapter for stable test, assuming it's registered
    encoded_str = await async_encode(data, to_format="json")

    # Check if the result is a string
    assert isinstance(encoded_str, str)
    assert '"project": "Toonverter"' in encoded_str

    decoded_data = await async_decode(encoded_str, from_format="json")
    assert decoded_data == data


@pytest.mark.asyncio
async def test_async_convert_file(dummy_file: Path, output_path: Path) -> None:
    """Test async conversion from one format to another."""

    # Convert JSON file (dummy_file) to TOON (output_path)
    result = await async_convert(
        source=str(dummy_file), target=str(output_path), from_format="json", to_format="toon"
    )

    assert result.success is True
    assert output_path.exists()

    # Verify the converted content in the output file
    output_content = await async_read_file(str(output_path))

    # Expected output for {"user": "Zaphod", "id": 42} in TOON format
    # The exact TOON format depends on your encoder, but should be close to this:
    assert "user: Zaphod" in output_content
    assert "id: 42" in output_content


# Note: Remember to install pytest-asyncio and ensure your core encoder/decoder
# logic is available in the synchronous adapters used by the async wrappers.
