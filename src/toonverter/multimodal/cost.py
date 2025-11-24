"""Cost estimation for vision models."""

import math
from enum import Enum


class VisionProvider(str, Enum):
    """Supported Vision Providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class CostEstimator:
    """Estimates token cost for images based on provider logic."""

    def estimate_cost(
        self,
        width: int,
        height: int,
        provider: VisionProvider = VisionProvider.OPENAI,
        detail: str = "auto",
    ) -> int:
        """Estimate token cost for an image.

        Args:
            width: Image width
            height: Image height
            provider: Provider name (openai, anthropic)
            detail: Detail level (low, high, auto) - OpenAI only

        Returns:
            Estimated token count
        """
        if provider == VisionProvider.OPENAI:
            return self._estimate_openai(width, height, detail)
        if provider == VisionProvider.ANTHROPIC:
            return self._estimate_anthropic(width, height)
        return 0  # type: ignore[unreachable]

    def _estimate_openai(self, width: int, height: int, detail: str) -> int:
        """OpenAI Vision pricing model (GPT-4o / GPT-4-Turbo)."""
        # Low detail mode
        if detail == "low":
            return 85

        # High/Auto detail mode
        # 1. Scale to fit within 2048 x 2048
        if width > 2048 or height > 2048:
            ratio = min(2048 / width, 2048 / height)
            width = int(width * ratio)
            height = int(height * ratio)

        # 2. Scale such that the shortest side is 768px
        if width >= height > 768:
            width = int(width * (768 / height))
            height = 768
        elif height > width > 768:
            height = int(height * (768 / width))
            width = 768

        # 3. Calculate 512px tiles
        tiles_width = math.ceil(width / 512)
        tiles_height = math.ceil(height / 512)
        total_tiles = tiles_width * tiles_height

        # Cost = 170 tokens per tile + 85 base tokens
        return (total_tiles * 170) + 85

    def _estimate_anthropic(self, width: int, height: int) -> int:
        """Anthropic Claude 3 Vision pricing model.

        Approximate calculation: (width * height) / 750
        """
        return math.ceil((width * height) / 750)
