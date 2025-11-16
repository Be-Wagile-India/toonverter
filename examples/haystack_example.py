"""Haystack Integration Example.

Demonstrates all features of toonverter's Haystack integration:
1. Document conversion and roundtrip
2. Answer serialization for QA caching
3. Bulk operations for large document collections
4. Metadata extraction
5. Token savings analysis for search pipelines

Install dependencies:
    pip install toonverter[haystack]
"""

from haystack import Document
from haystack.schema import Answer, Span

from toonverter.integrations.haystack import (
    haystack_to_toon,
    toon_to_haystack,
    bulk_documents_to_toon,
    bulk_toon_to_documents,
    stream_documents_to_toon,
    answers_to_toon,
    toon_to_answers,
    extract_metadata_to_toon,
)


# =============================================================================
# 1. DOCUMENT CONVERSION
# =============================================================================

def example_document_conversion():
    """Example: Convert Haystack Documents to/from TOON."""
    print("\n" + "="*70)
    print("1. DOCUMENT CONVERSION")
    print("="*70)

    # Create a simple document
    print("\n📄 Simple Document → TOON:")
    doc = Document(
        content="Haystack is an open-source framework for building NLP applications.",
        meta={
            "source": "haystack_docs.txt",
            "section": "Introduction",
            "page": 1
        }
    )

    toon = haystack_to_toon(doc)
    print(toon)

    # Convert back
    print("\n📄 TOON → Document:")
    restored_doc = toon_to_haystack(toon)
    print(f"Content: {restored_doc.content}")
    print(f"Meta: {restored_doc.meta}")

    # Create document with score
    print("\n📄 Document with Score → TOON:")
    doc2 = Document(
        content="Neural networks are computational models inspired by biological brains.",
        meta={
            "title": "Neural Networks 101",
            "author": "Dr. Johnson",
            "category": "AI"
        },
        score=0.95
    )

    toon2 = haystack_to_toon(doc2)
    print(toon2)

    # Different content types
    print("\n📄 Table Document → TOON:")
    doc3 = Document(
        content="Name,Age,City\nAlice,30,NYC\nBob,25,LA",
        content_type="table",
        meta={"format": "csv"}
    )

    toon3 = haystack_to_toon(doc3)
    print(toon3)


# =============================================================================
# 2. ANSWER SERIALIZATION
# =============================================================================

def example_answer_serialization():
    """Example: Convert QA answers to/from TOON."""
    print("\n" + "="*70)
    print("2. ANSWER SERIALIZATION (QA CACHING)")
    print("="*70)

    # Create answers from a QA pipeline
    print("\n💬 Question: 'What is the capital of France?'")
    print("📝 QA Pipeline Results → TOON:\n")

    answers = [
        Answer(
            answer="Paris",
            type="extractive",
            score=0.95,
            context="The capital of France is Paris, known for the Eiffel Tower.",
            offsets_in_document=[Span(start=23, end=28)],
            offsets_in_context=[Span(start=23, end=28)],
            document_id="doc_france_001",
            meta={"source": "geography.txt"}
        ),
        Answer(
            answer="Paris",
            type="extractive",
            score=0.87,
            context="Paris, the capital city of France, has a population of 2.1 million.",
            offsets_in_document=[Span(start=0, end=5)],
            offsets_in_context=[Span(start=0, end=5)],
            document_id="doc_france_002",
            meta={"source": "demographics.txt"}
        )
    ]

    toon = answers_to_toon(answers)
    print(toon)

    # Convert back
    print("\n📥 TOON → Answers:")
    restored_answers = toon_to_answers(toon)
    print(f"✅ Restored {len(restored_answers)} answers")
    for i, ans in enumerate(restored_answers, 1):
        print(f"\nAnswer {i}:")
        print(f"  Text: {ans.answer}")
        print(f"  Score: {ans.score}")
        print(f"  Context: {ans.context[:50]}...")

    print("\n💡 Use case: Cache QA results in TOON for 40-60% token savings")


# =============================================================================
# 3. BULK OPERATIONS
# =============================================================================

def example_bulk_operations():
    """Example: Convert multiple documents efficiently."""
    print("\n" + "="*70)
    print("3. BULK OPERATIONS")
    print("="*70)

    # Create a collection of documents
    docs = [
        Document(
            content=f"This is document {i} about machine learning topic {i % 3}.",
            meta={
                "doc_id": i,
                "topic": f"ml_topic_{i % 3}",
                "date": f"2024-01-{(i % 30) + 1:02d}"
            },
            score=0.9 - (i * 0.05)
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
        print(f"  Content: {doc.content}")
        print(f"  Meta: {doc.meta}")
        print(f"  Score: {doc.score}")

    # Streaming for large collections
    print("\n📤 Streaming Large Collection (1000 docs):")
    large_docs = [
        Document(
            content=f"Document {i} content here.",
            meta={"id": i, "batch": i // 100}
        )
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
    print("\n" + "="*70)
    print("4. METADATA EXTRACTION")
    print("="*70)

    # Create documents with rich metadata
    docs = [
        Document(
            content="Long research paper content...",
            meta={
                "filename": "paper_2024.pdf",
                "page": 1,
                "section": "Abstract",
                "keywords": ["AI", "ML", "NLP"],
                "citations": 42
            }
        ),
        Document(
            content="Another document with lots of text...",
            meta={
                "filename": "report_Q1.pdf",
                "page": 5,
                "section": "Results",
                "keywords": ["Analysis", "Data"],
                "citations": 17
            }
        ),
        Document(
            content="Third document content...",
            meta={
                "filename": "thesis.docx",
                "page": 12,
                "section": "Methodology",
                "keywords": ["Research", "Experiments"],
                "citations": 89
            }
        )
    ]

    # Extract only metadata (ignore content)
    print("\n📊 Extract Metadata Only:")
    metadata_toon = extract_metadata_to_toon(docs)
    print(metadata_toon)

    print("\n💡 Use case: Analyze document collection without loading full content")
    print("   - Faster processing for metadata-only queries")
    print("   - Reduced token usage when analyzing large corpora")


# =============================================================================
# 5. SEARCH PIPELINE EXAMPLE
# =============================================================================

def example_search_pipeline():
    """Example: Search pipeline with token optimization."""
    print("\n" + "="*70)
    print("5. SEARCH PIPELINE WITH TOKEN OPTIMIZATION")
    print("="*70)

    # Simulate a search pipeline: retrieve relevant documents
    print("\n🔍 Step 1: Search query: 'machine learning frameworks'")
    print("📚 Retrieved documents from search index:\n")

    retrieved_docs = [
        Document(
            content="TensorFlow is an open-source machine learning framework developed by Google.",
            meta={
                "source": "tensorflow_guide.txt",
                "relevance_score": 0.92,
                "doc_id": "tf_001"
            },
            score=0.92
        ),
        Document(
            content="PyTorch is a popular machine learning library for Python and deep learning.",
            meta={
                "source": "pytorch_docs.md",
                "relevance_score": 0.89,
                "doc_id": "pt_002"
            },
            score=0.89
        ),
        Document(
            content="Scikit-learn provides simple tools for machine learning in Python.",
            meta={
                "source": "sklearn_intro.txt",
                "relevance_score": 0.85,
                "doc_id": "sk_003"
            },
            score=0.85
        )
    ]

    for doc in retrieved_docs:
        print(f"  [{doc.score:.2f}] {doc.content[:60]}...")

    # Convert to TOON for efficient transmission/storage
    print("\n📦 Step 2: Convert to TOON for efficient processing")
    toon = bulk_documents_to_toon(retrieved_docs)
    print(toon)

    # Compare with JSON
    print("\n📊 Step 3: Compare token usage")
    import json
    from toonverter.analysis import count_tokens

    # Create JSON equivalent
    json_data = [
        {
            "content": doc.content,
            "meta": doc.meta,
            "score": doc.score
        }
        for doc in retrieved_docs
    ]
    json_str = json.dumps(json_data, indent=2)

    toon_tokens = count_tokens(toon)
    json_tokens = count_tokens(json_str)
    savings = json_tokens - toon_tokens
    savings_pct = (savings / json_tokens * 100)

    print(f"\n💰 Token Savings for Search Results:")
    print(f"  JSON format: {json_tokens} tokens")
    print(f"  TOON format: {toon_tokens} tokens")
    print(f"  Savings: {savings} tokens ({savings_pct:.1f}%)")

    print(f"\n💡 Impact on Search Pipeline:")
    print(f"  - Fewer tokens sent to LLM = Lower API costs")
    print(f"  - More search results fit in same token budget")
    print(f"  - Faster response times with less data to process")


# =============================================================================
# 6. QA PIPELINE CACHING
# =============================================================================

def example_qa_caching():
    """Example: Cache QA results for faster responses."""
    print("\n" + "="*70)
    print("6. QA PIPELINE CACHING")
    print("="*70)

    print("\n💾 Scenario: Cache frequently asked questions")

    # Simulate common QA pairs
    qa_cache = {
        "What is Haystack?": [
            Answer(
                answer="Haystack is an open-source framework for building search systems and QA applications",
                type="extractive",
                score=0.98,
                context="Haystack is an open-source framework for building search systems and QA applications powered by LLMs.",
                document_id="haystack_intro"
            )
        ],
        "How to install Haystack?": [
            Answer(
                answer="pip install farm-haystack",
                type="extractive",
                score=0.95,
                context="To install Haystack, run: pip install farm-haystack",
                document_id="haystack_install"
            )
        ],
        "What databases does Haystack support?": [
            Answer(
                answer="Elasticsearch, OpenSearch, Weaviate, Pinecone, and more",
                type="extractive",
                score=0.92,
                context="Haystack supports multiple document stores including Elasticsearch, OpenSearch, Weaviate, Pinecone, and more.",
                document_id="haystack_databases"
            )
        ]
    }

    # Convert cache to TOON
    print("\n📤 Converting QA cache to TOON format:")
    toon_cache = {}
    total_json_tokens = 0
    total_toon_tokens = 0

    import json
    from toonverter.analysis import count_tokens

    for question, answers in qa_cache.items():
        # Convert to TOON
        toon = answers_to_toon(answers)
        toon_cache[question] = toon

        # Compare with JSON
        json_str = json.dumps([{
            "answer": a.answer,
            "score": a.score,
            "context": a.context
        } for a in answers])

        toon_tokens = count_tokens(toon)
        json_tokens = count_tokens(json_str)
        total_json_tokens += json_tokens
        total_toon_tokens += toon_tokens

        print(f"\n  Q: {question}")
        print(f"     JSON: {json_tokens} tokens | TOON: {toon_tokens} tokens")

    savings = total_json_tokens - total_toon_tokens
    savings_pct = (savings / total_json_tokens * 100)

    print(f"\n💰 Total Cache Savings:")
    print(f"  JSON format: {total_json_tokens} tokens")
    print(f"  TOON format: {total_toon_tokens} tokens")
    print(f"  Savings: {savings} tokens ({savings_pct:.1f}%)")


# =============================================================================
# TOKEN SAVINGS ANALYSIS
# =============================================================================

def example_token_savings():
    """Example: Analyze token savings for different collection sizes."""
    print("\n" + "="*70)
    print("7. TOKEN SAVINGS ANALYSIS")
    print("="*70)

    import json
    from toonverter.analysis import count_tokens

    test_cases = [
        ("Small (1 doc)", 1),
        ("Medium (10 docs)", 10),
        ("Large (100 docs)", 100),
        ("Very Large (1000 docs)", 1000)
    ]

    print("\n📊 Token Savings by Collection Size:\n")
    print(f"{'Collection Size':<20} {'JSON':<12} {'TOON':<12} {'Savings':<15}")
    print("-" * 70)

    for label, count in test_cases:
        # Create documents
        docs = [
            Document(
                content=f"This is document {i} with content about search topic {i % 5}.",
                meta={
                    "doc_id": i,
                    "category": f"cat_{i % 5}",
                    "priority": i % 3
                },
                score=0.9 - (i * 0.001)
            )
            for i in range(count)
        ]

        # Convert to TOON
        toon = bulk_documents_to_toon(docs)

        # Convert to JSON
        json_data = [
            {"content": d.content, "meta": d.meta, "score": d.score}
            for d in docs
        ]
        json_str = json.dumps(json_data)

        # Count tokens
        toon_tokens = count_tokens(toon)
        json_tokens = count_tokens(json_str)
        savings = json_tokens - toon_tokens
        savings_pct = (savings / json_tokens * 100)

        print(f"{label:<20} {json_tokens:<12} {toon_tokens:<12} {savings} ({savings_pct:.1f}%)")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "🚀 " + "="*66 + " 🚀")
    print("  TOONVERTER - HAYSTACK INTEGRATION EXAMPLES")
    print("🚀 " + "="*66 + " 🚀")

    example_document_conversion()
    example_answer_serialization()
    example_bulk_operations()
    example_metadata_extraction()
    example_search_pipeline()
    example_qa_caching()
    example_token_savings()

    print("\n" + "="*70)
    print("✅ All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
