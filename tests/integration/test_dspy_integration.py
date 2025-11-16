"""Integration tests for DSPy support."""

import pytest


# Skip if dspy-ai not installed
pytest.importorskip("dspy")

from toonverter.integrations.dspy_integration import toon_to_dspy, dspy_to_toon


class TestDSPyExamples:
    """Test DSPy Example handling."""

    def test_example_to_toon(self):
        """Test converting DSPy Example to TOON."""
        try:
            import dspy

            example = dspy.Example(question="What is 2+2?", answer="4")

            toon = dspy_to_toon(example)

            assert "2+2" in toon
            assert "4" in toon
        except (ImportError, AttributeError):
            pytest.skip("DSPy Example not available")

    def test_example_roundtrip(self):
        """Test Example roundtrip."""
        try:
            import dspy

            example_original = dspy.Example(input="test input", output="test output")

            toon = dspy_to_toon(example_original)
            example_result = toon_to_dspy(toon)

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

            toon = dspy_to_toon(examples)

            assert "Q1" in toon
            assert "Q2" in toon
            assert "Q3" in toon
        except (ImportError, AttributeError):
            pytest.skip("DSPy not available")
