"""Example of optimizing images for vision models.

This example demonstrates how to use toonverter's vision optimization tools
to reduce token usage and costs when working with multimodal LLMs.
"""

import base64
import os
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import toonverter as toon


def create_sample_image(path: str) -> None:
    """Create a sample image for testing."""
    if not PIL_AVAILABLE:
        print("Pillow not installed, skipping image creation.")
        return

    img = Image.new('RGB', (2048, 2048), color='red')
    img.save(path)
    print(f"Created sample image at {path} ({os.path.getsize(path) / 1024:.1f} KB)")


def run_vision_optimization():
    """Run vision optimization examples."""
    print("---""" Vision Optimization Example ---"""")

    if not PIL_AVAILABLE:
        print("Error: This example requires Pillow. Install with: pip install Pillow")
        return

    # Create a large sample image
    image_path = "sample_large.png"
    create_sample_image(image_path)

    try:
        # Read raw bytes
        with open(image_path, "rb") as f:
            raw_bytes = f.read()

        print(f"Original Size: {len(raw_bytes) / 1024:.1f} KB")

        # 1. Optimize for OpenAI (GPT-4o)
        print("\nOptimizing for OpenAI (GPT-4o)...")
        opt_bytes_openai, mime_openai = toon.optimize_vision(
            raw_bytes,
            provider="openai"
        )
        print(f"Optimized Size: {len(opt_bytes_openai) / 1024:.1f} KB")
        print(f"Format: {mime_openai}")
        
        # Calculate savings
        savings = (len(raw_bytes) - len(opt_bytes_openai)) / len(raw_bytes) * 100
        print(f"Savings: {savings:.1f}%")

        # 2. Get provider-specific payload directly
        print("\nGenerating Anthropic payload...")
        payload = toon.optimize_vision(
            raw_bytes,
            provider="anthropic",
            return_payload=True
        )
        # Payload structure for Anthropic API
        print("Payload keys:", payload.keys())
        print(f"Media Type: {payload['source']['media_type']}")

    finally:
        # Cleanup
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"\nRemoved {image_path}")


if __name__ == "__main__":
    run_vision_optimization()
