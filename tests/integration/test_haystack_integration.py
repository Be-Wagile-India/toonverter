"""Integration tests for Haystack support."""

import pytest

from toonverter.integrations.haystack_integration import haystack_to_toon, toon_to_haystack


# Check if haystack is available
try:
    from haystack.dataclasses import Document  # noqa: F401

    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False


@pytest.mark.skipif(not HAYSTACK_AVAILABLE, reason="Haystack not installed")
class TestHaystackDocuments:
    """Test Haystack Document handling."""

    def test_document_to_toon(self):
        """Test converting Haystack Document to TOON."""
        from haystack.dataclasses import Document

        doc = Document(content="Test content", meta={"source": "test.txt"})
        toon = haystack_to_toon(doc)

        assert "Test content" in toon
        assert "test.txt" in toon

    def test_document_roundtrip(self):
        """Test Document roundtrip."""
        from haystack.dataclasses import Document

        doc_original = Document(content="Content", meta={"key": "value"})
        toon = haystack_to_toon(doc_original)
        doc_result = toon_to_haystack(toon)

        assert doc_result.content == "Content"
        assert doc_result.meta["key"] == "value"

    def test_multiple_documents(self):
        """Test list of Documents."""
        from haystack.dataclasses import Document

        docs = [Document(content="Doc 1"), Document(content="Doc 2"), Document(content="Doc 3")]
        toon = haystack_to_toon(docs)

        assert "Doc 1" in toon
        assert "Doc 2" in toon
