from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.decoders.toon_decoder import decode as decode_toon


def test_simple_object_and_items():
    text = """
name: "Datta"
age: 42
active: true
items[3]:
  - 1
  - 2
  - 3
"""
    result = decode_toon(text)
    assert result == {
        "name": "Datta",
        "age": 42,
        "active": True,
        "items": [1, 2, 3],
    }


def test_root_list():
    text = """
- 1
- 2
- 3
"""
    assert decode_toon(text) == [1, 2, 3]


def test_nested_object():
    text = """
user:
  name: "Datta"
  age: 42
  active: true
"""
    assert decode_toon(text) == {"user": {"name": "Datta", "age": 42, "active": True}}


def test_debug_pydantic_decoder_issue():
    input_str = "name: Charlie\nage: 35\nemail: charlie@test.com\nactive: true"

    decoder = ToonDecoder()
    decoded_data = decoder.decode(input_str)

    expected_data = {"name": "Charlie", "age": 35, "email": "charlie@test.com", "active": True}
    assert decoded_data == expected_data
