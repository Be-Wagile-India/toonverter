"""Tests for the Streaming Encoder."""

from typing import Any

import pytest

from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder
from toonverter.encoders.toon_encoder import ToonEncoder


@pytest.fixture
def stream_encoder() -> ToonStreamEncoder:
    return ToonStreamEncoder()


@pytest.fixture
def standard_encoder() -> ToonEncoder:
    return ToonEncoder()


def assert_encoding_match(data: Any, stream_enc: ToonStreamEncoder, std_enc: ToonEncoder) -> None:
    """Assert that streaming encoding matches standard encoding exactly."""
    # Standard result
    expected = std_enc.encode(data)

    # Stream result (joined)
    stream_gen = stream_enc.iterencode(data)
    actual = "".join(stream_gen)

    assert actual == expected


class TestToonStreamEncoder:
    """Test suite for ToonStreamEncoder."""

    def test_primitives(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test encoding of primitive values."""
        assert_encoding_match(42, stream_encoder, standard_encoder)
        assert_encoding_match(3.14, stream_encoder, standard_encoder)
        assert_encoding_match("hello world", stream_encoder, standard_encoder)
        assert_encoding_match(True, stream_encoder, standard_encoder)
        assert_encoding_match(None, stream_encoder, standard_encoder)

    def test_simple_dict(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test encoding of simple dictionary."""
        data = {"name": "Alice", "age": 30}
        assert_encoding_match(data, stream_encoder, standard_encoder)

    def test_nested_dict(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test encoding of nested dictionary."""
        data = {"user": {"name": "Bob", "details": {"age": 25, "active": True}}, "meta": "data"}
        assert_encoding_match(data, stream_encoder, standard_encoder)

    def test_empty_structures(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test encoding of empty structures."""
        assert_encoding_match({}, stream_encoder, standard_encoder)
        assert_encoding_match([], stream_encoder, standard_encoder)
        assert_encoding_match(
            {"empty_list": [], "empty_dict": {}}, stream_encoder, standard_encoder
        )

    def test_list_basic(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test encoding of simple list."""
        data = [1, 2, 3, "four"]
        # Note: Standard encoder might choose INLINE for small lists.
        # Stream encoder forces LIST form.
        # So we cannot compare exact string match if standard chooses INLINE.
        # We should check if standard encoder can be forced to LIST form or just verify valid TOON.
        # For this test, we accept that they might differ in whitespace/format but should be semantically valid.

        # Actually, let's verify stream output structure directly for lists
        # since we know StreamEncoder forces LIST form.
        stream_gen = stream_encoder.iterencode(data)
        actual = "".join(stream_gen)
        # Expected List Form:
        # [4]:
        # - 1
        # - 2
        # - 3
        # - four
        assert "[4]:" in actual
        assert "- 1" in actual
        assert "- four" in actual

    def test_list_nested_objects(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test list containing objects."""
        data = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
        stream_gen = stream_encoder.iterencode(data)
        actual = "".join(stream_gen)

        # Verify structure
        # [2]:
        # -
        # >   id: 1
        # >   val: a
        # -
        # >   id: 2
        # >   val: b

        assert "[2]:" in actual
        assert "  id: 1" in actual  # Indented key

    def test_deeply_nested_structure(
        self, stream_encoder: ToonStreamEncoder, standard_encoder: ToonEncoder
    ) -> None:
        """Test deeply nested structure to verify no recursion error."""
        # Create a deep structure
        depth = 200  # Python recursion limit is usually 1000, but safer to test reasonably deep
        data = {"level_0": "start"}
        current = data
        for i in range(1, depth):
            new_node = {"level": i}
            current["next"] = new_node
            current = new_node

        # Should not raise error
        stream_gen = stream_encoder.iterencode(data)
        # Consume generator
        for _ in stream_gen:
            pass

    def test_adapter_integration(self) -> None:
        """Test integration with ToonFormatAdapter."""
        from toonverter.formats.toon_format import ToonFormatAdapter

        adapter = ToonFormatAdapter()
        assert adapter.supports_streaming()

        data = {"key": "value"}
        stream = adapter.encode_stream(data)
        result = "".join(stream)
        assert "key: value" in result

    def test_stream_list_input(self, stream_encoder: ToonStreamEncoder) -> None:
        """Test encoding StreamList input."""
        data_iter = iter([1, 2, 3])
        stream_list = StreamList(iterator=data_iter, length=3)

        stream_gen = stream_encoder.iterencode(stream_list)
        result = "".join(stream_gen)

        assert "[3]:" in result
        assert "- 1" in result
        assert "- 3" in result

    def test_nested_stream_list(self, stream_encoder: ToonStreamEncoder) -> None:
        """Test nested StreamList."""
        inner_iter = iter(["a", "b"])
        inner_stream = StreamList(iterator=inner_iter, length=2)

        data = [inner_stream, "c"]

        stream_gen = stream_encoder.iterencode(data)
        result = "".join(stream_gen)

        # Expected:
        # [2]:
        # - [2]:
        #   - a
        #   - b
        # - c

        assert "[2]:" in result
        assert "- [2]:" in result
        assert "  - a" in result
        assert "- c" in result

    def test_empty_stream_list(self, stream_encoder: ToonStreamEncoder) -> None:
        """Test empty StreamList."""
        stream_list = StreamList(iterator=iter([]), length=0)
        stream_gen = stream_encoder.iterencode(stream_list)
        result = "".join(stream_gen)
        assert "[0]:" in result
