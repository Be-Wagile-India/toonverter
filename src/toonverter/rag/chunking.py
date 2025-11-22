import math
from collections.abc import Generator, Iterable
from typing import TYPE_CHECKING, Any, TypeVar

from toonverter.analysis.token_counter import TiktokenCounter
from toonverter.core.registry import registry


if TYPE_CHECKING:
    from toonverter.core.interfaces import FormatAdapter, TokenCounter

# Type alias for a RAG chunk
TOONChunk = str
T = TypeVar("T")


class ToonChunker:
    """
    Intelligently chunks Python data into token-optimized, semantically coherent
    TOON strings for RAG.

    It uses a token counter (Tiktoken) and your TOON adapter to break down
    complex structures (dictionaries and lists) into contextually enriched chunks,
    ensuring each output chunk remains below the specified token limit.
    """

    def __init__(
        self,
        max_tokens: int = 500,
        model: str = "gpt-4o",
        context_tokens: int = 50,
    ) -> None:
        """
        Initializes the chunker with token limits and context settings.

        Args:
            max_tokens: The maximum desired token length for any single chunk.
            model: The LLM model name for token counting.
            context_tokens: Tokens reserved for metadata or surrounding context
                            (subtracted from the total max_tokens).
        """
        self.max_tokens = max_tokens
        self.model = model
        # The true max payload size available for the *content*
        self.effective_max_tokens = max_tokens - context_tokens

        self.counter: TokenCounter = TiktokenCounter(model_name=self.model)

        self.toon_adapter: FormatAdapter = registry.get("toon")

        # Pre-calculate token cost for the minimal header template
        header_template = "Context_Path: path"
        self._min_header_cost = self.counter.count_tokens(header_template)

    def _count_tokens(self, text: str) -> int:
        """Internal wrapper to count tokens using the configured model."""
        return self.counter.count_tokens(text)

    def _create_contextual_chunk(self, content: Any, path: str) -> TOONChunk:
        """
        Encodes content and prepends a contextual TOON header.

        Args:
            content: The Python data object to be encoded (dict or list).
            path: The hierarchical path string (e.g., 'root.section[2-5]').

        Returns:
            The complete TOON chunk string with header.
        """

        # 1. Create the content TOON string using the actual encoder
        content_str = self.toon_adapter.encode(content)

        # 2. Create the header (using TOON's structure for metadata)
        header = f"Context_Path: {path}"

        # 3. Combine header and content
        return f"{header}\n\n{content_str}"

    def chunk(self, data: Any) -> Generator[TOONChunk, None, None]:
        """
        Entry point for the chunking process.

        Args:
            data: The Python object (dict, list, etc.) to be chunked.

        Yields:
            TOONChunk: A valid, token-constrained, contextual TOON string.
        """
        yield from self._chunk_recursive(data)

    def _chunk_recursive(
        self, data: Any, current_path: str = "root"
    ) -> Generator[TOONChunk, None, None]:
        """
        The core recursive function that walks the data structure.
        Determines if an object fits, or if it needs to be split further.
        """
        # Max tokens available for the content payload itself
        max_payload_tokens = self.effective_max_tokens - self._min_header_cost

        # 1. Base Case: Try to encode the whole object with its contextual header
        try:
            full_chunk = self._create_contextual_chunk(data, current_path)
            full_tokens = self._count_tokens(full_chunk)
        except Exception:
            # If encoding fails (e.g., unsupported type), treat it as too large to force recursion/fallback
            full_tokens = math.inf
            full_chunk = ""

        # If it fits (checking against the absolute max_tokens), yield the whole thing
        if full_tokens <= self.max_tokens:
            if full_chunk:
                yield full_chunk
            return

        # 2. Recursive Case: Split complex structures
        if isinstance(data, dict):
            yield from self._chunk_dict(data, max_payload_tokens, current_path)

        elif isinstance(data, (list, tuple)) and isinstance(data, Iterable):
            yield from self._chunk_list(list(data), max_payload_tokens, current_path)

        # 3. Fallback: Yield the oversized chunk if it couldn't be split (e.g., a giant string)
        elif full_chunk:
            yield full_chunk

    def _chunk_dict(
        self, data: dict[Any, Any], max_payload_tokens: int, path: str
    ) -> Generator[TOONChunk, None, None]:
        """
        Intelligent dictionary chunking: batches key-value pairs into semantically
        grouped chunks that fit the token limit.
        """
        current_batch: dict[Any, Any] = {}
        current_batch_tokens = 0

        for key, value in data.items():
            item_data = {key: value}

            try:
                # Token cost of the single key-value pair
                item_str = self.toon_adapter.encode(item_data)
                item_tokens = self._count_tokens(item_str)
            except Exception:
                # If the item itself is too complex to encode in isolation, recurse on the value
                yield from self._chunk_recursive(value, f"{path}.{key}")
                continue

            if (current_batch_tokens + item_tokens) <= max_payload_tokens:
                # Add to the current batch
                current_batch[key] = value
                current_batch_tokens += item_tokens
            else:
                # Current item doesn't fit the current batch.
                if current_batch:
                    # 1. Yield the full, token-optimized current batch
                    yield self._create_contextual_chunk(current_batch, path)

                # 2. Start a new batch
                if item_tokens > max_payload_tokens:
                    # Single item is too large (value must be split), recurse on the value
                    yield from self._chunk_recursive(value, f"{path}.{key}")
                    current_batch = {}
                    current_batch_tokens = 0
                else:
                    # Start the new batch with this item
                    current_batch = item_data
                    current_batch_tokens = item_tokens

        # Yield any remaining batch
        if current_batch:
            yield self._create_contextual_chunk(current_batch, path)

    def _chunk_list(
        self, items: list[Any], max_payload_tokens: int, path: str
    ) -> Generator[TOONChunk, None, None]:
        """
        Intelligent list/tabular chunking: groups list items into token-optimized batches,
        ensuring the output path includes the index range for context.
        """
        current_batch: list[Any] = []
        current_batch_tokens = 0

        for i, item in enumerate(items):
            try:
                # Encode as a list of one item to accurately capture the structural cost of a table row
                item_str = self.toon_adapter.encode([item])
                item_tokens = self._count_tokens(item_str)
            except Exception:
                continue

            if (current_batch_tokens + item_tokens) <= max_payload_tokens:
                current_batch.append(item)
                current_batch_tokens += item_tokens
            else:
                # Current item doesn't fit the current batch.
                if current_batch:
                    # 1. Yield the full, semantically safe current batch
                    start_index = i - len(current_batch)
                    end_index = i - 1
                    yield self._create_contextual_chunk(
                        current_batch, f"{path}[{start_index}-{end_index}]"
                    )

                # 2. Start a new batch
                if item_tokens > max_payload_tokens:
                    # Single item is oversized. Recurse on the item itself (e.g., a giant object in the list).
                    yield from self._chunk_recursive(item, f"{path}[{i}]")
                    current_batch = []
                    current_batch_tokens = 0
                else:
                    # Start the new batch with this item
                    current_batch = [item]
                    current_batch_tokens = item_tokens

        # Yield any remaining batch
        if current_batch:
            start_index = len(items) - len(current_batch)
            end_index = len(items) - 1
            yield self._create_contextual_chunk(current_batch, f"{path}[{start_index}-{end_index}]")
