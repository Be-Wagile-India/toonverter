"""Comprehensive functional tests for all integrations.

This test suite verifies that all integrations work correctly with the fixed
options conversion system, testing both EncodeOptions and ToonEncodeOptions paths.
"""

import pytest

import toonverter as toon
from toonverter.core.types import EncodeOptions


# =============================================================================
# PANDAS INTEGRATION TESTS
# =============================================================================


class TestPandasIntegration:
    """Complete functional tests for Pandas integration."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        pd = pytest.importorskip("pandas")
        return pd.DataFrame(
            {
                "name": ["Alice", "Bob", "Charlie"],
                "age": [30, 25, 35],
                "city": ["NYC", "LA", "SF"],
                "active": [True, False, True],
            }
        )

    def test_pandas_to_toon_basic(self, sample_df):
        """Test basic DataFrame to TOON conversion."""
        from toonverter.integrations.pandas_integration import pandas_to_toon

        result = pandas_to_toon(sample_df)
        assert "[3]{name,age,city,active}:" in result
        assert "Alice,30,NYC,true" in result

    def test_pandas_with_options(self, sample_df):
        """Test DataFrame encoding with custom options."""
        from toonverter.integrations.pandas_integration import pandas_to_toon

        options = EncodeOptions(delimiter="|", compact=True)
        result = pandas_to_toon(sample_df, options)
        assert "{name|age|city|active}:" in result
        assert "Alice|30|NYC|true" in result

    def test_pandas_roundtrip(self, sample_df):
        """Test DataFrame roundtrip."""
        import pandas as pd

        from toonverter.integrations.pandas_integration import pandas_to_toon, toon_to_pandas

        toon_str = pandas_to_toon(sample_df)
        result_df = toon_to_pandas(toon_str)

        # Verify shape and columns
        assert result_df.shape == sample_df.shape
        assert set(result_df.columns) == set(sample_df.columns)

        # Proper deep comparison
        pd.testing.assert_frame_equal(sample_df, result_df, check_like=True)

    def test_empty_dataframe(self):
        """Test empty DataFrame encoding."""
        pytest.importorskip("pandas")
        import pandas as pd

        from toonverter.integrations.pandas_integration import pandas_to_toon

        df = pd.DataFrame()
        result = pandas_to_toon(df)
        assert result == "[0]:"


# =============================================================================
# PYDANTIC INTEGRATION TESTS
# =============================================================================


class TestPydanticIntegration:
    """Complete functional tests for Pydantic integration."""

    @pytest.fixture
    def user_model(self):
        """Create Pydantic User model."""
        pytest.importorskip("pydantic")
        from pydantic import BaseModel

        class User(BaseModel):
            name: str
            age: int
            email: str
            active: bool = True

        return User

    def test_basic_encoding(self, user_model):
        """Test basic Pydantic model encoding."""
        from toonverter.integrations.pydantic_integration import pydantic_to_toon

        user = user_model(name="Alice", age=30, email="alice@example.com")
        result = pydantic_to_toon(user)
        assert "Alice" in result
        assert "30" in result
        assert "alice@example.com" in result

    def test_pydantic_roundtrip(self, user_model):
        """Test Pydantic roundtrip."""
        from toonverter.integrations.pydantic_integration import (
            pydantic_to_toon,
            toon_to_pydantic,
        )

        user = user_model(name="Charlie", age=35, email="charlie@test.com")
        toon_str = pydantic_to_toon(user)
        result_user = toon_to_pydantic(toon_str, user_model)
        assert result_user.name == user.name
        assert result_user.age == user.age
        assert result_user.email == user.email


# =============================================================================
# LANGCHAIN INTEGRATION TESTS
# =============================================================================


def _get_langchain_document_or_skip():
    """Return a LangChain Document class from known locations."""
    try:
        from langchain_core.documents import Document

        return Document
    except Exception:
        pass
    try:
        from langchain.schema import Document

        return Document
    except Exception:
        pass
    try:
        from langchain.docstore.document import Document

        return Document
    except Exception:
        pass
    pytest.skip("langchain not installed")


class TestLangChainIntegration:
    """Complete functional tests for LangChain integration."""

    def test_document_roundtrip(self):
        """Test LangChain Document roundtrip."""
        Document = _get_langchain_document_or_skip()
        from toonverter.integrations.langchain_integration import (
            langchain_to_toon,
            toon_to_langchain,
        )

        doc = Document(page_content="Original Content", metadata={"source": "origin.txt"})
        toon_str = langchain_to_toon(doc)
        result_doc = toon_to_langchain(toon_str)
        assert result_doc.page_content == doc.page_content
        assert result_doc.metadata == doc.metadata


# =============================================================================
# FACADE API & CROSS-CUTTING TESTS
# =============================================================================


class TestFacadeAPI:
    """Test main facade API with various options."""

    def test_encode_decode_roundtrip(self):
        """Test encode/decode roundtrip through facade API."""
        data = {"name": "Alice", "age": 30, "tags": ["admin", "user"]}
        encoded = toon.encode(data)
        decoded = toon.decode(encoded)
        assert decoded == data

    def test_compact_mode(self):
        """Test that compact mode produces no indentation."""
        data = {"user": {"name": "Alice", "settings": {"theme": "dark"}}}
        result = toon.encode(data, compact=True)
        for line in result.split("\n"):
            if line:
                assert not line.startswith(" ")

    def test_delimiter_options(self):
        """Test different delimiter options."""
        data = [{"a": 1, "b": 2}]

        # Pipe
        res_pipe = toon.encode(data, delimiter="|", compact=True)
        assert "|" in res_pipe

        # Tab
        res_tab = toon.encode(data, delimiter="\t", compact=True)
        assert "\t" in res_tab


class TestSummary:
    """Test general system consistency."""

    def test_all_integrations_importable(self):
        """Verify key integrations are importable."""
        integrations = [
            "pandas_integration",
            "pydantic_integration",
            "langchain_integration",
            "fastapi_integration",
            "haystack_integration",
            "llamaindex_integration",
            "sqlalchemy_integration",
            "dspy_integration",
            "instructor_integration",
        ]
        for integration in integrations:
            module = __import__(f"toonverter.integrations.{integration}", fromlist=[integration])
            assert module is not None
