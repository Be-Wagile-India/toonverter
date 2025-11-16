"""Instructor Integration Example.

Demonstrates all features of toonverter's Instructor integration:
1. Response model conversion and roundtrip
2. Bulk response processing
3. Schema export
4. Extraction batch handling
5. Response caching with TOON
6. Token savings analysis

Install dependencies:
    pip install toonverter[instructor]
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

from toonverter.integrations.instructor_integration import (
    response_to_toon,
    toon_to_response,
    bulk_responses_to_toon,
    bulk_toon_to_responses,
    stream_responses_to_toon,
    schema_to_toon,
    validation_results_to_toon,
    extraction_batch_to_toon,
    toon_to_extraction_batch,
    cache_response,
)


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class User(BaseModel):
    """User information model."""
    name: str = Field(description="Full name of the user")
    age: int = Field(description="Age in years", gt=0, lt=150)
    email: str = Field(description="Email address")
    bio: Optional[str] = Field(default=None, description="User biography")


class Entity(BaseModel):
    """Named entity extraction model."""
    text: str = Field(description="Entity text")
    type: str = Field(description="Entity type (person, organization, location, etc.)")
    confidence: float = Field(description="Extraction confidence", ge=0.0, le=1.0)
    context: Optional[str] = Field(default=None, description="Surrounding context")


class SentimentAnalysis(BaseModel):
    """Sentiment analysis result model."""
    text: str = Field(description="Input text")
    sentiment: str = Field(description="Sentiment label (positive, negative, neutral)")
    confidence: float = Field(description="Confidence score", ge=0.0, le=1.0)
    emotions: List[str] = Field(default_factory=list, description="Detected emotions")


class QAPair(BaseModel):
    """Question-answer pair model."""
    question: str = Field(description="Question text")
    answer: str = Field(description="Answer text")
    source: Optional[str] = Field(default=None, description="Source document")
    confidence: float = Field(default=1.0, description="Answer confidence")


# =============================================================================
# 1. RESPONSE MODEL CONVERSION
# =============================================================================

def example_response_conversion():
    """Example: Convert Instructor responses to/from TOON."""
    print("\n" + "="*70)
    print("1. RESPONSE MODEL CONVERSION")
    print("="*70)

    # Create a simple response
    print("\n📄 Simple Response → TOON:")
    user = User(
        name="Alice Johnson",
        age=30,
        email="alice@example.com",
        bio="Software engineer with 10 years of experience"
    )

    toon = response_to_toon(user)
    print(toon)

    # Convert back
    print("\n📄 TOON → Response:")
    restored_user = toon_to_response(toon, User)
    print(f"Name: {restored_user.name}")
    print(f"Email: {restored_user.email}")
    print(f"Bio: {restored_user.bio}")

    # With metadata
    print("\n📄 Response with Metadata → TOON:")
    toon_with_meta = response_to_toon(user, include_metadata=True)
    print(toon_with_meta)


# =============================================================================
# 2. BULK OPERATIONS
# =============================================================================

def example_bulk_operations():
    """Example: Convert multiple responses efficiently."""
    print("\n" + "="*70)
    print("2. BULK OPERATIONS")
    print("="*70)

    # Create a collection of responses
    users = [
        User(name="Alice", age=30, email="alice@example.com"),
        User(name="Bob", age=25, email="bob@example.com"),
        User(name="Carol", age=35, email="carol@example.com"),
        User(name="Dave", age=28, email="dave@example.com"),
        User(name="Eve", age=32, email="eve@example.com"),
    ]

    # Bulk convert to TOON
    print("\n📤 Bulk Responses → TOON:")
    bulk_toon = bulk_responses_to_toon(users)
    print(bulk_toon)

    # Convert back
    print("\n📥 TOON → Bulk Responses:")
    restored_users = bulk_toon_to_responses(bulk_toon, User)
    print(f"✅ Restored {len(restored_users)} users")
    for i, user in enumerate(restored_users[:2]):  # Show first 2
        print(f"\nUser {i + 1}:")
        print(f"  Name: {user.name}")
        print(f"  Email: {user.email}")

    # Streaming for large collections
    print("\n📤 Streaming Large Collection (1000 responses):")
    large_responses = [
        User(
            name=f"User {i}",
            age=20 + (i % 50),
            email=f"user{i}@example.com"
        )
        for i in range(1000)
    ]

    chunk_count = 0
    for chunk_toon in stream_responses_to_toon(large_responses, chunk_size=200):
        chunk_count += 1

    print(f"✅ Streamed 1000 responses in {chunk_count} chunks (200 responses/chunk)")


# =============================================================================
# 3. SCHEMA EXPORT
# =============================================================================

def example_schema_export():
    """Example: Export Pydantic schemas to TOON."""
    print("\n" + "="*70)
    print("3. SCHEMA EXPORT")
    print("="*70)

    # Export User schema
    print("\n📋 User Model Schema → TOON:")
    user_schema = schema_to_toon(User)
    print(user_schema[:300] + "...\n(truncated)")

    # Export Entity schema
    print("\n📋 Entity Model Schema → TOON:")
    entity_schema = schema_to_toon(Entity)
    print(entity_schema[:300] + "...\n(truncated)")

    print("\n💡 Use case: Share model schemas with other services")


# =============================================================================
# 4. ENTITY EXTRACTION BATCH
# =============================================================================

def example_extraction_batch():
    """Example: Handle batch entity extraction results."""
    print("\n" + "="*70)
    print("4. ENTITY EXTRACTION BATCH")
    print("="*70)

    # Simulate entity extraction from text
    print("\n🔍 Text: 'Apple and Google announced partnership in San Francisco.'")
    print("\n📊 Extracted Entities → TOON:")

    entities = [
        Entity(text="Apple", type="organization", confidence=0.95, context="announced partnership"),
        Entity(text="Google", type="organization", confidence=0.93, context="announced partnership"),
        Entity(text="San Francisco", type="location", confidence=0.89, context="partnership in")
    ]

    toon = extraction_batch_to_toon(
        entities,
        source_metadata={
            "document": "tech_news.txt",
            "date": "2024-01-15",
            "model": "instructor-large"
        }
    )
    print(toon)

    # Convert back
    print("\n📥 TOON → Extraction Batch:")
    result = toon_to_extraction_batch(toon, Entity)
    print(f"✅ Extracted {result['count']} entities")
    print(f"Source: {result['metadata']['document']}")

    for entity in result['extractions']:
        print(f"\n  [{entity.type}] {entity.text} (confidence: {entity.confidence})")


# =============================================================================
# 5. RESPONSE CACHING
# =============================================================================

def example_response_caching():
    """Example: Cache responses with TOON format."""
    print("\n" + "="*70)
    print("5. RESPONSE CACHING")
    print("="*70)

    # Create response to cache
    user = User(
        name="Alice Johnson",
        age=30,
        email="alice@example.com",
        bio="Software engineer"
    )

    # Create cache entry
    print("\n💾 Creating Cache Entry:")
    cache_entry = cache_response(user, "user:alice:profile", ttl=3600)

    print(f"Cache Key: {cache_entry['key']}")
    print(f"Model: {cache_entry['model']}")
    print(f"TTL: {cache_entry['ttl']} seconds")
    print(f"\nCached TOON data:")
    print(cache_entry['toon'][:150] + "...")

    print("\n💡 Use case: Cache LLM responses to reduce API calls")
    print("  - Store in Redis/Memcached with TTL")
    print("  - 40-60% smaller than JSON")
    print("  - Faster serialization/deserialization")


# =============================================================================
# 6. SENTIMENT ANALYSIS WORKFLOW
# =============================================================================

def example_sentiment_workflow():
    """Example: Sentiment analysis with Instructor + TOON."""
    print("\n" + "="*70)
    print("6. SENTIMENT ANALYSIS WORKFLOW")
    print("="*70)

    # Simulate sentiment analysis results
    print("\n📊 Batch Sentiment Analysis → TOON:")
    analyses = [
        SentimentAnalysis(
            text="This product is amazing! Highly recommend.",
            sentiment="positive",
            confidence=0.95,
            emotions=["joy", "satisfaction"]
        ),
        SentimentAnalysis(
            text="Terrible experience, very disappointed.",
            sentiment="negative",
            confidence=0.92,
            emotions=["anger", "disappointment"]
        ),
        SentimentAnalysis(
            text="It's okay, nothing special.",
            sentiment="neutral",
            confidence=0.78,
            emotions=["indifference"]
        ),
        SentimentAnalysis(
            text="Absolutely love it! Best purchase ever!",
            sentiment="positive",
            confidence=0.98,
            emotions=["joy", "excitement"]
        )
    ]

    toon = bulk_responses_to_toon(analyses)
    print(toon)

    print("\n💡 Benefits:")
    print("  - Compact storage for analysis results")
    print("  - Easy to cache and retrieve")
    print("  - Reduced database storage costs")


# =============================================================================
# 7. QA EXTRACTION
# =============================================================================

def example_qa_extraction():
    """Example: Extract and store Q&A pairs."""
    print("\n" + "="*70)
    print("7. QA EXTRACTION")
    print("="*70)

    # Simulate Q&A extraction from documents
    print("\n❓ Extracted Q&A Pairs → TOON:")
    qa_pairs = [
        QAPair(
            question="What is Python?",
            answer="Python is a high-level programming language known for its simplicity and readability.",
            source="python_guide.txt",
            confidence=0.95
        ),
        QAPair(
            question="Who created Python?",
            answer="Python was created by Guido van Rossum in 1991.",
            source="python_history.txt",
            confidence=0.98
        ),
        QAPair(
            question="What is Python used for?",
            answer="Python is used for web development, data science, AI, automation, and more.",
            source="python_applications.txt",
            confidence=0.92
        )
    ]

    toon = bulk_responses_to_toon(qa_pairs)
    print(toon)

    print("\n💡 Use case: Build Q&A knowledge bases efficiently")
    print("  - Extract from documentation")
    print("  - Store in compact format")
    print("  - Fast retrieval for chatbots")


# =============================================================================
# 8. TOKEN SAVINGS ANALYSIS
# =============================================================================

def example_token_savings():
    """Example: Analyze token savings for Instructor responses."""
    print("\n" + "="*70)
    print("8. TOKEN SAVINGS ANALYSIS")
    print("="*70)

    import json
    from toonverter.analysis import count_tokens

    test_cases = [
        ("Small (10 responses)", 10),
        ("Medium (50 responses)", 50),
        ("Large (200 responses)", 200),
        ("Very Large (1000 responses)", 1000)
    ]

    print("\n📊 Token Savings by Response Count:\n")
    print(f"{'Response Count':<25} {'JSON':<12} {'TOON':<12} {'Savings':<15}")
    print("-" * 70)

    for label, count in test_cases:
        # Create responses
        users = [
            User(
                name=f"User {i}",
                age=20 + (i % 50),
                email=f"user{i}@example.com",
                bio=f"Bio for user {i} with some additional information."
            )
            for i in range(count)
        ]

        # Convert to TOON
        toon = bulk_responses_to_toon(users)

        # Convert to JSON
        json_data = [user.model_dump() for user in users]
        json_str = json.dumps(json_data)

        # Count tokens
        toon_tokens = count_tokens(toon)
        json_tokens = count_tokens(json_str)
        savings = json_tokens - toon_tokens
        savings_pct = (savings / json_tokens * 100)

        print(f"{label:<25} {json_tokens:<12} {toon_tokens:<12} {savings} ({savings_pct:.1f}%)")


# =============================================================================
# 9. VALIDATION RESULTS
# =============================================================================

def example_validation_results():
    """Example: Store validation errors."""
    print("\n" + "="*70)
    print("9. VALIDATION RESULTS")
    print("="*70)

    # Simulate validation errors
    print("\n❌ Validation Errors → TOON:")
    validation_errors = [
        {
            "field": "age",
            "error": "must be greater than 0",
            "value": -5,
            "input": {"name": "Alice", "age": -5}
        },
        {
            "field": "email",
            "error": "invalid email format",
            "value": "not-an-email",
            "input": {"name": "Bob", "email": "not-an-email"}
        },
        {
            "field": "confidence",
            "error": "must be between 0.0 and 1.0",
            "value": 1.5,
            "input": {"text": "Test", "confidence": 1.5}
        }
    ]

    toon = validation_results_to_toon(validation_errors)
    print(toon)

    print("\n💡 Use case: Debug and log validation failures")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run all examples."""
    print("\n" + "🚀 " + "="*66 + " 🚀")
    print("  TOONVERTER - INSTRUCTOR INTEGRATION EXAMPLES")
    print("🚀 " + "="*66 + " 🚀")

    example_response_conversion()
    example_bulk_operations()
    example_schema_export()
    example_extraction_batch()
    example_response_caching()
    example_sentiment_workflow()
    example_qa_extraction()
    example_token_savings()
    example_validation_results()

    print("\n" + "="*70)
    print("✅ All examples completed successfully!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
