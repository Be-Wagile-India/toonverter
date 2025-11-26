"""Tests for Multimodal Optimization."""

from unittest.mock import ANY, MagicMock, patch

import pytest

from toonverter.multimodal import CostEstimator, VisionProvider


class TestCostEstimator:
    def test_openai_cost_low_detail(self):
        estimator = CostEstimator()
        cost = estimator.estimate_cost(1024, 1024, provider=VisionProvider.OPENAI, detail="low")
        assert cost == 85

    def test_openai_cost_high_detail_simple(self):
        # 512x512 image -> 1 tile + base
        estimator = CostEstimator()
        cost = estimator.estimate_cost(512, 512, provider=VisionProvider.OPENAI)
        # 1 tile * 170 + 85 = 255
        assert cost == 255

    def test_openai_cost_large_image(self):
        # 2048x2048 -> 768x768 (shortest side 768)
        # 4 tiles
        estimator = CostEstimator()
        cost = estimator.estimate_cost(2048, 2048, provider=VisionProvider.OPENAI)
        assert cost == 765

    def test_openai_cost_wide_image(self):
        # Wide image: 2048x512
        # Shortest side 512 <= 768. No scaling needed for short side?
        # But 2048 > 2048? No.
        # Let's try 4096x1024.
        # Scale to fit 2048x2048 -> 2048x512.
        # Shortest side 512 <= 768.
        # Tiles: ceil(2048/512)=4, ceil(512/512)=1. Total 4 tiles.
        estimator = CostEstimator()
        cost = estimator.estimate_cost(4096, 1024, provider=VisionProvider.OPENAI)
        # 4 * 170 + 85 = 765
        assert cost == 765

    def test_openai_cost_tall_image(self):
        # Tall image: 1024x4096
        estimator = CostEstimator()
        cost = estimator.estimate_cost(1024, 4096, provider=VisionProvider.OPENAI)
        assert cost == 765

    def test_openai_cost_resize_short_side(self):
        # Image where scaling by 2048 doesn't reduce short side enough.
        # e.g. 1500x1500. Fits in 2048.
        # Short side 1500 > 768.
        # Scale to 768x768.
        # Tiles: ceil(768/512)=2, 2x2=4 tiles.
        estimator = CostEstimator()
        cost = estimator.estimate_cost(1500, 1500, provider=VisionProvider.OPENAI)
        assert cost == 765

    def test_anthropic_cost(self):
        estimator = CostEstimator()
        cost = estimator.estimate_cost(1000, 1000, provider=VisionProvider.ANTHROPIC)
        # 1,000,000 / 750 = 1333.33 -> 1334
        assert cost == 1334

    def test_unknown_provider(self):
        estimator = CostEstimator()
        # cast to string to bypass type check for test
        cost = estimator.estimate_cost(100, 100, provider="unknown")  # type: ignore
        assert cost == 0


# Mocking PIL/numpy for Processor tests if not installed
@patch("toonverter.multimodal.processor.VISION_AVAILABLE", True)
@patch("toonverter.multimodal.processor.Image")
@patch("toonverter.multimodal.processor.np")
class TestSmartImageProcessor:
    def test_init_raises_if_missing_deps(self, mock_np, mock_image):
        with patch("toonverter.multimodal.processor.VISION_AVAILABLE", False):
            from toonverter.multimodal import SmartImageProcessor

            with pytest.raises(ImportError):
                SmartImageProcessor()

    def test_process_chart_detection(self, mock_np, mock_image):
        from toonverter.multimodal import SmartImageProcessor

        # Mock Image object
        mock_img_instance = MagicMock()
        mock_img_instance.mode = "RGB"
        mock_img_instance.size = (500, 500)
        mock_image.open.return_value = mock_img_instance

        # Mock numpy analysis for "chart" (low unique colors)
        mock_arr = MagicMock()
        mock_arr.shape = (100, 100, 3)
        mock_np.array.return_value = mock_arr
        mock_np.unique.return_value = list(range(100))  # 100 unique colors < 500
        mock_np.reshape = MagicMock()

        processor = SmartImageProcessor()
        _, mime = processor.process(b"fake_data", target_provider="openai")

        assert mime == "image/png"
        mock_img_instance.save.assert_called_with(ANY, format="PNG", optimize=True)

    def test_process_photo_detection(self, mock_np, mock_image):
        from toonverter.multimodal import SmartImageProcessor

        # Mock Image object
        mock_img_instance = MagicMock()
        mock_img_instance.mode = "RGB"
        mock_img_instance.size = (500, 500)
        mock_image.open.return_value = mock_img_instance

        # Mock numpy analysis for "photo" (high unique colors)
        mock_np.unique.return_value = list(range(600))  # > 500

        processor = SmartImageProcessor()
        _, mime = processor.process(b"fake_data", target_provider="openai")

        assert mime == "image/jpeg"
        mock_img_instance.save.assert_called_with(ANY, format="JPEG", quality=85, optimize=True)

    def test_process_convert_rgba(self, mock_np, mock_image):
        from toonverter.multimodal import SmartImageProcessor

        mock_img_instance = MagicMock()
        mock_img_instance.mode = "RGBA"
        mock_img_instance.size = (500, 500)
        mock_img_instance.convert.return_value = mock_img_instance  # Return self for chaining
        mock_image.open.return_value = mock_img_instance

        # Photo content
        mock_np.unique.return_value = list(range(600))

        processor = SmartImageProcessor()
        processor.process(b"fake", target_provider="openai")

        # Should verify convert called
        # Note: convert is called twice (once for thumb, once for main image if RGBA)
        # Using any_call to be safe
        mock_img_instance.convert.assert_any_call("RGB")

    def test_optimize_for_tiles_snapping(self, mock_np, mock_image):
        from toonverter.multimodal import SmartImageProcessor

        # Mock image 515x515 -> Should snap to 512x512
        mock_img_instance = MagicMock()
        mock_img_instance.mode = "RGB"
        mock_img_instance.size = (515, 515)
        # Mock resize to return a new mock
        resized_mock = MagicMock()
        resized_mock.size = (512, 512)
        mock_img_instance.resize.return_value = resized_mock

        mock_image.open.return_value = mock_img_instance

        processor = SmartImageProcessor()

        # Access protected method for direct testing
        processor._optimize_for_tiles(mock_img_instance)

        mock_img_instance.resize.assert_called()

        # Check args (512, 512)
        args = mock_img_instance.resize.call_args[0]
        assert args[0] == (512, 512)

    def test_optimize_for_tiles_no_snapping(self, mock_np, mock_image):
        from toonverter.multimodal import SmartImageProcessor

        # Mock image 570x570 -> Too far from 512 to snap (58px diff > 50px threshold)
        mock_img_instance = MagicMock()
        mock_img_instance.mode = "RGB"
        mock_img_instance.size = (570, 570)
        mock_image.open.return_value = mock_img_instance

        processor = SmartImageProcessor()
        optimized = processor._optimize_for_tiles(mock_img_instance)

        # Should NOT resize
        mock_img_instance.resize.assert_not_called()
        assert optimized == mock_img_instance


class TestVendorAdapters:
    def test_openai_adapter(self):
        from toonverter.multimodal.vendors import OpenAIAdapter

        adapter = OpenAIAdapter()
        payload = adapter.format(b"test_data", "image/jpeg")

        assert payload["type"] == "image_url"
        assert payload["image_url"]["detail"] == "auto"
        assert "data:image/jpeg;base64,dGVzdF9kYXRh" in payload["image_url"]["url"]

    def test_anthropic_adapter(self):
        from toonverter.multimodal.vendors import AnthropicAdapter

        adapter = AnthropicAdapter()
        payload = adapter.format(b"test_data", "image/png")

        assert payload["type"] == "image"
        assert payload["source"]["type"] == "base64"
        assert payload["source"]["media_type"] == "image/png"
        assert payload["source"]["data"] == "dGVzdF9kYXRh"

    def test_get_adapter_invalid(self):
        from toonverter.multimodal.vendors import get_vendor_adapter

        with pytest.raises(ValueError, match="Unsupported vision provider"):
            get_vendor_adapter("unknown_provider")
