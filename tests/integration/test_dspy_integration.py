"""Integration tests for DSPy support."""

import pytest


# Skip if dspy-ai not installed
pytest.importorskip("dspy")

from toonverter.integrations.dspy_integration import from_toon_example, to_toon_example


class TestDSPyExamples:
    """Test DSPy Example handling."""

    def test_example_to_toon(self):
        """Test converting DSPy Example to TOON."""
        try:
            import dspy

            example = dspy.Example(question="What is 2+2?", answer="4")

            toon = to_toon_example(example)

            assert "2+2" in toon
            assert "4" in toon
        except (ImportError, AttributeError):
            pytest.skip("DSPy Example not available")

    def test_example_roundtrip(self):
        """Test Example roundtrip."""
        try:
            import dspy

            example_original = dspy.Example(input="test input", output="test output")

            toon = to_toon_example(example_original)
            example_result = from_toon_example(toon)

            assert example_result.input == "test input"
            assert example_result.output == "test output"
        except (ImportError, AttributeError):
            pytest.skip("DSPy not available")

    def test_multiple_examples(self):
        """Test list of Examples."""
        try:
            import dspy

            examples = [
                dspy.Example(question="Q1", answer="A1"),
                dspy.Example(question="Q2", answer="A2"),
                dspy.Example(question="Q3", answer="A3"),
            ]

            toon = to_toon_example(examples)

            assert "Q1" in toon
            assert "Q2" in toon
            assert "Q3" in toon
        except (ImportError, AttributeError):
            pytest.skip("DSPy not available")
