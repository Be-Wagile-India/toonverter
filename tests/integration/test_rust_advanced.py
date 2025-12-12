import json
import os

import pytest

from toonverter import convert_json_batch, convert_json_directory, convert_toon_batch, decode


# Skip tests if Rust extension is not available
try:
    from toonverter._toonverter_core import decode_toon  # noqa: F401

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust extension not available")
class TestRustAdvancedFeatures:
    @pytest.fixture
    def json_files(self, tmp_path):
        data1 = {"key": "value1", "list": [1, 2]}
        data2 = {"key": "value2", "nested": {"a": 1}}

        f1 = tmp_path / "file1.json"
        f2 = tmp_path / "file2.json"

        with open(f1, "w") as f:
            json.dump(data1, f)
        with open(f2, "w") as f:
            json.dump(data2, f)

        return [str(f1), str(f2)], data1, data2

    def test_convert_json_batch_memory(self, json_files):
        paths, d1, d2 = json_files

        results = convert_json_batch(paths, None)
        assert len(results) == 2

        # Result format: (original_path, content, is_error)
        p1, c1, err1 = results[0]
        _p2, c2, err2 = results[1]

        assert not err1
        assert not err2
        assert p1 == paths[0]

        # Verify content can be decoded back
        # Use python decoder for verification
        obj1 = decode(c1)
        assert obj1 == d1

        obj2 = decode(c2)
        assert obj2 == d2

    def test_convert_json_batch_disk(self, json_files, tmp_path):
        paths, d1, _d2 = json_files
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        results = convert_json_batch(paths, str(out_dir))
        assert len(results) == 2

        _p1, out1, err1 = results[0]
        assert not err1
        assert out1.endswith(".toon")
        assert os.path.exists(out1)

        # Verify file content
        with open(out1) as f:
            c1 = f.read()
            assert decode(c1) == d1

    def test_convert_toon_batch_roundtrip(self, json_files, tmp_path):
        paths, d1, _d2 = json_files

        # 1. JSON -> TOON (Disk)
        out_dir = tmp_path / "toon_out"
        out_dir.mkdir()
        toon_results = convert_json_batch(paths, str(out_dir))
        toon_paths = [r[1] for r in toon_results]

        # 2. TOON -> JSON (Disk)
        json_out_dir = tmp_path / "json_out"
        json_out_dir.mkdir()
        json_results = convert_toon_batch(toon_paths, str(json_out_dir))

        assert len(json_results) == 2
        _p1, out1, err1 = json_results[0]
        assert not err1
        assert out1.endswith(".json")

        # 3. Verify JSON content
        with open(out1) as f:
            loaded = json.load(f)
            assert loaded == d1

    def test_convert_json_directory(self, json_files, tmp_path):
        # json_files are in tmp_path already
        # Create a subdirectory with another file
        sub = tmp_path / "subdir"
        sub.mkdir()
        with open(sub / "sub.json", "w") as f:
            json.dump({"sub": True}, f)

        # Recursive scan
        results = convert_json_directory(str(tmp_path), recursive=True, output_dir=None)

        # Should find 3 files (file1, file2, sub.json)
        assert len(results) == 3

        paths_found = {r[0] for r in results}
        assert str(sub / "sub.json") in paths_found

        # Verify content
        for _p, c, err in results:
            assert not err
            assert len(c) > 0
