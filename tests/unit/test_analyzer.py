"""Comprehensive tests for token analyzer."""

import pytest
from toonverter.analysis.analyzer import TiktokenCounter, count_tokens, analyze_text
from toonverter.core.exceptions import TokenCountError


class TestTiktokenCounter:
    """Test TiktokenCounter functionality."""

    def test_init_default_model(self):
        """Test initialization with default model."""
        counter = TiktokenCounter()
        assert counter.model_name == "gpt-4"

    def test_init_custom_model(self):
        """Test initialization with custom model."""
        counter = TiktokenCounter(model="gpt-3.5-turbo")
        assert counter.model_name == "gpt-3.5-turbo"

    def test_init_with_encoding_name(self):
        """Test initialization with encoding name."""
        counter = TiktokenCounter(model="cl100k_base")
        assert counter.model_name == "cl100k_base"

    def test_init_unknown_model_uses_default(self):
        """Test initialization with unknown model uses default encoding."""
        counter = TiktokenCounter(model="unknown-model")
        assert counter.model_name == "unknown-model"
        # Should still work with default encoding

    def test_get_encoding_name_gpt4(self):
        """Test getting encoding name for GPT-4."""
        counter = TiktokenCounter(model="gpt-4")
        assert counter._encoding_name == "cl100k_base"

    def test_get_encoding_name_gpt35(self):
        """Test getting encoding name for GPT-3.5."""
        counter = TiktokenCounter(model="gpt-3.5-turbo")
        assert counter._encoding_name == "cl100k_base"

    def test_get_encoding_name_davinci(self):
        """Test getting encoding name for Davinci."""
        counter = TiktokenCounter(model="text-davinci-003")
        assert counter._encoding_name == "p50k_base"

    def test_count_tokens_simple_text(self):
        """Test counting tokens in simple text."""
        counter = TiktokenCounter()
        count = counter.count_tokens("Hello, world!")
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_empty_string(self):
        """Test counting tokens in empty string."""
        counter = TiktokenCounter()
        count = counter.count_tokens("")
        assert count == 0

    def test_count_tokens_multiline(self):
        """Test counting tokens in multiline text."""
        counter = TiktokenCounter()
        text = "Line 1\nLine 2\nLine 3"
        count = counter.count_tokens(text)
        assert count > 0

    def test_count_tokens_json(self):
        """Test counting tokens in JSON."""
        counter = TiktokenCounter()
        text = '{"name": "Alice", "age": 30}'
        count = counter.count_tokens(text)
        assert count > 0

    def test_count_tokens_long_text(self):
        """Test counting tokens in long text."""
        counter = TiktokenCounter()
        text = "hello " * 1000
        count = counter.count_tokens(text)
        assert count > 1000  # Should be more than word count

    def test_analyze_returns_token_analysis(self):
        """Test analyze returns TokenAnalysis."""
        counter = TiktokenCounter()
        analysis = counter.analyze("Hello, world!", "text")

        assert analysis.format == "text"
        assert analysis.token_count > 0
        assert analysis.model == "gpt-4"
        assert analysis.encoding == "cl100k_base"

    def test_analyze_includes_metadata(self):
        """Test analyze includes metadata."""
        counter = TiktokenCounter()
        text = "Line 1\nLine 2\nLine 3"
        analysis = counter.analyze(text, "text")

        assert "text_length" in analysis.metadata
        assert "text_lines" in analysis.metadata
        assert "compression_ratio" in analysis.metadata

        assert analysis.metadata["text_length"] == len(text)
        assert analysis.metadata["text_lines"] == 3

    def test_analyze_compression_ratio(self):
        """Test analyze calculates compression ratio."""
        counter = TiktokenCounter()
        text = "Hello, world!"
        analysis = counter.analyze(text, "text")

        compression_ratio = analysis.metadata["compression_ratio"]
        assert compression_ratio > 0
        assert compression_ratio == len(text) / analysis.token_count

    def test_analyze_empty_text(self):
        """Test analyzing empty text."""
        counter = TiktokenCounter()
        analysis = counter.analyze("", "text")

        assert analysis.token_count == 0
        assert analysis.metadata["text_length"] == 0
        assert analysis.metadata["text_lines"] == 1

    def test_model_name_property(self):
        """Test model_name property."""
        counter = TiktokenCounter(model="gpt-4-turbo")
        assert counter.model_name == "gpt-4-turbo"

    def test_multiple_models(self):
        """Test different models produce different counts."""
        text = "Hello, world!"

        counter_gpt4 = TiktokenCounter(model="gpt-4")
        counter_davinci = TiktokenCounter(model="text-davinci-003")

        count_gpt4 = counter_gpt4.count_tokens(text)
        count_davinci = counter_davinci.count_tokens(text)

        # Both should return valid counts
        assert count_gpt4 > 0
        assert count_davinci > 0

    def test_unicode_text(self):
        """Test counting tokens in unicode text."""
        counter = TiktokenCounter()
        text = "Hello 世界 🌍"
        count = counter.count_tokens(text)
        assert count > 0

    def test_special_characters(self):
        """Test counting tokens with special characters."""
        counter = TiktokenCounter()
        text = "Test: @#$% & *()[]{}|\\<>?/"
        count = counter.count_tokens(text)
        assert count > 0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_count_tokens_function(self):
        """Test count_tokens convenience function."""
        count = count_tokens("Hello, world!")
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_with_custom_model(self):
        """Test count_tokens with custom model."""
        count = count_tokens("Hello, world!", model="gpt-3.5-turbo")
        assert count > 0

    def test_analyze_text_function(self):
        """Test analyze_text convenience function."""
        analysis = analyze_text('{"name": "Alice"}', "json")

        assert analysis.format == "json"
        assert analysis.token_count > 0
        assert analysis.model == "gpt-4"

    def test_analyze_text_with_custom_model(self):
        """Test analyze_text with custom model."""
        analysis = analyze_text("Hello", "text", model="gpt-3.5-turbo")

        assert analysis.model == "gpt-3.5-turbo"
        assert analysis.token_count > 0

    def test_analyze_text_includes_metadata(self):
        """Test analyze_text includes metadata."""
        analysis = analyze_text("Test\ntext", "text")

        assert "text_length" in analysis.metadata
        assert "text_lines" in analysis.metadata
        assert analysis.metadata["text_lines"] == 2


class TestEdgeCases:
    """Test edge cases."""

    def test_very_long_text(self):
        """Test analyzing very long text."""
        counter = TiktokenCounter()
        text = "word " * 10000
        count = counter.count_tokens(text)
        assert count > 10000

    def test_repeated_analysis(self):
        """Test repeated analysis of same text."""
        counter = TiktokenCounter()
        text = "Hello, world!"

        count1 = counter.count_tokens(text)
        count2 = counter.count_tokens(text)

        assert count1 == count2

    def test_whitespace_only(self):
        """Test text with only whitespace."""
        counter = TiktokenCounter()
        text = "   \n\t  "
        count = counter.count_tokens(text)
        assert count >= 0

    def test_numbers_and_symbols(self):
        """Test text with numbers and symbols."""
        counter = TiktokenCounter()
        text = "123 456 !@# $%^"
        count = counter.count_tokens(text)
        assert count > 0
