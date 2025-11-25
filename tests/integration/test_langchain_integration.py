"""Integration tests for LangChain support.

These tests are resilient to multiple LangChain package layouts:
- langchain_core.documents.Document (new)
- langchain.schema.Document (common)
- langchain.docstore.document.Document (older)

Message tests will attempt to import message classes (HumanMessage/AIMessage/SystemMessage)
from langchain.schema or langchain_core and will skip only if none are available.
"""

import pytest

from toonverter.integrations.langchain_integration import (
    langchain_to_toon,
    messages_to_toon,
    toon_to_langchain,
    toon_to_messages,
)


def _get_document_class_or_skip():
    """Try multiple import locations for LangChain Document and return the class.

    If none are available, call pytest.skip so the test is marked as skipped with
    a helpful message.
    """
    try:
        # Newer layout
        from langchain_core.documents import Document  # type: ignore

        return Document
    except Exception:
        pass

    try:
        # Common schema export
        from langchain.schema import Document

        return Document
    except Exception:
        pass

    try:
        # Older classic layout
        from langchain.docstore.document import Document

        return Document
    except Exception:
        pass

    pytest.skip("LangChain Document not available")
    return None

def _get_message_classes_or_skip():
    """Return a tuple of (HumanMessageClass, AIMessageClass, SystemMessageClass) or skip.

    If no message classes are available, call pytest.skip.
    """
    try:
        # modern schema
        from langchain.schema import AIMessage, HumanMessage, SystemMessage  # type: ignore

        return HumanMessage, AIMessage, SystemMessage
    except Exception:
        pass

    # Try langchain_core if available
    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # type: ignore

        return HumanMessage, AIMessage, SystemMessage
    except Exception:
        pass

    pytest.skip("LangChain message classes not available")
    return None

class TestLangChainDocuments:
    """Test LangChain Document handling."""

    def test_document_to_toon(self):
        """Test converting LangChain Document to TOON."""
        Document = _get_document_class_or_skip()

        doc = Document(
            page_content="This is the content", metadata={"source": "test.txt", "page": 1}
        )

        toon = langchain_to_toon(doc)

        assert "This is the content" in toon
        assert "test.txt" in toon
        assert "1" in str(toon)

    def test_document_roundtrip(self):
        """Test Document roundtrip."""
        Document = _get_document_class_or_skip()

        doc_original = Document(page_content="Test content", metadata={"key": "value"})

        toon = langchain_to_toon(doc_original)
        doc_result = toon_to_langchain(toon)

        assert doc_result.page_content == "Test content"
        assert doc_result.metadata["key"] == "value"

    def test_multiple_documents(self):
        """Test list of Documents."""
        Document = _get_document_class_or_skip()

        docs = [
            Document(page_content="Doc 1", metadata={"id": 1}),
            Document(page_content="Doc 2", metadata={"id": 2}),
            Document(page_content="Doc 3", metadata={"id": 3}),
        ]

        toon = langchain_to_toon(docs)

        assert "Doc 1" in toon
        assert "Doc 2" in toon
        assert "Doc 3" in toon


class TestLangChainMessages:
    """Test LangChain message handling."""

    def test_messages_to_toon_and_roundtrip(self):
        """Test converting messages to TOON and back (roundtrip)."""
        HumanMessage, AIMessage, SystemMessage = _get_message_classes_or_skip()

        # Build sample messages
        msgs = [
            HumanMessage(content="Hello", additional_kwargs={"mood": "curious"}),  # type: ignore
            AIMessage(content="Hi there!", additional_kwargs={"confidence": 0.95}),  # type: ignore
            SystemMessage(content="System notice"),  # type: ignore
        ]

        toon = messages_to_toon(msgs)
        assert isinstance(toon, str)

        restored = toon_to_messages(toon)
        assert isinstance(restored, list)
        # At least ensure content values roundtrip
        contents = [
            getattr(m, "content", m.get("content") if isinstance(m, dict) else None)
            for m in restored
        ]
        assert "Hello" in contents
        assert "Hi there!" in contents
        assert "System notice" in contents
