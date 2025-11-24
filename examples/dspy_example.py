"""DSPy Integration Example.

Demonstrates all features of toonverter's DSPy integration:
1. Example conversion and roundtrip
2. Dataset serialization for training data
3. Prediction caching
4. Few-shot learning optimization
5. Token savings analysis for prompts

Install dependencies:
    pip install toonverter[dspy]
"""

import dspy
from dspy import Example, Prediction

from toonverter.integrations.dspy import (
    dspy_to_toon,
    toon_to_dspy,
    dataset_to_toon,
    toon_to_dataset,
    stream_dataset_to_toon,
    predictions_to_toon,
    toon_to_predictions,
    few_shot_to_toon,
    signature_examples_to_toon,
    optimization_trace_to_toon,
)


# =============================================================================
# 1. EXAMPLE CONVERSION
# =============================================================================


def example_example_conversion():
    """Example: Convert DSPy Examples to/from TOON."""
    print("\n" + "=" * 70)
    print("1. EXAMPLE CONVERSION")
    print("=" * 70)

    # Create a simple QA example
    print("\n📝 Simple Example → TOON:")
    example = Example(question="What is the capital of France?", answer="Paris").with_inputs(
        "question"
    )

    toon = dspy_to_toon(example)
    print(toon)

    # Convert back
    print("\n📝 TOON → Example:")
    restored_example = toon_to_dspy(toon, with_inputs=["question"])
    print(f"Question: {restored_example.question}")
    print(f"Answer: {restored_example.answer}")

    # Create a multi-field example
    print("\n📝 Complex Example → TOON:")
    example2 = Example(
        context="Paris is the capital and largest city of France.",
        question="What is the capital of France?",
        answer="Paris",
        reasoning="The context explicitly states that Paris is the capital of France.",
        confidence=0.98,
    ).with_inputs("context", "question")

    toon2 = dspy_to_toon(example2)
    print(toon2)


# =============================================================================
# 2. DATASET SERIALIZATION
# =============================================================================


def example_dataset_serialization():
    """Example: Convert DSPy datasets to/from TOON."""
    print("\n" + "=" * 70)
    print("2. DATASET SERIALIZATION")
    print("=" * 70)

    # Create a training dataset
    print("\n📚 Training Dataset → TOON:")
    train_examples = [
        Example(question="What is 2+2?", answer="4").with_inputs("question"),
        Example(question="What is 3*5?", answer="15").with_inputs("question"),
        Example(question="What is 10-7?", answer="3").with_inputs("question"),
        Example(question="What is 12/4?", answer="3").with_inputs("question"),
        Example(question="What is 5+8?", answer="13").with_inputs("question"),
    ]

    toon = dataset_to_toon(train_examples)
    print(toon)

    # Convert back
    print("\n📚 TOON → Dataset:")
    restored_dataset = toon_to_dataset(toon, with_inputs=["question"])
    print(f"✅ Restored {len(restored_dataset)} examples")
    for i, ex in enumerate(restored_dataset[:2]):  # Show first 2
        print(f"\nExample {i + 1}:")
        print(f"  Q: {ex.question}")
        print(f"  A: {ex.answer}")

    # Streaming for large datasets
    print("\n📚 Streaming Large Dataset (1000 examples):")
    large_dataset = [
        Example(input=f"Input {i}", output=f"Output {i}", metadata={"id": i, "batch": i // 100})
        for i in range(1000)
    ]

    chunk_count = 0
    for chunk_toon in stream_dataset_to_toon(large_dataset, chunk_size=200):
        chunk_count += 1

    print(f"✅ Streamed 1000 examples in {chunk_count} chunks (200 examples/chunk)")


# =============================================================================
# 3. PREDICTION CACHING
# =============================================================================


def example_prediction_caching():
    """Example: Cache model predictions to/from TOON."""
    print("\n" + "=" * 70)
    print("3. PREDICTION CACHING")
    print("=" * 70)

    # Simulate model predictions
    print("\n🔮 Model Predictions → TOON:")
    predictions = [
        Prediction(
            answer="Paris",
            reasoning="France's capital is explicitly mentioned as Paris.",
            confidence=0.95,
        ),
        Prediction(
            answer="London",
            reasoning="The United Kingdom's capital city is London.",
            confidence=0.92,
        ),
        Prediction(
            answer="Berlin",
            reasoning="Germany's capital and largest city is Berlin.",
            confidence=0.89,
        ),
    ]

    toon = predictions_to_toon(predictions)
    print(toon)

    # Convert back
    print("\n🔮 TOON → Predictions:")
    restored_predictions = toon_to_predictions(toon)
    print(f"✅ Restored {len(restored_predictions)} predictions")
    for i, pred in enumerate(restored_predictions, 1):
        print(f"\nPrediction {i}:")
        print(f"  Answer: {pred.answer}")
        print(f"  Confidence: {pred.confidence}")
        print(f"  Reasoning: {pred.reasoning[:50]}...")

    print("\n💡 Use case: Cache predictions to avoid repeated API calls")


# =============================================================================
# 4. FEW-SHOT LEARNING
# =============================================================================


def example_few_shot_learning():
    """Example: Optimize few-shot examples with TOON."""
    print("\n" + "=" * 70)
    print("4. FEW-SHOT LEARNING OPTIMIZATION")
    print("=" * 70)

    # Create few-shot examples for sentiment analysis
    print("\n🎯 Few-shot Examples → TOON:")
    few_shot_examples = [
        Example(text="This movie was absolutely fantastic!", sentiment="positive"),
        Example(text="I really enjoyed the performance.", sentiment="positive"),
        Example(text="This was a waste of time and money.", sentiment="negative"),
        Example(text="Terrible experience, would not recommend.", sentiment="negative"),
        Example(text="It was okay, nothing special.", sentiment="neutral"),
    ]

    # Convert to TOON for minimal token usage in prompts
    toon = few_shot_to_toon(few_shot_examples, max_examples=3)
    print(toon)

    print("\n💡 Benefits:")
    print("  - Compact format reduces prompt tokens")
    print("  - More examples fit in context window")
    print("  - Lower API costs for few-shot learning")


# =============================================================================
# 5. SIGNATURE EXAMPLES
# =============================================================================


def example_signature_examples():
    """Example: Store signature-specific examples."""
    print("\n" + "=" * 70)
    print("5. SIGNATURE EXAMPLES")
    print("=" * 70)

    # Create examples for a QA signature
    print("\n📋 QA Signature Examples → TOON:")
    qa_examples = [
        Example(
            context="The Eiffel Tower is located in Paris, France.",
            question="Where is the Eiffel Tower?",
            answer="Paris, France",
        ),
        Example(
            context="Python was created by Guido van Rossum in 1991.",
            question="Who created Python?",
            answer="Guido van Rossum",
        ),
        Example(
            context="The speed of light is approximately 299,792 km/s.",
            question="What is the speed of light?",
            answer="299,792 km/s",
        ),
    ]

    toon = signature_examples_to_toon("QuestionAnswering", qa_examples)
    print(toon)


# =============================================================================
# 6. OPTIMIZATION TRACES
# =============================================================================


def example_optimization_traces():
    """Example: Store DSPy optimization history."""
    print("\n" + "=" * 70)
    print("6. OPTIMIZATION TRACES")
    print("=" * 70)

    # Simulate an optimization trace
    print("\n📊 Optimization History → TOON:")
    trace = [
        {
            "step": 1,
            "score": 0.65,
            "metric": "accuracy",
            "hyperparams": {"temperature": 0.7, "max_tokens": 100},
        },
        {
            "step": 2,
            "score": 0.78,
            "metric": "accuracy",
            "hyperparams": {"temperature": 0.5, "max_tokens": 150},
        },
        {
            "step": 3,
            "score": 0.85,
            "metric": "accuracy",
            "hyperparams": {"temperature": 0.3, "max_tokens": 120},
        },
        {
            "step": 4,
            "score": 0.91,
            "metric": "accuracy",
            "hyperparams": {"temperature": 0.3, "max_tokens": 100},
        },
    ]

    toon = optimization_trace_to_toon(trace)
    print(toon)

    print("\n💡 Use case: Track and analyze optimization runs")
    print("  - Compare different hyperparameter configurations")
    print("  - Store optimization history efficiently")
    print("  - Reproduce best-performing models")


# =============================================================================
# 7. TOKEN SAVINGS ANALYSIS
# =============================================================================


def example_token_savings():
    """Example: Analyze token savings for DSPy workflows."""
    print("\n" + "=" * 70)
    print("7. TOKEN SAVINGS ANALYSIS")
    print("=" * 70)

    import json
    from toonverter.analysis import count_tokens

    test_cases = [
        ("Small Dataset (10 examples)", 10),
        ("Medium Dataset (50 examples)", 50),
        ("Large Dataset (200 examples)", 200),
        ("Very Large Dataset (1000 examples)", 1000),
    ]

    print("\n📊 Token Savings by Dataset Size:\n")
    print(f"{'Dataset Size':<30} {'JSON':<12} {'TOON':<12} {'Savings':<15}")
    print("-" * 70)

    for label, count in test_cases:
        # Create examples
        examples = [
            Example(
                question=f"What is the result of calculation {i}?",
                context=f"Given the numbers {i} and {i + 1}, perform the operation.",
                answer=f"The answer is {i * 2}",
                reasoning=f"By calculating {i} * 2, we get {i * 2}",
            )
            for i in range(count)
        ]

        # Convert to TOON
        toon = dataset_to_toon(examples)

        # Convert to JSON
        json_data = [
            {
                "question": ex.question,
                "context": ex.context,
                "answer": ex.answer,
                "reasoning": ex.reasoning,
            }
            for ex in examples
        ]
        json_str = json.dumps(json_data)

        # Count tokens
        toon_tokens = count_tokens(toon)
        json_tokens = count_tokens(json_str)
        savings = json_tokens - toon_tokens
        savings_pct = savings / json_tokens * 100

        print(f"{label:<30} {json_tokens:<12} {toon_tokens:<12} {savings} ({savings_pct:.1f}%)")


# =============================================================================
# 8. PROMPT OPTIMIZATION
# =============================================================================


def example_prompt_optimization():
    """Example: Optimize prompts with TOON format."""
    print("\n" + "=" * 70)
    print("8. PROMPT OPTIMIZATION FOR FEW-SHOT")
    print("=" * 70)

    # Create training examples for classification
    print("\n🎯 Scenario: Optimize few-shot prompt for text classification")

    examples = [
        Example(text="Great product, highly recommend!", label="positive"),
        Example(text="Terrible quality, broke after one use.", label="negative"),
        Example(text="Average product, nothing special.", label="neutral"),
        Example(text="Exceeded my expectations!", label="positive"),
        Example(text="Complete waste of money.", label="negative"),
    ]

    # Compare JSON vs TOON for prompt inclusion
    import json
    from toonverter.analysis import count_tokens

    # JSON representation
    json_examples = [{"text": ex.text, "label": ex.label} for ex in examples]
    json_str = json.dumps(json_examples, indent=2)

    # TOON representation
    toon_str = few_shot_to_toon(examples)

    json_tokens = count_tokens(json_str)
    toon_tokens = count_tokens(toon_str)
    savings = json_tokens - toon_tokens
    savings_pct = savings / json_tokens * 100

    print(f"\n📋 JSON Format ({json_tokens} tokens):")
    print(json_str[:200] + "...")

    print(f"\n📋 TOON Format ({toon_tokens} tokens):")
    print(toon_str[:200] + "...")

    print(f"\n💰 Prompt Token Savings:")
    print(f"  JSON: {json_tokens} tokens")
    print(f"  TOON: {toon_tokens} tokens")
    print(f"  Savings: {savings} tokens ({savings_pct:.1f}%)")

    print(f"\n💡 Impact:")
    print(f"  - Fit more examples in context window")
    print(f"  - Lower API costs per prompt")
    print(f"  - Faster model responses")


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run all examples."""
    print("\n" + "🚀 " + "=" * 66 + " 🚀")
    print("  TOONVERTER - DSPY INTEGRATION EXAMPLES")
    print("🚀 " + "=" * 66 + " 🚀")

    example_example_conversion()
    example_dataset_serialization()
    example_prediction_caching()
    example_few_shot_learning()
    example_signature_examples()
    example_optimization_traces()
    example_token_savings()
    example_prompt_optimization()

    print("\n" + "=" * 70)
    print("✅ All examples completed successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
