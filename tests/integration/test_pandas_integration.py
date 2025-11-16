"""Integration tests for Pandas DataFrame support."""

import pytest


# Skip if pandas not installed
pytest.importorskip("pandas")

import pandas as pd

from toonverter.integrations.pandas_integration import pandas_to_toon, toon_to_pandas


class TestPandasDataFrameConversion:
    """Test Pandas DataFrame to/from TOON conversion."""

    def test_simple_dataframe_pandas_to_toon(self):
        """Test converting simple DataFrame to TOON."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "Carol"], "age": [30, 25, 35]})

        toon = pandas_to_toon(df)

        # Should use tabular format
        assert "[3]{name,age}:" in toon or "[3]{age,name}:" in toon

    def test_simple_dataframe_roundtrip(self):
        """Test DataFrame roundtrip."""
        df_original = pd.DataFrame({"id": [1, 2, 3], "value": ["a", "b", "c"]})

        toon = pandas_to_toon(df_original)
        df_result = toon_to_pandas(toon)

        # Compare data (column order might differ)
        assert df_result.shape == df_original.shape
        assert set(df_result.columns) == set(df_original.columns)

    def test_dataframe_with_various_types(self):
        """Test DataFrame with different column types."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )

        toon = pandas_to_toon(df)
        df_result = toon_to_pandas(toon)

        assert df_result.shape == df.shape

    def test_empty_dataframe(self):
        """Test empty DataFrame."""
        df = pd.DataFrame()

        toon = pandas_to_toon(df)
        df_result = toon_to_pandas(toon)

        assert df_result.empty

    def test_dataframe_with_index(self):
        """Test DataFrame with custom index."""
        df = pd.DataFrame({"value": [10, 20, 30]}, index=["a", "b", "c"])

        toon = pandas_to_toon(df, include_index=True)

        # Should include index
        assert "a" in toon or "index" in toon.lower()

    def test_large_dataframe(self):
        """Test large DataFrame."""
        df = pd.DataFrame({"id": range(1000), "value": [f"item_{i}" for i in range(1000)]})

        toon = pandas_to_toon(df)

        assert "[1000]{" in toon


class TestPandasSeriesConversion:
    """Test Pandas Series to/from TOON conversion."""

    def test_simple_series_pandas_to_toon(self):
        """Test converting Series to TOON."""
        s = pd.Series([1, 2, 3, 4, 5], name="numbers")

        toon = pandas_to_toon(s)

        # Should be an inline array
        assert "[5]:" in toon

    def test_series_roundtrip(self):
        """Test Series roundtrip."""
        s_original = pd.Series(["a", "b", "c"], name="letters")

        toon = pandas_to_toon(s_original)
        s_result = toon_to_pandas(toon, as_series=True)

        assert len(s_result) == len(s_original)


class TestPandasOptions:
    """Test Pandas conversion options."""

    def test_orient_option(self):
        """Test different orient options."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        # Test records orient (list of dicts)
        toon_records = pandas_to_toon(df, orient="records")
        assert "[2]" in toon_records

        # Test columns orient
        toon_columns = pandas_to_toon(df, orient="columns")
        assert "a" in toon_columns
        assert "b" in toon_columns

    def test_compression_option(self):
        """Test compression option for large DataFrames."""
        df = pd.DataFrame({"x": list(range(100)), "y": list(range(100, 200))})

        # Default (no compression)
        toon_normal = pandas_to_toon(df)

        # With compression
        toon_compressed = pandas_to_toon(df, compress=True)

        # Compressed should be smaller or equal
        assert len(toon_compressed) <= len(toon_normal)
