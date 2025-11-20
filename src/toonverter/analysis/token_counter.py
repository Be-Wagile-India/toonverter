from typing import Any

import tiktoken

from toonverter.core.interfaces import TokenCounter


class TiktokenCounter(TokenCounter):
    """
    Implements the TokenCounter interface using the `tiktoken` library,
    the standard tokenization method used by OpenAI models.
    """

    def __init__(self, model_name: str = "gpt-4o") -> None:
        """
        Initializes the counter by loading the appropriate encoding for the model.

        Args:
            model_name: The name of the model to use for tokenization
                        (e.g., "gpt-4", "gpt-3.5-turbo").
        """
        self._model_name = model_name

        try:
            # Use encoding_for_model for robustness against model name changes
            self._encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to a common encoder if the model name is unknown
            self._encoding = tiktoken.get_encoding("cl100k_base")

    @property
    def model_name(self) -> str:
        """Returns the name of the model associated with this counter."""
        return self._model_name

    def count_tokens(self, text: str) -> int:
        """
        Calculates the number of tokens in the given text.

        Args:
            text: The string to tokenize.

        Returns:
            The token count as an integer.
        """
        if not text:
            return 0
        return len(self._encoding.encode(text))

    def analyze(self, text: str, _format_name: str) -> dict[str, Any]:
        """
        Analyzes the text and returns detailed tokenization data.

        Args:
            text: The string to analyze.
            _format_name: The format of the data (e.g., "json", "toon").
                          (Marked as unused as this implementation doesn't need it).

        Returns:
            A dictionary containing analysis details, including the token list.
        """
        tokens = self._encoding.encode(text)
        return {
            "token_count": len(tokens),
            "tokens": tokens,
            "encoding": self._encoding.name,
            "model_name": self.model_name,
        }
