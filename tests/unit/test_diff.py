"""Tests for ToonDiff."""

import json
from unittest.mock import MagicMock, patch

import pytest

from toonverter.differ import ChangeType, DiffChange, DiffFormatter, DiffResult, ToonDiffer


class TestToonDiffer:
    def test_diff_identical_dicts(self):
        differ = ToonDiffer()
        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 2, "a": 1}  # Different order
        result = differ.diff(obj1, obj2)
        assert result.match
        assert len(result.changes) == 0

    def test_diff_added_key(self):
        differ = ToonDiffer()
        obj1 = {"a": 1}
        obj2 = {"a": 1, "b": 2}
        result = differ.diff(obj1, obj2)
        assert not result.match
        assert len(result.changes) == 1
        change = result.changes[0]
        assert change.type == ChangeType.ADD
        assert change.path == "$.b"
        assert change.new_value == 2

    def test_diff_removed_key(self):
        differ = ToonDiffer()
        obj1 = {"a": 1, "b": 2}
        obj2 = {"a": 1}
        result = differ.diff(obj1, obj2)
        assert not result.match
        assert len(result.changes) == 1
        change = result.changes[0]
        assert change.type == ChangeType.REMOVE
        assert change.path == "$.b"
        assert change.old_value == 2

    def test_diff_changed_value(self):
        differ = ToonDiffer()
        obj1 = {"a": 1}
        obj2 = {"a": 2}
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.CHANGE
        assert change.path == "$.a"
        assert change.old_value == 1
        assert change.new_value == 2

    def test_diff_nested_dict(self):
        differ = ToonDiffer()
        obj1 = {"user": {"name": "Alice", "age": 30}}
        obj2 = {"user": {"name": "Bob", "age": 30}}
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.CHANGE
        assert change.path == "$.user.name"
        assert change.old_value == "Alice"
        assert change.new_value == "Bob"

    def test_diff_list_add(self):
        differ = ToonDiffer()
        obj1 = [1, 2]
        obj2 = [1, 2, 3]
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.ADD
        assert change.path == "$[2]"
        assert change.new_value == 3

    def test_diff_list_remove(self):
        differ = ToonDiffer()
        obj1 = [1, 2, 3]
        obj2 = [1, 2]
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.REMOVE
        assert change.path == "$[2]"
        assert change.old_value == 3

    def test_diff_list_change(self):
        differ = ToonDiffer()
        obj1 = [1, 2]
        obj2 = [1, 3]
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.CHANGE
        assert change.path == "$[1]"
        assert change.old_value == 2
        assert change.new_value == 3

    def test_diff_type_change(self):
        differ = ToonDiffer()
        obj1 = {"a": 1}
        obj2 = {"a": "1"}
        result = differ.diff(obj1, obj2)
        assert not result.match
        change = result.changes[0]
        assert change.type == ChangeType.TYPE_CHANGE
        assert change.path == "$.a"
        assert change.old_value == "int"
        assert change.new_value == "str"


class TestDiffFormatter:
    @pytest.fixture
    def sample_result(self):
        changes = [
            DiffChange("$.add", ChangeType.ADD, new_value="new"),
            DiffChange("$.rem", ChangeType.REMOVE, old_value="old"),
            DiffChange("$.chg", ChangeType.CHANGE, old_value="old", new_value="new"),
            DiffChange("$.type", ChangeType.TYPE_CHANGE, old_value="int", new_value="str"),
        ]
        return DiffResult(changes=changes)

    def test_format_text_no_changes(self):
        formatter = DiffFormatter()
        result = DiffResult(changes=[])
        output = formatter.format_text(result)
        assert "No differences found" in output

    def test_format_text_with_changes(self, sample_result):
        formatter = DiffFormatter()
        output = formatter.format_text(sample_result)
        assert "Differences found:" in output
        assert "+ $.add: new" in output
        assert "- $.rem: old" in output
        assert "~ $.chg: old -> new" in output
        assert "! $.type: Type changed from int to str" in output

    def test_format_json(self, sample_result):
        formatter = DiffFormatter()
        output = formatter.format_json(sample_result)
        data = json.loads(output)
        assert data["match"] is False
        assert len(data["changes"]) == 4
        assert data["changes"][0]["type"] == "add"

    @patch("toonverter.differ.formatter.Console")
    @patch("toonverter.differ.formatter.RICH_AVAILABLE", True)
    def test_print_rich_match(self, mock_console_cls):
        mock_console = MagicMock()
        mock_console_cls.return_value = mock_console

        formatter = DiffFormatter()
        result = DiffResult(changes=[])
        formatter.print_rich(result)

        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0]
        assert "No differences found" in str(args[0])

    @patch("toonverter.differ.formatter.Console")
    @patch("toonverter.differ.formatter.RICH_AVAILABLE", True)
    def test_print_rich_changes(self, mock_console_cls, sample_result):
        mock_console = MagicMock()
        mock_console_cls.return_value = mock_console

        formatter = DiffFormatter()
        formatter.print_rich(sample_result)

        mock_console.print.assert_called_once()
        # Verify a table was passed
        from rich.table import Table

        assert isinstance(mock_console.print.call_args[0][0], Table)

    @patch("builtins.print")
    @patch("toonverter.differ.formatter.RICH_AVAILABLE", False)
    def test_print_rich_fallback(self, mock_print, sample_result):
        formatter = DiffFormatter()
        formatter.print_rich(sample_result)
        mock_print.assert_called_once()
        assert "Differences found" in mock_print.call_args[0][0]
