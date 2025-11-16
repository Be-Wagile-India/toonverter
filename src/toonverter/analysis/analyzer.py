"""Token analysis module using tiktoken."""

from typing import ClassVar

import tiktoken

from toonverter.core.exceptions import TokenCountError
from toonverter.core.interfaces import TokenCounter
from toonverter.core.types import TokenAnalysis


class TiktokenCounter(TokenCounter):
    """Token counter implementation using tiktoken library.

    Supports various OpenAI models and provides accurate token counts.
    """

    # Model to encoding mapping
    MODEL_ENCODINGS: ClassVar[dict[str, str]] = {
        "gpt-4": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "text-davinci-003": "p50k_base",
        "text-davinci-002": "p50k_base",
        "claude-3": "cl100k_base",  # Approximation
        "claude-2": "cl100k_base",  # Approximation
    }

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize token counter.

        Args:
            model: Model name or encoding name
        """
        self._model = model
        self._encoding_name = self._get_encoding_name(model)

        try:
            self._encoding = tiktoken.get_encoding(self._encoding_name)
        except Exception as e:
            msg = f"Failed to load encoding '{self._encoding_name}': {e}"
            raise TokenCountError(msg) from e

    def _get_encoding_name(self, model: str) -> str:
        """Get encoding name for model.

        Args:
            model: Model name

        Returns:
            Encoding name
        """
        # Check if it's a known model
        if model in self.MODEL_ENCODINGS:
            return self.MODEL_ENCODINGS[model]

        # Check if it's already an encoding name
        try:
            tiktoken.get_encoding(model)
            return model
        except Exception:
            pass

        # Default to cl100k_base (most common for modern models)
        return "cl100k_base"

    @property
    def model_name(self) -> str:
        """Return the model name.

        Returns:
            Model identifier
        """
        return self._model

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to analyze

        Returns:
            Number of tokens

        Raises:
            TokenCountError: If counting fails
        """
        if not text:
            return 0

        try:
            tokens = self._encoding.encode(text)
            return len(tokens)
        except Exception as e:
            msg = f"Failed to count tokens: {e}"
            raise TokenCountError(msg) from e

    def analyze(self, text: str, format_name: str) -> TokenAnalysis:
        """Analyze token usage for text.

        Args:
            text: Text to analyze
            format_name: Format of the text

        Returns:
            TokenAnalysis with statistics

        Raises:
            TokenCountError: If analysis fails
        """
        token_count = self.count_tokens(text)

        return TokenAnalysis(
            format=format_name,
            token_count=token_count,
            model=self._model,
            encoding=self._encoding_name,
            metadata={
                "text_length": len(text),
                "text_lines": text.count("\n") + 1,
                "compression_ratio": len(text) / max(token_count, 1),
            },
        )


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Convenience function to count tokens.

    Args:
        text: Text to analyze
        model: Model name or encoding

    Returns:
        Number of tokens

    Examples:
        >>> count_tokens("Hello, world!")
        4
    """
    counter = TiktokenCounter(model)
    return counter.count_tokens(text)


def analyze_text(text: str, format_name: str, model: str = "gpt-4") -> TokenAnalysis:
    """Convenience function to analyze text.

    Args:
        text: Text to analyze
        format_name: Format of the text
        model: Model name or encoding

    Returns:
        TokenAnalysis with statistics

    Examples:
        >>> analysis = analyze_text('{"name": "Alice"}', "json")
        >>> print(analysis.token_count)
        7
    """
    counter = TiktokenCounter(model)
    return counter.analyze(text, format_name)
