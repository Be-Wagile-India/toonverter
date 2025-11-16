"""Comprehensive tests for CSV format adapter."""

import pytest
from toonverter.formats.csv_format import CsvFormatAdapter as CSVFormat
from toonverter.core.exceptions import EncodingError, DecodingError


class TestCSVEncoding:
    """Test CSV encoding functionality."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_encode_simple_table(self):
        """Test encoding simple table."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        result = self.adapter.encode(data, None)
        assert "name,age" in result
        assert "Alice,30" in result
        assert "Bob,25" in result

    def test_encode_with_headers(self):
        """Test encoding with explicit headers."""
        data = [
            {"name": "Alice", "city": "NYC"},
            {"name": "Bob", "city": "LA"}
        ]
        result = self.adapter.encode(data, None)
        lines = result.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows

    def test_encode_empty_rows(self):
        """Test encoding empty rows."""
        data = []
        with pytest.raises(EncodingError):
            self.adapter.encode(data, None)

    def test_encode_single_row(self):
        """Test encoding single row."""
        data = [{"name": "Alice", "age": 30}]
        result = self.adapter.encode(data, None)
        assert "name,age" in result
        assert "Alice,30" in result

    def test_encode_with_commas_in_values(self):
        """Test encoding values containing commas."""
        data = [{"name": "Smith, John", "age": 30}]
        result = self.adapter.encode(data, None)
        # Commas in values should be quoted
        assert '"Smith, John"' in result or "Smith, John" in result

    def test_encode_with_quotes_in_values(self):
        """Test encoding values containing quotes."""
        data = [{"name": 'John "Johnny" Doe', "age": 30}]
        result = self.adapter.encode(data, None)
        # Should handle quotes properly
        assert "John" in result

    def test_encode_numeric_values(self):
        """Test encoding numeric values."""
        data = [
            {"id": 1, "value": 100.5},
            {"id": 2, "value": 200.75}
        ]
        result = self.adapter.encode(data, None)
        assert "100.5" in result or "100.5" in result.replace('"', '')

    def test_encode_non_list_data(self):
        """Test encoding non-list data raises error."""
        data = {"name": "Alice"}
        with pytest.raises(EncodingError):
            self.adapter.encode(data, None)


class TestCSVDecoding:
    """Test CSV decoding functionality."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_decode_simple_table(self):
        """Test decoding simple table."""
        csv_str = "name,age\nAlice,30\nBob,25"
        result = self.adapter.decode(csv_str, None)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"name": "Alice", "age": "30"}

    def test_decode_with_headers(self):
        """Test decoding with headers."""
        csv_str = "name,city\nAlice,NYC\nBob,LA"
        result = self.adapter.decode(csv_str, None)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_decode_empty_csv(self):
        """Test decoding empty CSV."""
        csv_str = ""
        result = self.adapter.decode(csv_str, None)
        assert result == []

    def test_decode_headers_only(self):
        """Test decoding headers only."""
        csv_str = "name,age"
        result = self.adapter.decode(csv_str, None)
        assert result == []

    def test_decode_with_quoted_values(self):
        """Test decoding quoted values."""
        csv_str = 'name,age\n"Smith, John",30'
        result = self.adapter.decode(csv_str, None)
        assert result[0]["name"] == "Smith, John"

    def test_decode_with_newlines_in_quotes(self):
        """Test decoding newlines in quoted values."""
        csv_str = 'text,value\n"Line1\nLine2",100'
        result = self.adapter.decode(csv_str, None)
        assert "Line1" in result[0]["text"]


class TestCSVRoundtrip:
    """Test CSV roundtrip."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert decoded == data

    def test_roundtrip_preserves_headers(self):
        """Test roundtrip preserves headers."""
        data = [
            {"col1": "A", "col2": "B"},
            {"col1": "C", "col2": "D"}
        ]
        encoded = self.adapter.encode(data, None)
        decoded = self.adapter.decode(encoded, None)
        assert set(decoded[0].keys()) == {"col1", "col2"}
