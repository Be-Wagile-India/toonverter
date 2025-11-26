"Tests for the Streaming Decoder."

from collections.abc import Iterator

import pytest

from toonverter.decoders.stream_decoder import StreamDecoder


@pytest.fixture
def stream_decoder() -> StreamDecoder:
    return StreamDecoder()


def stream_from_string(text: str) -> Iterator[str]:
    """Simulate file stream."""
    yield from text.splitlines(keepends=True)


class TestToonStreamDecoder:
    """Test suite for ToonStreamDecoder."""

    def test_stream_list_basic(self, stream_decoder: StreamDecoder) -> None:
        """Test streaming a basic list."""
        toon = """
[3]:
- 1
- 2
- 3
"""
        stream = stream_from_string(toon)
        items = list(stream_decoder.decode_stream(stream))
        assert items == [1, 2, 3]

    def test_stream_list_objects(self, stream_decoder: StreamDecoder) -> None:
        """Test streaming a list of objects."""
        # Clean construction to avoid whitespace ambiguity
        toon = "[2]:\n- \n  name: Alice\n  age: 30\n- \n  name: Bob\n  age: 25\n"

        stream = stream_from_string(toon)
        items = list(stream_decoder.decode_stream(stream))
        assert len(items) == 2
        assert items[0] == {"name": "Alice", "age": 30}
        assert items[1] == {"name": "Bob", "age": 25}

    def test_stream_inline_array(self, stream_decoder: StreamDecoder) -> None:
        """Test streaming an inline array (fallback logic)."""
        toon = "[3]: 1, 2, 3"
        stream = stream_from_string(toon)
        items = list(stream_decoder.decode_stream(stream))
        assert items == [1, 2, 3]

    def test_large_stream_simulation(self, stream_decoder: StreamDecoder) -> None:
        """Test streaming with many items."""

        def large_stream() -> Iterator[str]:
            yield "[100]:\n"
            for i in range(100):
                yield f"- {i}\n"

        items = list(stream_decoder.decode_stream(large_stream()))
        assert len(items) == 100
        assert items[0] == 0
        assert items[99] == 99

    def test_adapter_integration(self) -> None:
        """Test integration via ToonFormatAdapter."""
        from toonverter.formats.toon_format import ToonFormatAdapter

        adapter = ToonFormatAdapter()
        toon = """
[2]:
- 1
- 2
"""
        stream = stream_from_string(toon)
        items = list(adapter.decode_stream(stream))
        assert items == [1, 2]

    def test_malformed_array_short(self, stream_decoder: StreamDecoder) -> None:
        """Test array ending prematurely."""
        toon = "[5]:\n- 1\n- 2"
        stream = stream_from_string(toon)
        # Should yield what it can find
        items = list(stream_decoder.decode_stream(stream))
        assert items == [1, 2]

    def test_sparse_array(self, stream_decoder: StreamDecoder) -> None:
        """Test array with empty slots (sparse/nulls)."""
        # Inline array with empty slots: 1, , 3
        toon = "[3]: 1, , 3"
        stream = stream_from_string(toon)
        items = list(stream_decoder.decode_stream(stream))
        # ToonDecoder logic skips empty slots (commas).
        # So [1, , 3] becomes [1, 3].
        # Strict mode would raise error due to length mismatch, but default might not?
        # StreamDecoder currently yields what it finds.
        assert len(items) == 2
        assert items == [1, 3]

    def test_empty_stream(self, stream_decoder: StreamDecoder) -> None:
        """Test decoding an empty stream."""
        stream = stream_from_string("")
        items = list(stream_decoder.decode_stream(stream))
        assert items == []

        stream_ws = stream_from_string("   \n  ")
        items = list(stream_decoder.decode_stream(stream_ws))
        assert items == []

    def test_root_object_fallback(self, stream_decoder: StreamDecoder) -> None:
        """Test fallback to non-streaming decoding for root objects."""
        toon = "name: Alice\nage: 30"
        stream = stream_from_string(toon)
        items = list(stream_decoder.decode_stream(stream))
        # Fallback yields the single parsed object
        assert len(items) == 1
        assert items[0] == {"name": "Alice", "age": 30}
