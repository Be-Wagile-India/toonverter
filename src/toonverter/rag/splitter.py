from typing import Any

from toonverter.analysis.analyzer import count_tokens
from toonverter.encoders import encode

from .models import Chunk


class ToonHybridSplitter:
    """
    Splits JSON/TOON-like data structures into semantically meaningful chunks
    that fit within a specified token limit.

    It uses a hybrid approach:
    1. Structural Traversal: Recursively walks the object tree.
    2. Buffer Accumulation: Groups small sibling nodes (e.g., dict keys or list items) together to maximize context preservation within a chunk.
    3. Semantic Text Splitting: For string values that exceed the chunk size, it splits them textually (e.g., by paragraphs) while attaching the structural path to every segment.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 0,
        min_chunk_size: int = 50,
        model_name: str = "gpt-4",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.model_name = model_name

    def split(self, data: Any, metadata: dict[str, Any] | None = None) -> list[Chunk]:
        """
        Main entry point to split data into chunks.
        """
        if metadata is None:
            metadata = {}

        chunks: list[Chunk] = []
        # Start the recursive traversal
        for chunk in self._visit(data, [], metadata):
            chunks.append(chunk)

        return chunks

    def _visit(
        self, node: Any, path: list[str], metadata: dict[str, Any]
    ) -> Any:  # Generator[Chunk, None, None] typed as Any to avoid import hassle
        """
        Recursive visitor that decides whether to emit a node as a chunk
        or recurse deeper.
        """
        # 1. Measure the node
        node_str = self._serialize(node)
        token_count = count_tokens(node_str, model=self.model_name)

        # 2. Base Case: If it fits, yield it (unless it's empty/trivial)
        if token_count <= self.chunk_size:
            if token_count >= self.min_chunk_size or not path:  # Always yield root if tiny
                # Construct the context-enriched content
                content_with_context = self._format_chunk(path, node)
                yield Chunk(
                    content=content_with_context,
                    path=path,
                    metadata=metadata,
                    token_count=token_count,
                )
            return

        # 3. Recursive Case: It's too big. Breakdown strategy depends on type.
        if isinstance(node, dict):
            yield from self._process_container(node.items(), path, metadata, is_dict=True)
        elif isinstance(node, list):
            yield from self._process_container(enumerate(node), path, metadata, is_dict=False)
        elif isinstance(node, str):
            yield from self._split_long_string(node, path, metadata)
        else:
            # Primitive that is somehow too huge (unlikely for int/float/bool)
            # Just yield it to avoid crash, even if oversized.
            content = self._format_chunk(path, node)
            yield Chunk(content=content, path=path, metadata=metadata, token_count=token_count)

    def _process_container(
        self, items: Any, path: list[str], metadata: dict[str, Any], is_dict: bool
    ) -> Any:
        """
        Handles Dicts and Lists using Buffer Accumulation.
        Groups small siblings together until chunk_size is reached.
        """
        buffer: Any = {} if is_dict else []
        buffer_size = 0

        for key, value in items:
            # Determine path segment for this item
            key_str = str(key)
            item_path = [*path, key_str]

            # Measure this specific item
            item_str = self._serialize(value)
            item_tokens = count_tokens(item_str, model=self.model_name)

            # If this single item is HUGE, we must flush buffer and recurse on the item
            if item_tokens > self.chunk_size:
                # Flush existing buffer if not empty
                if buffer_size > 0:
                    yield self._create_chunk_from_buffer(buffer, path, metadata, buffer_size)
                    buffer = {} if is_dict else []
                    buffer_size = 0

                # Recurse on the large item
                yield from self._visit(value, item_path, metadata)
                continue

            # If adding this item exceeds buffer, flush first
            # Heuristic: We estimate overhead of syntax (brackets, commas) as ~5 tokens
            if buffer_size + item_tokens + 5 > self.chunk_size:
                yield self._create_chunk_from_buffer(buffer, path, metadata, buffer_size)
                buffer = {} if is_dict else []
                buffer_size = 0

            # Add to buffer
            if is_dict:
                buffer[key] = value
            else:
                buffer.append(value)
            buffer_size += item_tokens

        # Final flush
        if buffer_size > 0:
            yield self._create_chunk_from_buffer(buffer, path, metadata, buffer_size)

    def _create_chunk_from_buffer(
        self, buffer: Any, path: list[str], metadata: dict[str, Any], _size: int
    ) -> Chunk:
        content = self._format_chunk(path, buffer)
        # Recalculate exact size including the context/formatting we just added
        final_size = count_tokens(content, model=self.model_name)
        return Chunk(content=content, path=path, metadata=metadata, token_count=final_size)

    def _split_long_string(self, text: str, path: list[str], metadata: dict[str, Any]) -> Any:
        """
        Splits a long string into overlapping segments, preserving context.
        """
        # Simple text splitting by separators (Double Newline -> Newline -> Space)
        # In a full prod system, we might use a dedicated NLP library here.
        # For now, we use a robust recursive logic similar to LangChain's default.

        separators = ["\n\n", "\n", ". ", " ", ""]
        final_chunks: list[str] = []
        self._recursive_text_split(text, separators, final_chunks)

        for segment in final_chunks:
            # Re-wrap in context: key: "segment..."
            content = self._format_chunk(path, segment)
            size = count_tokens(content, model=self.model_name)
            yield Chunk(content=content, path=path, metadata=metadata, token_count=size)

    def _recursive_text_split(self, text: str, separators: list[str], result: list[str]) -> None:
        """
        Helper to recursively split text by separators.
        """
        final_sep = separators[-1]

        # Find the best separator to use
        separator = final_sep
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break

        # Split
        splits = text.split(separator) if separator else list(text)

        # Merge back into chunks
        current_chunk: list[str] = []
        current_len = 0

        for s in splits:
            s_len = count_tokens(s, model=self.model_name)
            if current_len + s_len > self.chunk_size:
                if current_chunk:
                    joined = (separator if separator else "").join(current_chunk)
                    result.append(joined)
                    current_chunk = []
                    current_len = 0

                # If single split is still too big, recurse with next separator
                if s_len > self.chunk_size and separators.index(separator) + 1 < len(separators):
                    self._recursive_text_split(
                        s, separators[separators.index(separator) + 1 :], result
                    )
                else:
                    current_chunk.append(s)
                    current_len += s_len
            else:
                current_chunk.append(s)
                current_len += s_len

        if current_chunk:
            joined = (separator if separator else "").join(current_chunk)
            result.append(joined)

    def _serialize(self, data: Any) -> str:
        """Fast serialization for size estimation."""
        # Use toonverter.encoders.encode for TOON-aware sizing estimation
        return encode(data)

    def _format_chunk(self, path: list[str], data: Any) -> str:
        """
        Formats the chunk with its structural context.
        Example: path=['users', '0'], data={'name': 'Bob'}
        -> {"users": [{"name": "Bob"}]} (conceptual)

        For readibility/RAG, we prefer a flattened path notation:
        "users.0: {'name': 'Bob'}"
        """
        path_str = ".".join(path)
        data_str = self._serialize(data)
        if path_str:
            return f"# Path: {path_str}\n{data_str}"
        return data_str
