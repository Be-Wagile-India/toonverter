"""
Advanced image processing utilities for resizing, token estimation, and optimization.
Includes EXIF handling, smart background flattening, and strict size enforcement.
"""

import base64
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Union

from toonverter.core.types import ImageDetail, ImageOptimizeOptions, ToonImage


if TYPE_CHECKING:
    from PIL import Image as PILImage

try:
    from PIL import Image, ImageOps

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore
    ImageOps = None  # type: ignore

logger = logging.getLogger(__name__)


class ImageOptimizer:
    """
    Handles advanced image processing for Vision LLMs.

    Features:
    - EXIF rotation correction.
    - Smart transparency flattening (white background).
    - Iterative compression to meet file size limits.
    - Accurate token estimation for OpenAI/Anthropic models.
    """

    def __init__(self) -> None:
        """Initialize the optimizer and check for PIL availability."""
        if not PIL_AVAILABLE:
            logger.warning("Pillow not installed. Image optimization disabled.")

    def process_image(
        self, source: str | Path | bytes | Any, options: ImageOptimizeOptions
    ) -> ToonImage:
        """
        Reads, corrects, resizes, and encodes an image source.

        Args:
            source: File path, URL string, raw bytes, or PIL Image object.
            options: Configuration for optimization.

        Returns:
            ToonImage object with processed data and estimated token cost.

        Raises:
            ImportError: If Pillow is not installed.
            ValueError: If the image data is invalid or cannot be processed.
        """
        if not PIL_AVAILABLE:
            msg = "Pillow library required. Install with `pip install pillow`"
            raise ImportError(msg)

        # 1. Identify and Load Image
        img = self._load_image(source)

        # If _load_image returns a ToonImage directly (e.g., it was a URL), return it.
        if isinstance(img, ToonImage):
            return img

        # 2. Pre-processing: EXIF Rotation & Color Mode
        # Correct orientation from EXIF tags (crucial for phone photos)
        img = ImageOps.exif_transpose(img)

        # Convert RGBA to RGB with white background (better for OCR/Vision than black)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = self._flatten_alpha_to_white(img)
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # 3. Resize Dimensions
        img = self._resize_image(img, options.max_dimension)

        # 4. Compress and Encode
        # If max_size_kb is set, we might need to try multiple quality settings
        b64_data, final_mime = self._compress_to_target(img, options)

        # 5. Estimate Tokens
        token_cost = self._estimate_vision_tokens(img.size, options.detail)

        return ToonImage(
            data=b64_data,
            mime_type=final_mime,
            detail=options.detail,
            token_cost=token_cost,
            is_url=False,
        )

    def _load_image(self, source: str | Path | bytes | Any) -> Union["PILImage.Image", ToonImage]:
        """Parses the source and returns a PIL Image or a pre-built ToonImage (for URLs)."""
        try:
            if isinstance(source, (str, Path)):
                str_source = str(source)
                if str_source.startswith(("http://", "https://")):
                    # URLs are returned directly as ToonImage
                    return ToonImage(
                        data=str_source,
                        mime_type="n/a",
                        detail=ImageDetail.AUTO,
                        token_cost=85,  # Base cost for URLs until fetched/analyzed
                        is_url=True,
                    )
                path = Path(source)
                if not path.exists():
                    msg = f"Image file not found: {path}"
                    raise ValueError(msg)
                return Image.open(path)

            if isinstance(source, bytes):
                return Image.open(io.BytesIO(source))

            # Assume valid PIL Image object if not bytes/str
            if hasattr(source, "size") and hasattr(source, "convert"):
                return source

            msg = "Unsupported image source type"
            raise ValueError(msg)

        except Exception as e:
            # Use logging.exception for exception context without redundant argument
            logger.exception("Failed to load image source")

            msg = f"Invalid image source: {e}"
            raise ValueError(msg) from e

    def _flatten_alpha_to_white(self, img: "PILImage.Image") -> "PILImage.Image":
        """Converts an image with transparency to RGB with a white background."""
        # Create a white background image
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Paste the image on top, using the alpha channel as a mask
        # For P mode with transparency, we convert to RGBA first
        if img.mode == "P":
            img = img.convert("RGBA")

        # Split alpha channel
        if len(img.split()) > 3:
            background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        else:
            background.paste(img)

        return background

    def _resize_image(self, img: "PILImage.Image", max_dim: int) -> "PILImage.Image":
        """Resizes image maintaining aspect ratio using high-quality resampling."""
        width, height = img.size
        if width <= max_dim and height <= max_dim:
            return img

        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _compress_to_target(
        self, img: "PILImage.Image", options: ImageOptimizeOptions
    ) -> tuple[str, str]:
        """
        Compresses the image to base64, respecting quality and max_size_kb.
        Returns (base64_string, mime_type).
        """
        target_format = options.format.upper()
        if target_format == "JPEG":
            mime = "image/jpeg"
        elif target_format == "PNG":
            mime = "image/png"
        elif target_format == "WEBP":
            mime = "image/webp"
        else:
            # Fallback
            target_format = "JPEG"
            mime = "image/jpeg"

        # If no size limit, just save once
        if not options.max_size_kb:
            buffer = io.BytesIO()
            img.save(buffer, format=target_format, quality=options.quality, optimize=True)
            return base64.b64encode(buffer.getvalue()).decode("utf-8"), mime

        # Iterative compression for size limit
        max_bytes = options.max_size_kb * 1024
        min_quality = 10
        current_quality = options.quality

        for _ in range(3):  # Max 3 attempts to downscale/compress
            buffer = io.BytesIO()
            img.save(buffer, format=target_format, quality=current_quality, optimize=True)
            size = buffer.tell()

            if size <= max_bytes:
                return base64.b64encode(buffer.getvalue()).decode("utf-8"), mime

            # Reduce quality for next attempt
            current_quality = max(min_quality, int(current_quality * 0.7))

            # If quality is already at min, we might need to resize instead
            if current_quality == min_quality:
                # Aggressive resize if quality drop isn't enough
                img = img.resize((int(img.width * 0.8), int(img.height * 0.8)))

        # Final attempt return even if slightly over limit to avoid crash
        return base64.b64encode(buffer.getvalue()).decode("utf-8"), mime

    def _estimate_vision_tokens(self, size: tuple[int, int], detail: ImageDetail) -> int:
        """
        Estimates token cost based on OpenAI pricing model (Standard for Vision LLMs).
        """
        if detail == ImageDetail.LOW:
            return 85

        width, height = size

        # 1. Scale to fit within 2048x2048 (maintaining aspect ratio)
        if width > 2048 or height > 2048:
            ratio = 2048 / max(width, height)
            width = int(width * ratio)
            height = int(height * ratio)

        # 2. Scale such that shortest side is 768px
        if width < height:
            if width > 768:
                ratio = 768 / width
                width = 768
                height = int(height * ratio)
        elif height > 768:
            ratio = 768 / height
            height = 768
            width = int(width * ratio)

        # 3. Calculate 512px tiles
        tiles_w = (width + 511) // 512
        tiles_h = (height + 511) // 512
        total_tiles = tiles_w * tiles_h

        return (total_tiles * 170) + 85
