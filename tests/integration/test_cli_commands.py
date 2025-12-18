"""Integration tests for all CLI commands."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from toonverter.cli.main import cli


class TestCLICommands:
    """Test all CLI commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def simple_json_file(self, tmp_path):
        data = {"name": "Alice", "age": 30}
        file_path = tmp_path / "input.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path

    @pytest.fixture
    def simple_toon_file(self, tmp_path):
        data = "name: Alice\nage: 30"
        file_path = tmp_path / "input.toon"
        with open(file_path, "w") as f:
            f.write(data)
        return file_path

    @pytest.fixture
    def large_json_file(self, tmp_path):
        data = [{"id": i, "value": f"item_{i}"} for i in range(100)]
        file_path = tmp_path / "large_input.json"
        with open(file_path, "w") as f:
            json.dump(data, f)
        return file_path

    @pytest.fixture
    def large_toon_file(self, tmp_path):
        data = "\n".join([f"id: {i}\nvalue: item_{i}" for i in range(100)])
        file_path = tmp_path / "large_input.toon"
        with open(file_path, "w") as f:
            f.write(data)
        return file_path

    def test_convert_command_json_to_toon(self, runner, simple_json_file, tmp_path):
        """Test convert command from JSON to TOON."""
        output_file = tmp_path / "output.toon"
        result = runner.invoke(
            cli,
            ["convert", str(simple_json_file), str(output_file), "--from", "json", "--to", "toon"],
        )
        assert result.exit_code == 0
        assert "✓ Converted" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert "name: Alice" in content
            assert "age: 30" in content

    def test_convert_command_toon_to_json(self, runner, simple_toon_file, tmp_path):
        """Test convert command from TOON to JSON."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            cli,
            ["convert", str(simple_toon_file), str(output_file), "--from", "toon", "--to", "json"],
        )
        assert result.exit_code == 0
        assert "✓ Converted" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            content = json.load(f)
            assert content["name"] == "Alice"
            assert content["age"] == 30

    def test_convert_command_stream_jsonl_to_jsonl(self, runner, tmp_path):
        """Test convert command with streaming for JSONL."""
        input_file = tmp_path / "input.jsonl"
        with open(input_file, "w") as f:
            f.write('{"a": 1}\n')
            f.write('{"b": 2}\n')
        output_file = tmp_path / "output.jsonl"

        # Mock rich.progress to avoid ImportError if not installed
        with patch("rich.progress.Progress") as mock_progress:
            mock_progress.return_value.__enter__.return_value.add_task.return_value = 0
            mock_progress.return_value.__enter__.return_value.update.return_value = None

            result = runner.invoke(
                cli,
                [
                    "convert",
                    str(input_file),
                    str(output_file),
                    "--from",
                    "jsonl",
                    "--to",
                    "jsonl",
                    "--stream",
                    "--compact",  # Added compact flag
                ],
            )
            assert result.exit_code == 0
            assert "✓ Converted" in result.output
            assert output_file.exists()
            with open(output_file) as f:
                content = f.read()
                assert '{"a":1}\n' in content  # Expect compact output now
                assert '{"b":2}\n' in content

    def test_encode_command(self, runner, simple_json_file, tmp_path):
        """Test encode command."""
        output_file = tmp_path / "output.toon"
        result = runner.invoke(cli, ["encode", str(simple_json_file), "-o", str(output_file)])
        assert result.exit_code == 0
        assert "✓ Encoded to" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            content = f.read()
            assert "name: Alice" in content

    def test_decode_command(self, runner, simple_toon_file, tmp_path):
        """Test decode command."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            cli, ["decode", str(simple_toon_file), "-o", str(output_file), "--format", "json"]
        )
        assert result.exit_code == 0
        assert "✓ Decoded to" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            content = json.load(f)
            assert content["name"] == "Alice"

    def test_analyze_command(self, runner, simple_json_file):
        """Test analyze command."""
        result = runner.invoke(cli, ["analyze", str(simple_json_file)])
        assert result.exit_code == 0
        assert "Token Usage Comparison" in result.output  # Corrected assertion string
        assert "json" in result.output
        assert "toon" in result.output

    def test_formats_command(self, runner):
        """Test formats command."""
        result = runner.invoke(cli, ["formats"])
        assert result.exit_code == 0
        assert "Supported formats:" in result.output
        assert "• json" in result.output
        assert "• toon" in result.output

    def test_infer_command(self, runner, simple_json_file, tmp_path):
        """Test infer command."""
        output_file = tmp_path / "schema.json"
        result = runner.invoke(cli, ["infer", str(simple_json_file), "-o", str(output_file)])
        assert result.exit_code == 0
        assert "✓ Schema saved to" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            schema = json.load(f)
            assert (
                schema["type"] == "array"
            )  # Corrected assertion to expect array for streamed infer
            assert "name" in schema["items"]["properties"]  # Nested under items for array

    def test_validate_command_success(self, runner, simple_json_file, tmp_path):
        """Test validate command success."""
        schema_file = tmp_path / "schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        result = runner.invoke(
            cli, ["validate", str(simple_json_file), "--schema", str(schema_file)]
        )
        assert result.exit_code == 0
        assert "✓ Data is valid" in result.output

    def test_validate_command_failure(self, runner, tmp_path):  # Changed fixture
        """Test validate command failure."""
        # Create input data that explicitly violates the schema
        invalid_data_file = tmp_path / "invalid_data.json"
        with open(invalid_data_file, "w") as f:
            json.dump({"name": "Alice"}, f)  # Missing 'age'

        schema_file = tmp_path / "schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
            "required": ["name", "age"],
        }
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        result = runner.invoke(
            cli, ["validate", str(invalid_data_file), "--schema", str(schema_file)]
        )
        assert result.exit_code == 1
        assert "✗ Validation failed" in result.output
        assert "Missing required field 'age'" in result.output

    def test_diff_command(self, runner, tmp_path):
        """Test diff command."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        with open(file1, "w") as f:
            json.dump({"a": 1, "b": 2}, f)
        with open(file2, "w") as f:
            json.dump({"a": 1, "b": 3}, f)

        result = runner.invoke(cli, ["diff", str(file1), str(file2), "--format", "text"])
        assert result.exit_code == 1  # Exit code 1 for differences
        assert "~ $.b: 2 -> 3" in result.output  # Corrected assertion string

    def test_compress_command(self, runner, simple_json_file, tmp_path):
        """Test compress command."""
        output_file = tmp_path / "compressed.json"
        result = runner.invoke(cli, ["compress", str(simple_json_file), "-o", str(output_file)])
        assert result.exit_code == 0
        assert "✓ Compressed to" in result.output
        assert output_file.exists()

    def test_decompress_command(self, runner, simple_json_file, tmp_path):
        """Test decompress command."""
        # First compress a file
        compressed_file = tmp_path / "compressed.json"
        compress_result = runner.invoke(
            cli, ["compress", str(simple_json_file), "-o", str(compressed_file)]
        )
        assert compress_result.exit_code == 0

        output_file = tmp_path / "decompressed.json"
        result = runner.invoke(cli, ["decompress", str(compressed_file), "-o", str(output_file)])
        assert result.exit_code == 0
        assert "✓ Decompressed to" in result.output
        assert output_file.exists()
        with open(output_file) as f:
            content = json.load(f)
            assert content["name"] == "Alice"

    def test_deduplicate_command(self, runner, tmp_path):
        """Test deduplicate command (mocked)."""
        data = [{"id": 1}, {"id": 2}]
        input_file = tmp_path / "input.json"
        with open(input_file, "w") as f:
            json.dump(data, f)

        output_file = tmp_path / "output.json"

        # Mock toonverter.deduplicate to return modified data
        with patch("toonverter.deduplicate") as mock_dedup:
            mock_dedup.return_value = [{"id": 1}]

            result = runner.invoke(
                cli,
                [
                    "deduplicate",
                    str(input_file),
                    "--output",
                    str(output_file),
                    "--model",
                    "test-model",
                    "--threshold",
                    "0.8",
                ],
            )

            assert result.exit_code == 0
            assert "Deduplicated data saved" in result.output

            # Verify arguments passed to deduplicate
            mock_dedup.assert_called_once()
            _args, kwargs = mock_dedup.call_args
            assert kwargs["model_name"] == "test-model"
            assert kwargs["threshold"] == 0.8

    def test_schema_merge_command(self, runner, tmp_path):
        """Test schema-merge command."""
        s1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
        s2 = {"type": "object", "properties": {"b": {"type": "string"}}}

        p1 = tmp_path / "s1.json"
        p2 = tmp_path / "s2.json"

        with open(p1, "w") as f:
            json.dump(s1, f)
        with open(p2, "w") as f:
            json.dump(s2, f)

        output_file = tmp_path / "merged.json"

        result = runner.invoke(cli, ["schema-merge", str(p1), str(p2), "-o", str(output_file)])
        assert result.exit_code == 0
        assert "Merged schema saved" in result.output

        with open(output_file) as f:
            merged = json.load(f)

        assert "a" in merged["properties"]
        assert "b" in merged["properties"]

    def test_schema_merge_stdout(self, runner, tmp_path):
        """Test schema-merge command output to stdout."""
        s1 = {"type": "string"}
        s2 = {"type": "string"}

        p1 = tmp_path / "s1.json"
        p2 = tmp_path / "s2.json"

        with open(p1, "w") as f:
            json.dump(s1, f)
        with open(p2, "w") as f:
            json.dump(s2, f)

        result = runner.invoke(cli, ["schema-merge", str(p1), str(p2)])
        assert result.exit_code == 0
        assert '"type": "string"' in result.output

    def test_batch_convert_json_command(self, runner, large_json_file, tmp_path):
        """Test batch-convert-json command."""
        output_dir = tmp_path / "output_json_batch"
        output_dir.mkdir()

        # Mock the underlying Rust function
        with patch("toonverter.convert_json_batch") as mock_batch:
            mock_batch.return_value = [
                (str(large_json_file), "id: 0\nvalue: item_0", False),
                (str(large_json_file), "Conversion Error", True),
            ]
            result = runner.invoke(
                cli, ["batch-convert-json", str(large_json_file), "-o", str(output_dir)]
            )
            assert result.exit_code == 1  # Expect failure due to one error
            assert "✓ Converted" in result.output
            assert "✗ Failed to convert" in result.output
            assert "Summary: 1 succeeded, 1 failed." in result.output
            mock_batch.assert_called_once_with([str(large_json_file)], str(output_dir))

    def test_batch_convert_json_command_stdout(self, runner, large_json_file):
        """Test batch-convert-json command output to stdout."""
        with patch("toonverter.convert_json_batch") as mock_batch:
            mock_batch.return_value = [
                (str(large_json_file), "id: 0\nvalue: item_0", False),
            ]
            result = runner.invoke(cli, ["batch-convert-json", str(large_json_file)])
            assert result.exit_code == 0
            assert "---" in result.output
            assert "id: 0" in result.output
            assert "Summary: 1 succeeded, 0 failed." in result.output
            mock_batch.assert_called_once_with([str(large_json_file)], None)

    def test_batch_convert_toon_command(self, runner, large_toon_file, tmp_path):
        """Test batch-convert-toon command."""
        output_dir = tmp_path / "output_toon_batch"
        output_dir.mkdir()

        # Mock the underlying Rust function
        with patch("toonverter.convert_toon_batch") as mock_batch:
            mock_batch.return_value = [
                (str(large_toon_file), '{"id": 0, "value": "item_0"}', False)
            ]
            result = runner.invoke(
                cli, ["batch-convert-toon", str(large_toon_file), "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            assert "✓ Converted" in result.output
            assert "Summary: 1 succeeded, 0 failed." in result.output
            mock_batch.assert_called_once_with([str(large_toon_file)], str(output_dir))

    def test_convert_dir_json_command(self, runner, tmp_path):
        """Test convert-dir-json command."""
        input_dir = tmp_path / "input_dir"
        input_dir.mkdir()
        (input_dir / "file1.json").write_text('{"a":1}')
        (input_dir / "file2.json").write_text('{"b":2}')

        output_dir = tmp_path / "output_dir_json"
        output_dir.mkdir()

        # Mock the underlying Rust function
        with patch("toonverter.convert_json_directory") as mock_dir:
            mock_dir.return_value = [
                (str(input_dir / "file1.json"), "a: 1", False),
                (str(input_dir / "file2.json"), "b: 2", False),
            ]
            result = runner.invoke(cli, ["convert-dir-json", str(input_dir), "-o", str(output_dir)])
            assert result.exit_code == 0
            assert "✓ Converted" in result.output
            assert "Summary: 2 succeeded, 0 failed." in result.output
            mock_dir.assert_called_once_with(str(input_dir), False, str(output_dir))

    def test_convert_dir_json_recursive_command(self, runner, tmp_path):
        """Test convert-dir-json command with recursive flag."""
        input_dir = tmp_path / "input_dir_rec"
        (input_dir / "subdir").mkdir(parents=True)
        (input_dir / "subdir" / "file3.json").write_text('{"c":3}')

        output_dir = tmp_path / "output_dir_rec_json"
        output_dir.mkdir()

        with patch("toonverter.convert_json_directory") as mock_dir:
            mock_dir.return_value = [(str(input_dir / "subdir" / "file3.json"), "c: 3", False)]
            result = runner.invoke(
                cli, ["convert-dir-json", str(input_dir), "-r", "-o", str(output_dir)]
            )
            assert result.exit_code == 0
            assert "✓ Converted" in result.output
            assert "Summary: 1 succeeded, 0 failed." in result.output
            mock_dir.assert_called_once_with(str(input_dir), True, str(output_dir))
