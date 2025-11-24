"""Integration tests for new CLI commands."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from toonverter.cli.main import cli


class TestCLINewCommands:
    """Test deduplicate and schema-merge commands."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_deduplicate_command(self, runner, tmp_path):
        """Test deduplicate command (mocked)."""
        data = [{"id": 1}, {"id": 2}]
        input_file = tmp_path / "input.json"
        with open(input_file, "w") as f:
            json.dump(data, f)

        output_file = tmp_path / "output.json"

        # Mock toon.deduplicate to return modified data
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
