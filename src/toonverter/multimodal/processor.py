"""Smart Image Processor for Vision Optimization."""

import io
from typing import Literal


try:
    import numpy as np
    from PIL import Image

    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False


class SmartImageProcessor:
    """Content-aware image optimizer for Vision LLMs."""

    def __init__(self) -> None:
        if not VISION_AVAILABLE:
            msg = "Pillow and numpy are required for SmartImageProcessor. Install 'toonverter[vision]'"
            raise ImportError(msg)

    def process(
        self, image_data: bytes, _max_tokens: int | None = None, target_provider: str = "openai"
    ) -> tuple[bytes, str]:
        """Optimize image for vision model consumption.

        Args:
            image_data: Raw image bytes
            max_tokens: Token budget (not implemented yet)
            target_provider: Target LLM provider

        Returns:
            Tuple of (optimized_bytes, mime_type)
        """
        img: Image.Image = Image.open(io.BytesIO(image_data))

        # 1. Format Standardization
        # Convert RGBA to RGB if we are going to use JPEG (except for diagrams where we want PNG)
        if img.mode == "RGBA" and self._detect_content_type(img) == "photo":
            img = img.convert("RGB")  # type: ignore[assignment]

        # 2. Smart Resizing (Tile Optimization for OpenAI)
        if target_provider == "openai":
            img = self._optimize_for_tiles(img)  # type: ignore[arg-type]

        # 3. Compression
        output = io.BytesIO()
        content_type = self._detect_content_type(img)

        if content_type == "chart":
            # Lossless for charts/text
            img.save(output, format="PNG", optimize=True)
            mime = "image/png"
        else:
            # Lossy for photos
            img.save(output, format="JPEG", quality=85, optimize=True)
            mime = "image/jpeg"

        return output.getvalue(), mime

    def _detect_content_type(self, img: "Image.Image") -> Literal["photo", "chart"]:
        """Analyze image content to determine best compression strategy.

        Uses histogram analysis to check for limited color palettes (charts/ui)
        vs continuous tone (photos).
        """
        # Resize small for analysis speed
        thumb = img.copy()
        thumb.thumbnail((100, 100))

        # Check number of unique colors
        if thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        # Convert to numpy array
        arr = np.array(thumb)
        unique_colors = len(np.unique(arr.reshape(-1, arr.shape[2]), axis=0))

        # Threshold: if < 200 unique colors in a 100x100 thumb, likely a chart/UI
        if unique_colors < 500:
            return "chart"
        return "photo"

    def _optimize_for_tiles(self, img: "Image.Image", tile_size: int = 512) -> "Image.Image":
        """Resize image to minimize token usage based on tile grid.

        If image is just slightly larger than a tile boundary (e.g. 515px),
        resizing to 512px saves entire tiles.
        """
        width, height = img.size

        # Calculate potential savings

        # Check if we can snap to grid within 10% visual loss limit
        new_w = width
        new_h = height

        if width % tile_size < 50 and width > tile_size:
            # Snap width down
            new_w = (width // tile_size) * tile_size

        if height % tile_size < 50 and height > tile_size:
            # Snap height down
            new_h = (height // tile_size) * tile_size

        if new_w != width or new_h != height:
            # Resize strictly maintaining aspect ratio to fit within the smaller grid.
            target_w = (width // tile_size) * tile_size

            # If dimensions are close to grid, force resize
            if width > target_w and (width - target_w) < 50:
                img = img.resize(
                    (target_w, int(height * (target_w / width))), Image.Resampling.LANCZOS
                )

        return img
