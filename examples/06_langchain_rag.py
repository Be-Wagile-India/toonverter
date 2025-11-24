#!/usr/bin/env python3
"""
Example 6: LangChain RAG System Optimization

Demonstrates:
- Optimizing LangChain documents for RAG
- Reducing vector database storage
- Improving retrieval efficiency
- Token savings in document chains
"""

try:
    from langchain.schema import Document, HumanMessage, AIMessage
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from toonverter.integrations import langchain_to_toon, toon_to_langchain

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("Install langchain: pip install toonverter[langchain]")

import toonverter as toon


def example_document_conversion():
    """Convert LangChain documents to TOON."""
    if not LANGCHAIN_AVAILABLE:
        return

    print("\n--- Document Conversion ---")

    # Create documents
    doc1 = Document(
        page_content="Python is a high-level programming language known for its simplicity.",
        metadata={"source": "python_guide.pdf", "page": 1, "author": "Alice"},
    )

    doc2 = Document(
        page_content="Machine learning is a subset of artificial intelligence.",
        metadata={"source": "ml_intro.pdf", "page": 5, "author": "Bob"},
    )

    print("\nOriginal documents:")
    for i, doc in enumerate([doc1, doc2], 1):
        print(f"\nDocument {i}:")
        print(f"  Content: {doc.page_content[:50]}...")
        print(f"  Metadata: {doc.metadata}")

    # Convert to TOON
    toon_docs = [langchain_to_toon(doc) for doc in [doc1, doc2]]

    print("\nTOON representations:")
    for i, toon_str in enumerate(toon_docs, 1):
        print(f"\nDocument {i} (TOON):")
        print(toon_str)

    # Convert back
    restored_docs = [toon_to_langchain(toon_str) for toon_str in toon_docs]

    print("\nRestored documents:")
    for i, doc in enumerate(restored_docs, 1):
        print(f"\nDocument {i}:")
        print(f"  Content: {doc.page_content[:50]}...")
        print(f"  Metadata: {doc.metadata}")


def example_message_conversion():
    """Convert LangChain messages to TOON."""
    if not LANGCHAIN_AVAILABLE:
        return

    print("\n--- Message Conversion ---")

    messages = [
        HumanMessage(content="What is TOON format?"),
        AIMessage(
            content="TOON is a token-optimized data format that reduces LLM token usage by 30-60%."
        ),
        HumanMessage(content="How does it achieve this?"),
        AIMessage(content="TOON uses minimal syntax, tabular formats, and smart quoting rules."),
    ]

    print("\nOriginal messages:")
    for msg in messages:
        role = "Human" if isinstance(msg, HumanMessage) else "AI"
        print(f"  {role}: {msg.content[:50]}...")

    # Convert to TOON
    toon_messages = [langchain_to_toon(msg) for msg in messages]

    print("\nTOON representations:")
    for i, toon_str in enumerate(toon_messages, 1):
        print(f"\nMessage {i} (TOON):")
        print(toon_str)


def example_rag_pipeline():
    """RAG pipeline with TOON optimization."""
    if not LANGCHAIN_AVAILABLE:
        return

    print("\n--- RAG Pipeline Optimization ---")

    # Simulate a knowledge base
    knowledge_base = [
        "Python is a versatile programming language.",
        "Machine learning uses algorithms to learn from data.",
        "Natural language processing enables computers to understand human language.",
        "Deep learning is a subset of machine learning using neural networks.",
        "TOON format reduces token usage in LLM applications.",
    ]

    # Create documents
    documents = [
        Document(page_content=text, metadata={"source": f"doc{i}", "id": i})
        for i, text in enumerate(knowledge_base)
    ]

    print(f"\nKnowledge base: {len(documents)} documents")

    # Convert to TOON for storage
    toon_docs = [langchain_to_toon(doc) for doc in documents]

    # Calculate storage savings
    import json

    json_size = sum(
        len(json.dumps({"content": doc.page_content, "metadata": doc.metadata}))
        for doc in documents
    )
    toon_size = sum(len(toon_str) for toon_str in toon_docs)

    print(f"\nStorage comparison:")
    print(f"  JSON: {json_size} bytes")
    print(f"  TOON: {toon_size} bytes")
    print(f"  Savings: {((json_size - toon_size) / json_size * 100):.1f}%")

    # Token analysis
    all_docs_dict = [{"content": doc.page_content, "metadata": doc.metadata} for doc in documents]
    report = toon.analyze({"documents": all_docs_dict}, compare_formats=["json", "toon"])

    print(f"\nToken savings: {report.max_savings_percentage:.1f}%")
    print(f"  JSON: {report.format_results['json'].token_count} tokens")
    print(f"  TOON: {report.format_results['toon'].token_count} tokens")


def example_document_splitting():
    """Split and optimize documents."""
    if not LANGCHAIN_AVAILABLE:
        return

    print("\n--- Document Splitting & Optimization ---")

    # Long document
    long_text = (
        """
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
    Python has a comprehensive standard library and a vast ecosystem of third-party packages.
    The language is widely used in web development, data science, machine learning, and automation.
    """
        * 5
    )  # Repeat to make it longer

    # Split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    chunks = splitter.create_documents([long_text])

    print(f"\nDocument split into {len(chunks)} chunks")

    # Convert chunks to TOON
    toon_chunks = [langchain_to_toon(chunk) for chunk in chunks]

    # Show sample
    print("\nSample chunk (original):")
    print(chunks[0].page_content[:100] + "...")

    print("\nSample chunk (TOON):")
    print(toon_chunks[0][:150] + "...")

    # Calculate savings
    import json

    json_size = sum(
        len(json.dumps({"content": chunk.page_content, "metadata": chunk.metadata}))
        for chunk in chunks
    )
    toon_size = sum(len(toon_str) for toon_str in toon_chunks)

    print(f"\nTotal chunks storage:")
    print(f"  JSON: {json_size} bytes")
    print(f"  TOON: {toon_size} bytes")
    print(f"  Savings: {((json_size - toon_size) / json_size * 100):.1f}%")


def main():
    print("=" * 60)
    print("Example 6: LangChain RAG System Optimization")
    print("=" * 60)

    if not LANGCHAIN_AVAILABLE:
        print("\nPlease install: pip install toonverter[langchain]")
        return

    example_document_conversion()
    example_message_conversion()
    example_rag_pipeline()
    example_document_splitting()


if __name__ == "__main__":
    main()
