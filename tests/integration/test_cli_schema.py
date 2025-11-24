"""Integration tests for CLI Schema commands."""

import json

import pytest
from click.testing import CliRunner

from toonverter.cli.main import cli


class TestCLISchema:
    """Test schema inference and validation via CLI."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def sample_data(self, tmp_path):
        """Create sample data file."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        path = tmp_path / "data.json"
        with open(path, "w") as f:
            json.dump(data, f)
        return str(path)

    def test_infer_command(self, runner, sample_data):
        """Test infer command."""
        result = runner.invoke(cli, ["infer", sample_data])
        assert result.exit_code == 0
        assert "array" in result.output
        assert "properties" in result.output
        assert "age" in result.output

    def test_validate_command_success(self, runner, sample_data, tmp_path):
        """Test validate command success."""
        # First infer and save schema
        schema_path = tmp_path / "schema.json"
        runner.invoke(cli, ["infer", sample_data, "--output", str(schema_path)])

        # Then validate
        result = runner.invoke(cli, ["validate", sample_data, "--schema", str(schema_path)])
        assert result.exit_code == 0
        assert "Data is valid" in result.output

    def test_validate_command_failure(self, runner, tmp_path):
        """Test validate command failure."""
        # Create schema expecting string
        schema = {"type": "string"}
        schema_path = tmp_path / "string_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema, f)

        # Create invalid data (integer)
        data_path = tmp_path / "bad_data.json"
        with open(data_path, "w") as f:
            json.dump(42, f)

        result = runner.invoke(cli, ["validate", str(data_path), "--schema", str(schema_path)])
        assert result.exit_code == 1
        assert "Validation failed" in result.output
        assert "Expected string, got int" in result.output
