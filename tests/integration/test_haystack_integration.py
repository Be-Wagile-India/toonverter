"""Integration tests for Haystack support."""

import pytest

# Skip if haystack-ai not installed
pytest.importorskip("haystack")

from toonverter.integrations.haystack_integration import to_toon_document, from_toon_document


class TestHaystackDocuments:
    """Test Haystack Document handling."""

    def test_document_to_toon(self):
        """Test converting Haystack Document to TOON."""
        try:
            from haystack.dataclasses import Document

            doc = Document(
                content="Test content",
                meta={"source": "test.txt"}
            )

            toon = to_toon_document(doc)

            assert 'Test content' in toon
            assert 'test.txt' in toon
        except ImportError:
            pytest.skip("Haystack Document not available")

    def test_document_roundtrip(self):
        """Test Document roundtrip."""
        try:
            from haystack.dataclasses import Document

            doc_original = Document(
                content="Content",
                meta={"key": "value"}
            )

            toon = to_toon_document(doc_original)
            doc_result = from_toon_document(toon)

            assert doc_result.content == "Content"
            assert doc_result.meta["key"] == "value"
        except ImportError:
            pytest.skip("Haystack not available")

    def test_multiple_documents(self):
        """Test list of Documents."""
        try:
            from haystack.dataclasses import Document

            docs = [
                Document(content="Doc 1"),
                Document(content="Doc 2"),
                Document(content="Doc 3")
            ]

            toon = to_toon_document(docs)

            assert 'Doc 1' in toon and 'Doc 2' in toon
        except ImportError:
            pytest.skip("Haystack not available")
