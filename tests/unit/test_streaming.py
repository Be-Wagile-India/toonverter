import io
from typing import Any

from toonverter.streaming import StreamingDecoder, StreamingEncoder


def test_streaming_encoder_table() -> None:
    """Test that dictionaries are correctly encoded as a TOON table."""
    output = io.StringIO()
    encoder = StreamingEncoder(output)

    data: list[dict[str, Any]] = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]

    encoder.dump_iterable("users", data)

    result = output.getvalue()
    expected_header = "users[2]{id,name}:\n"
    expected_rows = "  1,Alice\n  2,Bob\n"

    assert expected_header in result
    assert expected_rows in result


def test_streaming_encoder_quoting() -> None:
    """Test that values containing commas are quoted correctly."""
    output = io.StringIO()
    encoder = StreamingEncoder(output)

    data = [{"id": 1, "desc": "Hello, World"}]
    encoder.dump_iterable("items", data)

    result = output.getvalue()
    assert '"Hello, World"' in result


def test_streaming_decoder_table() -> None:
    """Test that TOON table format is decoded back into dictionaries."""
    toon_data = """
users[2]{id,name}:
  1,Alice
  2,Bob
"""
    stream = io.StringIO(toon_data.strip())
    decoder = StreamingDecoder(stream)

    items = list(decoder.iter_items())

    assert len(items) == 2

    # Check first item
    key1, val1 = items[0]
    assert key1 == "users"
    assert isinstance(val1, dict)
    assert val1["id"] == "1"
    assert val1["name"] == "Alice"


def test_streaming_decoder_nested_skips() -> None:
    """Test that the decoder handles nesting context (conceptually)."""
    toon_data = """
meta:
  version: 1.0
data[1]{val}:
  100
"""
    stream = io.StringIO(toon_data.strip())
    decoder = StreamingDecoder(stream)

    items = list(decoder.iter_items())

    # Should capture meta version and data row
    assert ("version", "1.0") in items
    assert items[1][0] == "data"
    assert items[1][1] == {"val": "100"}
