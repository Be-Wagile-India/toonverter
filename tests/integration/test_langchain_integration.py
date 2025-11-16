"""Integration tests for LangChain support."""

import pytest


# Skip if langchain not installed
pytest.importorskip("langchain")

from toonverter.integrations.langchain_integration import (
    toon_to_langchain,
    from_toon_messages,
    langchain_to_toon,
    to_toon_messages,
)


class TestLangChainDocuments:
    """Test LangChain Document handling."""

    def test_document_to_toon(self):
        """Test converting LangChain Document to TOON."""
        try:
            from langchain.docstore.document import Document

            doc = Document(
                page_content="This is the content", metadata={"source": "test.txt", "page": 1}
            )

            toon = langchain_to_toon(doc)

            assert "This is the content" in toon
            assert "test.txt" in toon
            assert "1" in str(toon)
        except ImportError:
            pytest.skip("LangChain Document not available")

    def test_document_roundtrip(self):
        """Test Document roundtrip."""
        try:
            from langchain.docstore.document import Document

            doc_original = Document(page_content="Test content", metadata={"key": "value"})

            toon = langchain_to_toon(doc_original)
            doc_result = toon_to_langchain(toon)

            assert doc_result.page_content == "Test content"
            assert doc_result.metadata["key"] == "value"
        except ImportError:
            pytest.skip("LangChain Document not available")

    def test_multiple_documents(self):
        """Test list of Documents."""
        try:
            from langchain.docstore.document import Document

            docs = [
                Document(page_content="Doc 1", metadata={"id": 1}),
                Document(page_content="Doc 2", metadata={"id": 2}),
                Document(page_content="Doc 3", metadata={"id": 3}),
            ]

            toon = langchain_to_toon(docs)

            assert "Doc 1" in toon
            assert "Doc 2" in toon
            assert "Doc 3" in toon
        except ImportError:
            pytest.skip("LangChain Document not available")


class TestLangChainMessages:
    """Test LangChain message handling."""

    def test_messages_to_toon(self):
        """Test converting messages to TOON."""
        try:
            from langchain.schema import AIMessage, HumanMessage, SystemMessage

            messages = [
                SystemMessage(content="You are a helpful assistant"),
                HumanMessage(content="Hello!"),
                AIMessage(content="Hi there! How can I help?"),
            ]

            toon = to_toon_messages(messages)

            assert "helpful assistant" in toon
            assert "Hello!" in toon
            assert "How can I help?" in toon
        except ImportError:
            pytest.skip("LangChain messages not available")

    def test_messages_roundtrip(self):
        """Test message roundtrip."""
        try:
            from langchain.schema import HumanMessage

            messages_original = [HumanMessage(content="Test message")]

            toon = to_toon_messages(messages_original)
            messages_result = from_toon_messages(toon)

            assert len(messages_result) == 1
            assert messages_result[0].content == "Test message"
        except ImportError:
            pytest.skip("LangChain messages not available")
