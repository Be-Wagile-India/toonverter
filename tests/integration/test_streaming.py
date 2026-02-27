import json

import pytest

from toonverter import convert_stream, load_stream


@pytest.fixture
def jsonl_file(tmp_path):
    f = tmp_path / "data.jsonl"
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 3, "name": "Charlie"}]
    with f.open("w") as file:
        for item in data:
            file.write(json.dumps(item) + "\n")
    return f


@pytest.fixture
def json_array_file(tmp_path):
    f = tmp_path / "data.json"
    data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}, {"id": 3, "name": "Charlie"}]
    with f.open("w") as file:
        json.dump(data, file)
    return f


def test_load_stream_jsonl(jsonl_file):
    stream = load_stream(str(jsonl_file), format="jsonl")
    items = list(stream)
    assert len(items) == 3
    assert items[0]["name"] == "Alice"
    assert items[2]["name"] == "Charlie"


def test_load_stream_json_array(json_array_file):
    # This might require ijson, or fallback to file read if small?
    # Our implementation tries ijson then fallback.
    # We should ensure it works either way.
    stream = load_stream(str(json_array_file), format="json")
    items = list(stream)
    assert len(items) == 3
    assert items[1]["name"] == "Bob"


def test_convert_stream_jsonl_to_jsonl(jsonl_file, tmp_path):
    target = tmp_path / "output.jsonl"
    convert_stream(str(jsonl_file), str(target), from_format="jsonl", to_format="jsonl")

    assert target.exists()
    lines = target.read_text().strip().split("\n")
    assert len(lines) == 3
    assert json.loads(lines[0])["name"] == "Alice"


def test_convert_stream_json_to_jsonl(json_array_file, tmp_path):
    target = tmp_path / "output_from_array.jsonl"
    convert_stream(str(json_array_file), str(target), from_format="json", to_format="jsonl")

    assert target.exists()
    lines = target.read_text().strip().split("\n")
    assert len(lines) == 3
    assert json.loads(lines[1])["name"] == "Bob"


def test_convert_stream_jsonl_to_json(jsonl_file, tmp_path):
    target = tmp_path / "output_array.json"
    convert_stream(str(jsonl_file), str(target), from_format="jsonl", to_format="json")

    assert target.exists()
    data = json.loads(target.read_text())
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[2]["name"] == "Charlie"
