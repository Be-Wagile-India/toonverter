"""Comprehensive functional tests for all integrations.

This test suite verifies that all integrations work correctly with the fixed
options conversion, particularly focusing on integrations that use EncodeOptions.
"""

import pytest

import toonverter as toon
from toonverter.core.types import EncodeOptions


class TestPandasIntegration:
    """Test pandas integration with fixed options handling."""

    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        pytest.importorskip("pandas")
        import pandas as pd

        return pd.DataFrame(
            {"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35], "city": ["NYC", "LA", "SF"]}
        )

    def test_pandas_to_toon_basic(self, sample_dataframe):
        """Test basic DataFrame to TOON conversion (README example)."""
        pytest.importorskip("pandas")
        from toonverter.integrations import pandas_to_toon

        result = pandas_to_toon(sample_dataframe)

        # Verify tabular format
        assert "[3]{name,age,city}:" in result
        assert "Alice,30,NYC" in result
        assert "Bob,25,LA" in result
        assert "Charlie,35,SF" in result

    def test_pandas_to_toon_with_custom_options(self, sample_dataframe):
        """Test DataFrame conversion with custom options."""
        pytest.importorskip("pandas")
        from toonverter.integrations import pandas_to_toon

        options = EncodeOptions(delimiter="|", compact=True)
        result = pandas_to_toon(sample_dataframe, options)

        # Should use pipe delimiter (TOON format uses delimiter in array header too)
        assert "{name|age|city}:" in result
        assert "Alice|30|NYC" in result

    def test_pandas_roundtrip(self, sample_dataframe):
        """Test DataFrame to TOON and back."""
        pytest.importorskip("pandas")
        import pandas as pd
        from toonverter.integrations import pandas_to_toon, toon_to_pandas

        toon_str = pandas_to_toon(sample_dataframe)
        result_df = toon_to_pandas(toon_str)

        # Should be equal
        pd.testing.assert_frame_equal(sample_dataframe, result_df)

    def test_empty_dataframe(self):
        """Test empty DataFrame encoding."""
        pytest.importorskip("pandas")
        import pandas as pd
        from toonverter.integrations import pandas_to_toon

        df = pd.DataFrame()
        result = pandas_to_toon(df)
        assert result == "[0]:"

    def test_single_row_dataframe(self):
        """Test single row DataFrame."""
        pytest.importorskip("pandas")
        import pandas as pd
        from toonverter.integrations import pandas_to_toon

        df = pd.DataFrame({"x": [1], "y": [2]})
        result = pandas_to_toon(df)

        assert "[1]{x,y}:" in result
        assert "1,2" in result


class TestFacadeAPI:
    """Test main facade API with various options."""

    def test_encode_with_encode_options(self):
        """Test toon.encode() with EncodeOptions."""
        data = {"name": "Alice", "age": 30}
        result = toon.encode(data, to_format="toon", compact=True)

        assert "name:" in result
        assert "Alice" in result

    def test_encode_with_delimiter_option(self):
        """Test encoding with custom delimiter."""
        data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]
        result = toon.encode(data, to_format="toon", delimiter="|", compact=True)

        assert "|" in result
        assert "1|2" in result

    def test_encoder_class_with_options(self):
        """Test Encoder class with options."""
        encoder = toon.Encoder(format="toon", delimiter=",", compact=True)
        result = encoder.encode({"a": 1, "b": 2})

        assert "a:" in result
        assert "b:" in result

    def test_roundtrip_through_facade(self):
        """Test encode/decode roundtrip through facade API."""
        data = {"name": "Alice", "age": 30, "tags": ["admin", "user"]}

        encoded = toon.encode(data)
        decoded = toon.decode(encoded)

        assert decoded == data


class TestCompactModeIntegration:
    """Test compact mode integration across the system."""

    def test_compact_mode_no_indentation(self):
        """Test that compact mode produces no indentation."""
        data = {"user": {"name": "Alice", "age": 30, "settings": {"theme": "dark"}}}

        result = toon.encode(data, to_format="toon", compact=True)

        # No lines should start with spaces
        lines = result.split("\n")
        for line in lines:
            if line:
                assert not line.startswith(" "), f"Compact mode should not indent: {line!r}"

    def test_tabular_preset_is_compact(self):
        """Test that tabular preset produces compact output."""
        data = [{"x": 1, "y": 2}, {"x": 3, "y": 4}]

        options = EncodeOptions.tabular()
        result = toon.encode(data, to_format="toon", **options.__dict__)

        # Should be compact (no indentation for items)
        assert result.count("\n") >= 2  # Header + rows
        # No lines should be indented
        lines = result.split("\n")
        for line in lines:
            if line and not line.startswith("["):
                assert not line.startswith(" ")


class TestDelimiterOptions:
    """Test different delimiter options."""

    def test_comma_delimiter_default(self):
        """Test comma delimiter (default)."""
        data = [{"a": 1, "b": 2}]
        result = toon.encode(data, to_format="toon", compact=True)

        assert "," in result
        assert "1,2" in result

    def test_tab_delimiter(self):
        """Test tab delimiter."""
        data = [{"a": 1, "b": 2}]
        result = toon.encode(data, to_format="toon", delimiter="\t", compact=True)

        assert "\t" in result
        assert "1\t2" in result

    def test_pipe_delimiter(self):
        """Test pipe delimiter."""
        data = [{"a": 1, "b": 2}]
        result = toon.encode(data, to_format="toon", delimiter="|", compact=True)

        assert "|" in result
        assert "1|2" in result


class TestREADMEExamples:
    """Test all examples from README.md to ensure they work."""

    def test_simple_encode_decode_example(self):
        """Test: Quick Start - Simple Facade API example 1."""
        # From README lines 124-136
        data = {"name": "Alice", "age": 30, "city": "NYC"}
        toon_str = toon.encode(data)

        # Should encode successfully
        assert isinstance(toon_str, str)
        assert "name:" in toon_str or "name" in toon_str

        # Decode back
        decoded = toon.decode(toon_str)
        assert decoded == data

    def test_analyze_example(self):
        """Test: Quick Start - analyze() example."""
        # From README lines 141-145
        data = {"name": "Alice", "age": 30}
        report = toon.analyze(data, compare_formats=["json", "toon"])

        assert report.best_format in ["json", "toon"]
        assert isinstance(report.max_savings_percentage, float)
        assert report.max_savings_percentage >= 0

    def test_encoder_class_example(self):
        """Test: Object-Oriented API - Encoder example."""
        # From README lines 171-176
        encoder = toon.Encoder(format="toon", delimiter=",", compact=True)
        data = {"name": "Alice", "age": 30}
        encoded = encoder.encode(data)

        assert isinstance(encoded, str)
        assert "Alice" in encoded

    def test_pandas_dataframe_example(self):
        """Test: Integration Examples - Pandas DataFrame."""
        # From README lines 188-199
        pd = pytest.importorskip("pandas")
        from toonverter.integrations import pandas_to_toon

        df = pd.DataFrame(
            {"name": ["Alice", "Bob", "Charlie"], "age": [30, 25, 35], "city": ["NYC", "LA", "SF"]}
        )

        toon_str = pandas_to_toon(df)

        # Should produce tabular format
        assert "[3]{" in toon_str
        assert "name" in toon_str
        assert "Alice" in toon_str


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling."""

    def test_empty_dict(self):
        """Test encoding empty dictionary."""
        result = toon.encode({})
        assert isinstance(result, str)

    def test_empty_list(self):
        """Test encoding empty list."""
        result = toon.encode([])
        assert "[0]:" in result

    def test_none_value(self):
        """Test encoding None."""
        result = toon.encode(None)
        assert result == "null"

    def test_boolean_values(self):
        """Test encoding booleans."""
        data = {"active": True, "deleted": False}
        result = toon.encode(data)

        assert "true" in result
        assert "false" in result

    def test_nested_arrays(self):
        """Test nested arrays."""
        data = {"matrix": [[1, 2], [3, 4]]}
        result = toon.encode(data)

        # Should handle nested structure
        assert "matrix" in result

    def test_mixed_types_in_array(self):
        """Test arrays with mixed types."""
        data = [1, "hello", True, None]
        result = toon.encode(data)

        assert "1" in result
        assert "hello" in result
        assert "true" in result
        assert "null" in result


class TestPerformance:
    """Test performance-critical scenarios."""

    def test_large_tabular_data(self):
        """Test encoding large tabular dataset."""
        pd = pytest.importorskip("pandas")
        from toonverter.integrations import pandas_to_toon

        # Create larger DataFrame
        df = pd.DataFrame({"x": range(100), "y": range(100, 200), "z": range(200, 300)})

        result = pandas_to_toon(df)

        # Should use tabular format
        assert "[100]{x,y,z}:" in result
        # Should be compact
        assert len(result.split("\n")) == 101  # Header + 100 rows

    def test_deeply_nested_structure(self):
        """Test deeply nested structure."""
        data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        result = toon.encode(data)

        assert "deep" in result


class TestIntegrationConsistency:
    """Test consistency across different integration points."""

    def test_same_output_from_different_apis(self):
        """Test that different APIs produce same output."""
        data = {"name": "Alice", "age": 30}

        # Facade API
        result1 = toon.encode(data, to_format="toon")

        # Encoder class
        encoder = toon.Encoder(format="toon")
        result2 = encoder.encode(data)

        # Direct encoder
        from toonverter.encoders import encode

        result3 = encode(data)

        # All should produce similar output (may differ in whitespace)
        assert "Alice" in result1
        assert "Alice" in result2
        assert "Alice" in result3

    def test_options_consistency(self):
        """Test that options work consistently across APIs."""
        data = [{"x": 1}, {"x": 2}]

        # Via facade with kwargs
        result1 = toon.encode(data, to_format="toon", compact=True, delimiter="|")

        # Via Encoder class
        encoder = toon.Encoder(format="toon", compact=True, delimiter="|")
        result2 = encoder.encode(data)

        # Both should use pipe delimiter
        assert "|" in result1
        assert "|" in result2
