"""
Advanced Hybrid Serializer for optimizing mixed text and image data for Vision LLMs.
Features path tracking, image deduplication, and robust marker injection.
"""

import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from toonverter.core.registry import registry
from toonverter.core.types import ImageOptimizeOptions, MultimodalPayload, ToonImage

from .image_tool import ImageOptimizer


logger = logging.getLogger(__name__)


@dataclass
class SerializationContext:
    """Internal state for a single serialization operation."""

    options: ImageOptimizeOptions
    image_keys: set[str]
    # Maps marker ID -> ToonImage
    marker_map: dict[str, ToonImage] = field(default_factory=dict)
    # Maps source (path/bytes hash) -> marker ID (for deduplication)
    source_cache: dict[Any, str] = field(default_factory=dict)
    # Tracks errors: path -> error message
    errors: dict[str, str] = field(default_factory=dict)


class HybridSerializer:
    """
    Production-grade serializer for splitting nested data into text and image components.

    Capabilities:
    - Recursive traversal with path tracking (e.g., 'root.users[0].avatar').
    - In-memory caching to prevent re-processing identical image sources.
    - Structural splitting using unique, non-colliding UUID markers.
    - Fallback strategies for failed image processing.
    """

    def __init__(self) -> None:
        self.image_optimizer = ImageOptimizer()
        self.text_encoder = registry.get("toon")
        # Regex to find markers. Matches specific UUIDv4 format used in generation.
        self._marker_pattern = re.compile(r"(__IMG_CTX_[a-f0-9]{32}__)")

    def serialize(
        self,
        data: dict[str, Any],
        image_keys: list[str],
        optimize_options: ImageOptimizeOptions | None = None,
    ) -> MultimodalPayload:
        """
        Orchestrates the serialization of mixed content.

        Args:
            data: The root data dictionary.
            image_keys: Keys identifying image values.
            optimize_options: Configuration for image processing.

        Returns:
            List of text strings and ToonImage objects.
        """
        ctx = SerializationContext(
            options=optimize_options or ImageOptimizeOptions(), image_keys=set(image_keys)
        )

        # 1. Transform Data (Inject Markers)
        processed_data = self._walk_and_replace(data, "root", ctx)

        # 2. Encode Text Structure
        try:
            full_text = self.text_encoder.encode(processed_data)
        except Exception as e:
            logger.exception("Hybrid serialization text encoding failed")
            return [f"Error encoding text structure: {e}"]

        # 3. Split and Reassemble
        payload: MultimodalPayload = []
        parts = self._marker_pattern.split(full_text)

        for part in parts:
            if not part:
                continue

            if part in ctx.marker_map:
                # Inject the processed image object
                image_obj = ctx.marker_map[part]
                payload.append(image_obj)
            else:
                # Append text chunk
                payload.append(part)

        # Log any non-fatal errors encountered during image processing
        if ctx.errors:
            logger.warning("Hybrid serialization completed with %d image errors.", len(ctx.errors))

        return payload

    def _walk_and_replace(self, data: Any, path: str, ctx: SerializationContext) -> Any:
        """Recursively traverses data, replacing images with unique markers."""

        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                current_path = f"{path}.{key}"

                if key in ctx.image_keys:
                    new_dict[key] = self._process_image_node(value, current_path, ctx)
                else:
                    new_dict[key] = self._walk_and_replace(value, current_path, ctx)
            return new_dict

        if isinstance(data, list):
            return [
                self._walk_and_replace(item, f"{path}[{i}]", ctx) for i, item in enumerate(data)
            ]

        return data

    def _process_image_node(self, source: Any, path: str, ctx: SerializationContext) -> str:
        """Processes a single image value, handling caching and errors."""

        # 1. Check Cache (Deduplication)
        # Use source string/path as cache key if hashable, otherwise skip cache
        cache_key = source if isinstance(source, (str, bytes)) else None

        if cache_key and cache_key in ctx.source_cache:
            return ctx.source_cache[cache_key]

        # 2. Generate Marker
        # Using hex UUID ensures it's safe for most text encoders (no special chars)
        marker = f"__IMG_CTX_{uuid.uuid4().hex}__"

        # 3. Optimize Image
        try:
            optimized_image = self.image_optimizer.process_image(source, ctx.options)

            ctx.marker_map[marker] = optimized_image

            if cache_key:
                ctx.source_cache[cache_key] = marker

            return marker

        except Exception as e:
            logger.exception("Image processing failed at %s", path)
            ctx.errors[path] = str(e)
            return f"<Image Error at {path}: {e}>"
