"""Tests for Infinite Generators and Indefinite Arrays [*]."""

import itertools

from toonverter.decoders.stream_decoder import StreamDecoder
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder


def test_infinite_generator_encoding():
    """Test that an infinite generator can be encoded using [*] header."""
    # ... existing code ...

    # Create an infinite generator but only take 5 items for the test
    infinite_gen = itertools.count(start=1)

    # Wrap it in a generator that yields only the first 5 to avoid infinite loop in test,
    # but tell StreamList it has indefinite length (None)
    def limited_gen():
        for _i in range(5):
            yield next(infinite_gen)

    stream_data = StreamList(iterator=limited_gen(), length=None)
    encoder = ToonStreamEncoder()

    output = "".join(encoder.iterencode(stream_data))

    expected = "[*]:\n- 1\n- 2\n- 3\n- 4\n- 5"
    assert output == expected


def test_indefinite_array_decoding_python():
    """Test that [*] header can be decoded by the Python decoder."""
    toon_data = "[*]:\n- a\n- b\n- c"
    decoder = ToonDecoder()
    result = decoder.decode(toon_data)

    assert result == ["a", "b", "c"]


def test_indefinite_tabular_decoding_python():
    """Test that [*]{fields}: header can be decoded by the Python decoder."""
    toon_data = "[*]{id,name}:\n  1, Alice\n  2, Bob"
    decoder = ToonDecoder()
    result = decoder.decode(toon_data)

    assert result == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


def test_nested_indefinite_stream_encoding():
    """Test encoding a StreamList with indefinite length nested in a dict."""

    def gen():
        yield "val1"
        yield "val2"

    data = {"stream": StreamList(iterator=gen(), length=None)}
    encoder = ToonStreamEncoder()
    output = "".join(encoder.iterencode(data))

    # INDENTATION might be 2 spaces by default
    expected = "stream:\n  [*]:\n\n  - val1\n  - val2"
    assert output == expected


def test_indefinite_stream_decoding():
    """Test that StreamDecoder can handle [*] header."""
    toon_lines = ["[*]:\n", "- item1\n", "- item2\n"]
    decoder = StreamDecoder()
    result = list(decoder.decode_stream(iter(toon_lines)))

    assert result == ["item1", "item2"]
