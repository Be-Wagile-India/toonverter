"""Comprehensive tests for CSV format adapter."""

import pytest

from toonverter.core.exceptions import DecodingError, EncodingError
from toonverter.core.types import DecodeOptions, EncodeOptions
from toonverter.formats.csv_format import CsvFormatAdapter as CSVFormat


# Guaranteed error-inducing string for testing strict/non-strict decoding
# Using an unclosed quoted field at the end of the string to reliably trigger a csv.Error.
ERROR_CSV_STR = 'col1,col2\nA,"B'


class TestCSVEncoding:
    """Test CSV encoding functionality."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_encode_simple_table(self):
        """Test encoding list of dictionaries with default settings."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        result = self.adapter.encode(data, None)
        assert "name,age" in result
        assert "Alice,30" in result
        assert "Bob,25" in result

    def test_encode_list_of_lists(self):
        """Test encoding a list of lists (tabular data without headers)."""
        data = [["A", 1], ["B", 2]]
        result = self.adapter.encode(data, None)
        # Using splitlines for robust line ending check
        assert result.splitlines() == ["A,1", "B,2"]

    def test_encode_with_custom_delimiter(self):
        """Test encoding using a custom delimiter (e.g., semicolon)."""
        data = [{"name": "Alice", "age": 30}]
        options = EncodeOptions(delimiter=";")
        result = self.adapter.encode(data, options)
        assert "name;age" in result
        assert "Alice;30" in result

    def test_encode_sort_keys(self):
        """Test encoding with sort_keys=True option."""
        data = [{"c": 3, "a": 1, "b": 2}]
        options = EncodeOptions(sort_keys=True)
        result = self.adapter.encode(data, options)
        # Fix: Use splitlines to reliably assert against content without trailing \r
        assert result.splitlines()[0] == "a,b,c"

    def test_encode_empty_rows(self):
        """Test encoding empty list data raises EncodingError."""
        data = []
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "non-empty list data" in str(excinfo.value)

    def test_encode_non_tabular_list_data(self):
        """Test encoding a list that is neither list of dicts nor list of lists raises error."""
        data = [1, 2, 3]  # List of integers
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "list of dictionaries or list of lists" in str(excinfo.value)

    def test_encode_non_list_data(self):
        """Test encoding non-list data raises EncodingError."""
        data = {"name": "Alice"}
        with pytest.raises(EncodingError):
            self.adapter.encode(data, None)

    def test_encode_internal_encoding_failure(self):
        """
        Test encoding failure inside the try block (e.g., non-stringifiable/bad data types).
        We force a TypeError by providing a dict where not all keys match, which DictWriter
        cannot handle correctly without extensive setup.
        """
        data = [{"a": 1}, {"b": 2}]
        with pytest.raises(EncodingError) as excinfo:
            self.adapter.encode(data, None)
        assert "Failed to encode to CSV" in str(excinfo.value)


class TestCSVDecoding:
    """Test CSV decoding functionality."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_decode_simple_table(self):
        """Test decoding simple table. Type inference is ON by default."""
        csv_str = "name,age\nAlice,30\nBob,25"
        # Explicitly pass DecodeOptions() to ensure default type_inference=True is active
        result = self.adapter.decode(csv_str, DecodeOptions())
        assert isinstance(result, list)
        assert len(result) == 2
        # Expected: integer 30 due to default type_inference=True
        assert result[0] == {"name": "Alice", "age": 30}

    def test_decode_with_custom_delimiter(self):
        """Test decoding with a custom delimiter. Type inference is ON by default."""
        csv_str = "name;age\nAlice;30\nBob;25"
        # Explicitly pass DecodeOptions with delimiter to ensure type_inference=True is active
        options = DecodeOptions(delimiter=";")
        result = self.adapter.decode(csv_str, options)
        # Expected: integer 30 due to default type_inference=True
        assert result[0] == {"name": "Alice", "age": 30}

    def test_decode_type_inference(self):
        """Test decoding with type inference, covering all infer_types branches."""
        csv_str = "bool_val,int_val,float_val,empty_val,str_val\ntrue,10,-10.5,,Test String"
        options = DecodeOptions(type_inference=True)
        result = self.adapter.decode(csv_str, options)

        row = result[0]
        assert row["bool_val"] is True
        assert row["int_val"] == 10
        assert row["float_val"] == -10.5
        assert row["empty_val"] is None
        assert row["str_val"] == "Test String"

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
        # Explicitly disable inference for this test to assert against raw string values
        options = DecodeOptions(type_inference=False)
        result = self.adapter.decode(csv_str, options)
        assert result[0]["name"] == "Smith, John"
        assert result[0]["age"] == "30"

    def test_decode_with_newlines_in_quotes(self):
        """Test decoding newlines in quoted values."""
        csv_str = 'text,value\n"Line1\nLine2",100'
        # Explicitly disable inference for clear string testing
        options = DecodeOptions(type_inference=False)
        result = self.adapter.decode(csv_str, options)
        assert result[0]["text"] == "Line1\nLine2"

    def test_decode_strict_mode_failure(self):
        """Test decoding badly formed CSV in strict mode raises DecodingError."""
        # This test now relies on ERROR_CSV_STR (unclosed quote) reliably triggering a csv.Error
        options = DecodeOptions(strict=True)
        with pytest.raises(DecodingError) as excinfo:
            self.adapter.decode(ERROR_CSV_STR, options)
        assert "Failed to decode CSV" in str(excinfo.value)

    def test_decode_non_strict_mode_failure(self):
        """Test decoding badly formed CSV in non-strict mode returns the raw string."""
        # This test now relies on ERROR_CSV_STR (unclosed quote) reliably triggering a csv.Error
        options = DecodeOptions(strict=False)
        result = self.adapter.decode(ERROR_CSV_STR, options)
        # Should return the original string because of the caught csv.Error
        assert result == ERROR_CSV_STR


class TestCSVValidation:
    """Test CSV validation functionality."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_validate_valid_csv(self):
        """Test validation for a simple, valid CSV string."""
        csv_str = "name,age\nAlice,30\nBob,25"
        assert self.adapter.validate(csv_str) is True

    def test_validate_empty_string(self):
        """Test validation for an empty string (should be considered valid CSV, returning empty list)."""
        csv_str = ""
        assert self.adapter.validate(csv_str) is True

    def test_validate_invalid_csv(self):
        """Test validation for a string that causes a csv.Error (e.g., illegal quote)."""
        # This test now relies on ERROR_CSV_STR (unclosed quote) reliably triggering a csv.Error
        assert self.adapter.validate(ERROR_CSV_STR) is False


class TestCSVRoundtrip:
    """Test CSV roundtrip."""

    def setup_method(self):
        """Set up CSV format adapter."""
        self.adapter = CSVFormat()

    def test_roundtrip_simple(self):
        """Test simple roundtrip."""
        data = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        encoded = self.adapter.encode(data, None)
        # Explicitly pass DecodeOptions() to ensure default type_inference=True is active
        decoded = self.adapter.decode(encoded, DecodeOptions())
        # Expected: decoded data matches input data with inferred types (ints)
        assert decoded == data

    def test_roundtrip_preserves_headers(self):
        """Test roundtrip preserves headers."""
        data = [{"col1": "A", "col2": "B"}, {"col1": "C", "col2": "D"}]
        encoded = self.adapter.encode(data, None)
        # Disable inference for a direct string-to-string comparison on headers
        decoded = self.adapter.decode(encoded, DecodeOptions(type_inference=False))
        assert set(decoded[0].keys()) == {"col1", "col2"}

    def test_roundtrip_with_inference(self):
        """Test roundtrip that encodes strings and decodes them to native types."""
        # input data must be list of dicts for encode
        data_input = [{"id": 1, "is_active": True}, {"id": 2, "is_active": False}]

        encoded = self.adapter.encode(data_input, None)
        options = DecodeOptions(type_inference=True)
        decoded = self.adapter.decode(encoded, options)

        assert decoded == data_input
