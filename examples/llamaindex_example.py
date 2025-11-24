"""LlamaIndex Integration Example.

Demonstrates all features of toonverter's LlamaIndex integration:
1. Document conversion and roundtrip
2. Node serialization (TextNode, ImageNode, IndexNode)
3. Bulk operations for large document collections
4. Metadata extraction
5. Token savings analysis for RAG pipelines

Install dependencies:
    pip install toonverter[llamaindex]
"""

from llama_index.core import Document
from llama_index.core.schema import TextNode, ImageNode, IndexNode, NodeRelationship

from toonverter.integrations.llamaindex import (
    llamaindex_to_toon,
    toon_to_llamaindex,
    bulk_documents_to_toon,
    bulk_toon_to_documents,
    stream_documents_to_toon,
    extract_metadata_to_toon,
)


# =============================================================================
# 1. DOCUMENT CONVERSION
# =============================================================================


def example_document_conversion():
    """Example: Convert LlamaIndex Documents to/from TOON."""
    print("\n" + "=" * 70)
    print("1. DOCUMENT CONVERSION")
    print("=" * 70)

    # Create a simple document
    print("\n📄 Simple Document → TOON:")
    doc = Document(
        text="LlamaIndex is a data framework for LLM applications.",
        metadata={"source": "documentation.txt", "page": 1, "section": "Introduction"},
    )

    toon = llamaindex_to_toon(doc)
    print(toon)

    # Convert back
    print("\n📄 TOON → Document:")
    restored_doc = toon_to_llamaindex(toon)
    print(f"Text: {restored_doc.text}")
    print(f"Metadata: {restored_doc.metadata}")

    # Create document with more metadata
    print("\n📄 Complex Document → TOON:")
    doc2 = Document(
        text="This is a sample paragraph from a research paper about neural networks.",
        metadata={
            "title": "Deep Learning Review",
            "author": "Dr. Smith",
            "year": 2024,
            "keywords": ["AI", "ML", "Deep Learning"],
            "doi": "10.1234/example.2024",
        },
        excluded_embed_metadata_keys=["doi"],
        excluded_llm_metadata_keys=["author"],
    )

    toon2 = llamaindex_to_toon(doc2)
    print(toon2)


# =============================================================================
# 2. NODE SERIALIZATION
# =============================================================================


def example_node_serialization():
    """Example: Convert different node types to/from TOON."""
    print("\n" + "=" * 70)
    print("2. NODE SERIALIZATION")
    print("=" * 70)

    # TextNode with character indices
    print("\n📝 TextNode → TOON:")
    text_node = TextNode(
        text="LlamaIndex provides data loaders for various sources.",
        metadata={"source": "guide.md"},
        start_char_idx=0,
        end_char_idx=54,
    )

    toon = llamaindex_to_toon(text_node)
    print(toon)

    # ImageNode
    print("\n🖼️  ImageNode → TOON:")
    image_node = ImageNode(
        text="Architecture diagram showing LlamaIndex components",
        metadata={"caption": "Figure 1: System Architecture"},
        image_path="/path/to/architecture.png",
    )

    toon2 = llamaindex_to_toon(image_node)
    print(toon2)

    # IndexNode
    print("\n🗂️  IndexNode → TOON:")
    index_node = IndexNode(
        text="Reference to external knowledge base",
        metadata={"kb_name": "product_docs"},
        index_id="kb_v2_2024",
    )

    toon3 = llamaindex_to_toon(index_node)
    print(toon3)

    # Convert back with type detection
    print("\n📥 TOON → TextNode:")
    restored_node = toon_to_llamaindex(toon, node_type="text")
    print(f"Node type: {type(restored_node).__name__}")
    print(f"Text: {restored_node.text}")
    print(f"Char range: {restored_node.start_char_idx}-{restored_node.end_char_idx}")


# =============================================================================
# 3. BULK OPERATIONS
# =============================================================================


def example_bulk_operations():
    """Example: Convert multiple documents efficiently."""
    print("\n" + "=" * 70)
    print("3. BULK OPERATIONS")
    print("=" * 70)

    # Create a collection of documents
    docs = [
        Document(
            text=f"This is document {i} about topic {i % 3}.",
            metadata={"doc_id": i, "topic": f"topic_{i % 3}", "category": "example"},
        )
        for i in range(5)
    ]

    # Bulk convert to TOON
    print("\n📤 Bulk Documents → TOON:")
    bulk_toon = bulk_documents_to_toon(docs)
    print(bulk_toon)

    # Convert back
    print("\n📥 TOON → Bulk Documents:")
    restored_docs = bulk_toon_to_documents(bulk_toon)
    print(f"✅ Restored {len(restored_docs)} documents")
    for i, doc in enumerate(restored_docs[:2]):  # Show first 2
        print(f"\nDoc {i}:")
        print(f"  Text: {doc.text}")
        print(f"  Metadata: {doc.metadata}")

    # Streaming for large collections
    print("\n📤 Streaming Large Collection (1000 docs):")
    large_docs = [
        Document(text=f"Document {i} content here.", metadata={"id": i, "batch": i // 100})
        for i in range(1000)
    ]

    chunk_count = 0
    for chunk_toon in stream_documents_to_toon(large_docs, chunk_size=200):
        chunk_count += 1

    print(f"✅ Streamed 1000 documents in {chunk_count} chunks (200 docs/chunk)")


# =============================================================================
# 4. METADATA EXTRACTION
# =============================================================================


def example_metadata_extraction():
    """Example: Extract and analyze metadata."""
    print("\n" + "=" * 70)
    print("4. METADATA EXTRACTION")
    print("=" * 70)

    # Create documents with rich metadata
    docs = [
        Document(
            text="Long document content here...",
            metadata={
                "filename": "report_2024.pdf",
                "page": 1,
                "section": "Executive Summary",
                "word_count": 523,
            },
        ),
        Document(
            text="Another document with lots of text...",
            metadata={
                "filename": "analysis_Q1.pdf",
                "page": 3,
                "section": "Findings",
                "word_count": 892,
            },
        ),
        Document(
            text="Third document content...",
            metadata={
                "filename": "proposal.docx",
                "page": 1,
                "section": "Introduction",
                "word_count": 345,
            },
        ),
    ]

    # Extract only metadata (ignore text content)
    print("\n📊 Extract Metadata Only:")
    metadata_toon = extract_metadata_to_toon(docs)
    print(metadata_toon)

    print("\n💡 Use case: Analyze document collection without loading full text")
    print("   - Faster processing for metadata-only queries")
    print("   - Reduced token usage when analyzing large corpora")


# =============================================================================
# 5. RAG PIPELINE EXAMPLE
# =============================================================================


def example_rag_pipeline():
    """Example: RAG pipeline with token optimization."""
    print("\n" + "=" * 70)
    print("5. RAG PIPELINE WITH TOKEN OPTIMIZATION")
    print("=" * 70)

    # Simulate a RAG pipeline: retrieve relevant documents
    print("\n🔍 Step 1: Retrieve relevant documents from vector DB")

    retrieved_docs = [
        Document(
            text="Python is a high-level programming language known for its readability.",
            metadata={
                "source": "python_guide.txt",
                "relevance_score": 0.95,
                "chunk_id": "chunk_42",
            },
        ),
        Document(
            text="LlamaIndex provides tools for ingesting, structuring, and accessing data.",
            metadata={
                "source": "llamaindex_docs.md",
                "relevance_score": 0.89,
                "chunk_id": "chunk_17",
            },
        ),
        Document(
            text="RAG (Retrieval-Augmented Generation) combines retrieval with LLM generation.",
            metadata={"source": "rag_tutorial.pdf", "relevance_score": 0.87, "chunk_id": "chunk_8"},
        ),
    ]

    print(f"✅ Retrieved {len(retrieved_docs)} documents\n")

    # Convert to TOON for efficient transmission/storage
    print("📦 Step 2: Convert to TOON for efficient processing")
    toon = bulk_documents_to_toon(retrieved_docs)
    print(toon)

    # Compare with JSON
    print("\n📊 Step 3: Compare token usage")
    import json
    from toonverter.analysis import count_tokens

    # Create JSON equivalent
    json_data = [{"text": doc.text, "metadata": doc.metadata} for doc in retrieved_docs]
    json_str = json.dumps(json_data, indent=2)

    toon_tokens = count_tokens(toon)
    json_tokens = count_tokens(json_str)
    savings = json_tokens - toon_tokens
    savings_pct = savings / json_tokens * 100

    print(f"\n💰 Token Savings for RAG Context:")
    print(f"  JSON format: {json_tokens} tokens")
    print(f"  TOON format: {toon_tokens} tokens")
    print(f"  Savings: {savings} tokens ({savings_pct:.1f}%)")

    print(f"\n💡 Impact on RAG Pipeline:")
    print(f"  - Fewer tokens sent to LLM = Lower API costs")
    print(f"  - More context fits in same token budget")
    print(f"  - Faster response times with less data to process")


# =============================================================================
# 6. DOCUMENT CHUNKING WORKFLOW
# =============================================================================


def example_document_chunking():
    """Example: Chunk large documents and preserve metadata."""
    print("\n" + "=" * 70)
    print("6. DOCUMENT CHUNKING WORKFLOW")
    print("=" * 70)

    # Simulate a large document split into chunks
    print("\n📄 Original Document → Chunks with TextNode:")

    original_text = """
    LlamaIndex is a data framework for LLM applications. It provides tools
    for data ingestion, indexing, and retrieval. The framework supports
    various data sources including PDFs, databases, and APIs.
    """

    # Create text nodes for chunks (simulating a chunking strategy)
    chunks = [
        TextNode(
            text="LlamaIndex is a data framework for LLM applications.",
            metadata={"source": "guide.txt", "chunk": 0, "total_chunks": 3},
            start_char_idx=0,
            end_char_idx=54,
        ),
        TextNode(
            text="It provides tools for data ingestion, indexing, and retrieval.",
            metadata={"source": "guide.txt", "chunk": 1, "total_chunks": 3},
            start_char_idx=55,
            end_char_idx=118,
        ),
        TextNode(
            text="The framework supports various data sources including PDFs, databases, and APIs.",
            metadata={"source": "guide.txt", "chunk": 2, "total_chunks": 3},
            start_char_idx=119,
            end_char_idx=200,
        ),
    ]

    # Convert to TOON
    toon = bulk_documents_to_toon(chunks)
    print(toon)

    print("\n✅ Benefits:")
    print("  - Preserves chunk boundaries (start_char_idx, end_char_idx)")
    print("  - Maintains metadata across all chunks")
    print("  - Efficient storage for large document collections")


# =============================================================================
# TOKEN SAVINGS ANALYSIS
# =============================================================================


def example_token_savings():
    """Example: Analyze token savings for different document sizes."""
    print("\n" + "=" * 70)
    print("7. TOKEN SAVINGS ANALYSIS")
    print("=" * 70)

    import json
    from toonverter.analysis import count_tokens

    test_cases = [
        ("Small (1 doc)", 1),
        ("Medium (10 docs)", 10),
        ("Large (100 docs)", 100),
        ("Very Large (1000 docs)", 1000),
    ]

    print("\n📊 Token Savings by Collection Size:\n")
    print(f"{'Collection Size':<20} {'JSON':<12} {'TOON':<12} {'Savings':<15}")
    print("-" * 70)

    for label, count in test_cases:
        # Create documents
        docs = [
            Document(
                text=f"This is document {i} with some content about topic {i % 5}.",
                metadata={"doc_id": i, "category": f"cat_{i % 5}", "priority": i % 3},
            )
            for i in range(count)
        ]

        # Convert to TOON
        toon = bulk_documents_to_toon(docs)

        # Convert to JSON
        json_data = [{"text": d.text, "metadata": d.metadata} for d in docs]
        json_str = json.dumps(json_data)

        # Count tokens
        toon_tokens = count_tokens(toon)
        json_tokens = count_tokens(json_str)
        savings = json_tokens - toon_tokens
        savings_pct = savings / json_tokens * 100

        print(f"{label:<20} {json_tokens:<12} {toon_tokens:<12} {savings} ({savings_pct:.1f}%)")


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run all examples."""
    print("\n" + "🚀 " + "=" * 66 + " 🚀")
    print("  TOONVERTER - LLAMAINDEX INTEGRATION EXAMPLES")
    print("🚀 " + "=" * 66 + " 🚀")

    example_document_conversion()
    example_node_serialization()
    example_bulk_operations()
    example_metadata_extraction()
    example_rag_pipeline()
    example_document_chunking()
    example_token_savings()

    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
