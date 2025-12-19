"""Semantic deduplication of data structures."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from collections.abc import Callable, Generator, Iterable  # noqa: TC003
from typing import Any, Literal, TypeVar

from toonverter.core.registry import get_registry
from toonverter.core.spec import ToonEncodeOptions
from toonverter.core.types import DeduplicationResult, DuplicateItem


logger = logging.getLogger(__name__)


class ExactDeduplicator:
    """Detects and eliminates semantic duplicates in data.

    Supports two modes:
    1. 'exact': Deterministic structural hashing (fast, O(1)).
    2. 'semantic': Vector embedding similarity (slower, O(N^2), requires sentence-transformers).
    """

    def __init__(
        self,
        mode: Literal["exact", "semantic"] = "exact",
        threshold: float = 0.95,
        model_name: str = "all-MiniLM-L6-v2",
        key_selector: Callable[[Any], Any] | None = None,
    ) -> None:
        """Initialize deduplicator.

        Args:
            mode: Deduplication mode ('exact' or 'semantic').
            threshold: Similarity threshold for semantic mode (0.0 to 1.0).
            model_name: Model name for semantic embeddings.
            key_selector: Optional function to select specific parts of data for comparison.
        """
        self.mode = mode
        self.threshold = threshold
        self.model_name = model_name
        self.key_selector = key_selector
        self._seen_hashes: set[str] = set()
        self._hash_to_index: dict[str, int] = {}

        self._model: Any = None
        if self.mode == "semantic":
            self._init_model()

    def _init_model(self) -> None:
        """Lazy load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415

            self._model = SentenceTransformer(self.model_name)
        except ImportError:
            logger.warning("sentence-transformers not found. Falling back to 'exact' mode.")
            self.mode = "exact"

    def process(self, data: Iterable[Any]) -> DeduplicationResult:
        """Process an iterable and return unique items with a report.

        Args:
            data: Iterable of data items to check

        Returns:
            DeduplicationResult containing unique items and statistics
        """
        # Step 1: Exact Deduplication (Always run first as optimization)
        items = list(data)
        unique_candidates, exact_duplicates = self._process_exact(items)

        # Step 2: Semantic Deduplication (Optional)
        semantic_duplicates: list[DuplicateItem] = []
        final_unique: list[Any] = []

        if self.mode == "semantic" and self._model:
            final_unique, semantic_duplicates = self._process_semantic(unique_candidates)
        else:
            final_unique = unique_candidates

        # Merge results
        all_duplicates = exact_duplicates + semantic_duplicates

        # Recalculate reduction based on original count
        total_count = len(items)
        reduction = 0.0
        if total_count > 0:
            reduction = (len(all_duplicates) / total_count) * 100

        # Sort duplicates by original index for consistent reporting
        all_duplicates.sort(key=lambda x: x.duplicate_index)

        return DeduplicationResult(
            unique_items=final_unique,
            duplicate_count=len(all_duplicates),
            duplicates=all_duplicates,
            reduction_percentage=reduction,
        )

    def _process_exact(self, data: list[Any]) -> tuple[list[Any], list[DuplicateItem]]:
        """Run deterministic exact deduplication."""
        unique_items = []
        duplicates = []
        self._seen_hashes.clear()
        self._hash_to_index.clear()

        for index, item in enumerate(data):
            item_hash = self._compute_hash(item)

            if item_hash in self._seen_hashes:
                original_idx = self._hash_to_index[item_hash]
                duplicates.append(
                    DuplicateItem(original_index=original_idx, duplicate_index=index, item=item)
                )
            else:
                self._seen_hashes.add(item_hash)
                self._hash_to_index[item_hash] = index
                unique_items.append(item)

        return unique_items, duplicates

    def _process_semantic(self, candidates: list[Any]) -> tuple[list[Any], list[DuplicateItem]]:
        """Run embedding-based semantic deduplication on candidates."""
        if len(candidates) < 2:
            return candidates, []

        try:
            from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415
        except ImportError:
            logger.warning("scikit-learn not found. Skipping semantic analysis.")
            return candidates, []

        # Extract text representations
        texts = [self._extract_text(item) for item in candidates]

        # Filter valid texts
        valid_indices = [i for i, t in enumerate(texts) if t]
        valid_texts = [texts[i] for i in valid_indices]

        if len(valid_texts) < 2:
            return candidates, []

        # Compute Embeddings
        embeddings = self._model.encode(valid_texts, batch_size=32, show_progress_bar=False)

        to_remove_indices = set()
        duplicates = []

        # Use full matrix for small sets (maintains compatibility with existing tests/mocks)
        # and memory-efficient batched approach for large sets.
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415

        num_valid = len(valid_texts)

        if num_valid <= 1000:
            sim_matrix = cosine_similarity(embeddings)
            for i in range(num_valid):
                if valid_indices[i] in to_remove_indices:
                    continue
                for j in range(i + 1, num_valid):
                    if valid_indices[j] in to_remove_indices:
                        continue
                    if sim_matrix[i][j] >= self.threshold:
                        dup_real_idx = valid_indices[j]
                        orig_real_idx = valid_indices[i]
                        to_remove_indices.add(dup_real_idx)
                        duplicates.append(
                            DuplicateItem(
                                original_index=orig_real_idx,
                                duplicate_index=dup_real_idx,
                                item=candidates[dup_real_idx],
                            )
                        )
        else:
            # Memory-efficient batched iteration for large sets
            for i in range(num_valid):
                if valid_indices[i] in to_remove_indices:
                    continue

                if i + 1 < num_valid:
                    current_emb = embeddings[i : i + 1]
                    remaining_embs = embeddings[i + 1 :]
                    similarities = cosine_similarity(current_emb, remaining_embs)[0]

                    for offset, sim in enumerate(similarities):
                        j = i + 1 + offset
                        if sim >= self.threshold:
                            dup_real_idx = valid_indices[j]
                            orig_real_idx = valid_indices[i]

                            if dup_real_idx not in to_remove_indices:
                                to_remove_indices.add(dup_real_idx)
                                duplicates.append(
                                    DuplicateItem(
                                        original_index=orig_real_idx,
                                        duplicate_index=dup_real_idx,
                                        item=candidates[dup_real_idx],
                                    )
                                )

        # Reconstruct final list
        final_unique = []
        for i, item in enumerate(candidates):
            if i not in to_remove_indices:
                final_unique.append(item)

        return final_unique, duplicates

    def stream_unique(self, data: Iterable[Any]) -> Generator[Any, None, None]:
        """Yield unique items from a stream (Exact mode only).

        Args:
            data: Iterable of data items

        Yields:
            Unique items encountered so far
        """
        # Streaming implies we can't look ahead, so semantic (N^2) is hard/impossible without windows.
        # We fallback to exact hash deduplication for streams.
        self._seen_hashes.clear()

        for item in data:
            item_hash = self._compute_hash(item)
            if item_hash not in self._seen_hashes:
                self._seen_hashes.add(item_hash)
                yield item

    def _compute_hash(self, item: Any) -> str:
        """Compute a semantic hash for an item."""
        target = item
        if self.key_selector:
            target = self.key_selector(item)

        canonical = self._canonicalize(target)
        json_str = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    def _canonicalize(self, data: Any) -> Any:
        """Recursively canonicalize data structures."""
        if isinstance(data, dict):
            return {k: self._canonicalize(v) for k, v in sorted(data.items())}
        if isinstance(data, (list, tuple)):
            return [self._canonicalize(i) for i in data]
        if isinstance(data, set):
            return sorted([self._canonicalize(i) for i in data], key=str)
        return data

    def _extract_text(self, item: Any) -> str | None:
        """Extract text for embedding."""
        target = item
        if self.key_selector:
            target = self.key_selector(item)

        if isinstance(target, str):
            return target
        if isinstance(target, dict):
            # Heuristic: Join all string values
            parts = [str(v) for v in target.values() if isinstance(v, (str, int, float))]
            return " ".join(parts)
        return str(target)


_T = TypeVar("_T")


class SemanticDeduplicator:
    """
    A ContextOptimizer that detects and eliminates semantically duplicate items
    within lists in a data structure. It uses sentence embeddings to compare
    the semantic similarity of text content.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        threshold: float = 0.9,
        language_key: str = "language_code",  # Default to a literal string
        embedding_batch_size: int = 32,
        text_extraction_func: Callable[[Any], str | None] | None = None,
        spec: ToonEncodeOptions | None = None,
    ) -> None:
        """
        Initializes the SemanticDeduplicator.

        Args:
            model_name: The name of the sentence transformer model to use for embeddings.
            threshold: The cosine similarity threshold above which items are considered duplicates.
            language_key: The key used to identify language-specific content, if applicable.
            embedding_batch_size: Batch size for sentence embedding generation.
            text_extraction_func: A callable that extracts a string for embedding from an item.
                                  If None, a default extraction logic is used.
            spec: The TOON specification to use.
        """
        self.model_name = model_name
        self.threshold = threshold
        self.language_key = language_key
        self.embedding_batch_size = embedding_batch_size
        self.text_extraction_func = text_extraction_func
        self.spec = spec if spec is not None else ToonEncodeOptions()  # Default to an instance
        self.registry = get_registry()  # To get access to format adapters if needed
        self._embedding_cache: dict[str, Any] = {}  # Cache for embeddings
        self._model: Any = None

    @property
    def model(self) -> Any:
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # noqa: PLC0415

                self._model = SentenceTransformer(self.model_name)
            except ImportError as e:
                msg = "sentence-transformers is required for SemanticDeduplicator"
                raise ImportError(msg) from e
        return self._model

    def optimize(self, data: _T) -> _T:
        """
        Optimizes the given data structure by removing semantic duplicates from lists.

        Args:
            data: The input data structure.

        Returns:
            The optimized data structure with duplicates removed.
        """
        # Deep copy to avoid modifying the original data in place
        optimized_data = copy.deepcopy(data)
        self._visit(optimized_data, self._deduplicate_list)
        return optimized_data

    def _visit(self, node: Any, visitor_func: Callable[[list[Any]], None]) -> None:
        """
        Recursively visits nodes in the data structure.

        Args:
            node: The current node in the data structure.
            visitor_func: The function to apply to lists of items.
        """
        if isinstance(node, dict):
            for _key, value in node.items():
                if isinstance(value, (dict, list)):
                    self._visit(value, visitor_func)
        elif isinstance(node, list):
            # Apply the visitor function to the list itself
            visitor_func(node)
            for item in node:
                if isinstance(item, (dict, list)):
                    self._visit(item, visitor_func)

    def _deduplicate_list(self, items: list[Any]) -> None:
        """
        Deduplicates a list of items in place based on semantic similarity.
        """
        if not items or len(items) < 2:
            return

        # Ensure dependencies are available before proceeding
        try:
            from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415
        except ImportError:
            logger.warning("scikit-learn is required for SemanticDeduplicator. Skipping.")
            return

        texts = []
        for item in items:
            text = self._extract_text_for_embedding(item)
            texts.append(text)

        # Filter out items that couldn't provide text for embedding
        valid_items_indices: list[int] = []
        valid_texts: list[str] = []
        for i, text in enumerate(texts):
            if text is not None:
                valid_items_indices.append(i)
                valid_texts.append(text)

        if not valid_texts or len(valid_texts) < 2:
            return  # Not enough valid texts to deduplicate

        # Check cache for existing embeddings
        # Get unique uncached texts while preserving order
        unique_valid_texts = list(dict.fromkeys(valid_texts))
        uncached_texts: list[str] = [
            t for t in unique_valid_texts if t not in self._embedding_cache
        ]

        # Encode new texts in batches if needed
        if uncached_texts:
            new_embeddings = self.model.encode(
                uncached_texts,
                batch_size=self.embedding_batch_size,
                show_progress_bar=False,
            )
            for text, emb in zip(uncached_texts, new_embeddings, strict=True):
                self._embedding_cache[text] = emb

        # Retrieve all embeddings from cache (now guaranteed to exist)
        import numpy as np  # noqa: PLC0415

        embeddings = np.array([self._embedding_cache[t] for t in valid_texts])

        # Identify duplicates
        from sklearn.metrics.pairwise import cosine_similarity  # noqa: PLC0415

        to_remove_indices_in_valid_items = set()

        if len(valid_texts) <= 1000:
            similarity_matrix = cosine_similarity(embeddings)
            for i in range(len(valid_texts)):
                if i in to_remove_indices_in_valid_items:
                    continue
                for j in range(i + 1, len(valid_texts)):
                    if j in to_remove_indices_in_valid_items:
                        continue
                    if similarity_matrix[i][j] >= self.threshold:
                        to_remove_indices_in_valid_items.add(j)
        else:
            # Memory-efficient approach for large lists
            for i in range(len(valid_texts)):
                if i in to_remove_indices_in_valid_items:
                    continue

                if i + 1 < len(valid_texts):
                    current_emb = embeddings[i : i + 1]
                    remaining_embs = embeddings[i + 1 :]
                    similarities = cosine_similarity(current_emb, remaining_embs)[0]

                    for offset, sim in enumerate(similarities):
                        if sim >= self.threshold:
                            to_remove_indices_in_valid_items.add(i + 1 + offset)

        # Reconstruct the list, keeping only unique items
        new_items = []
        original_indices_to_keep = sorted(
            [
                valid_items_indices[i]
                for i in range(len(valid_texts))
                if i not in to_remove_indices_in_valid_items
            ]
        )

        # Add items that were not considered for embedding (e.g., non-textual data)
        # and the unique semantic items.
        kept_indices_set = set(original_indices_to_keep)
        for i, item in enumerate(items):
            if i in kept_indices_set or texts[i] is None:
                new_items.append(item)

        items[:] = new_items  # Modify the list in place

    def _extract_text_for_embedding(self, item: Any) -> str | None:
        """
        Extracts a string representation from an item suitable for embedding.
        Uses the provided text_extraction_func if available, otherwise a default logic.
        """
        if self.text_extraction_func:
            return self.text_extraction_func(item)

        # Default extraction logic
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            # Prioritize a 'description' key, otherwise concatenate values
            if "description" in item and isinstance(item["description"], str):
                return item["description"]

            # Concatenate string values from the dictionary
            return " ".join([str(v) for v in item.values() if isinstance(v, str)])
        return None
