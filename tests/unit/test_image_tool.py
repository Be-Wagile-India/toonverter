import base64
import io
from unittest.mock import patch

import pytest

from toonverter.core.types import ImageDetail, ImageOptimizeOptions, ToonImage
from toonverter.multimodal.image_tool import ImageOptimizer


# Mock PIL if not available
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


@pytest.fixture
def optimizer():
    """Create ImageOptimizer instance."""
    return ImageOptimizer()


@pytest.fixture
def default_options():
    """Create default ImageOptimizeOptions."""
    return ImageOptimizeOptions()


@pytest.fixture
def mock_image():
    """Create a mock PIL Image."""
    if not PIL_AVAILABLE:
        pytest.skip("PIL not available")

    return Image.new("RGB", (800, 600), color="red")


@pytest.fixture
def mock_rgba_image():
    """Create a mock RGBA PIL Image with transparency."""
    if not PIL_AVAILABLE:
        pytest.skip("PIL not available")

    return Image.new("RGBA", (800, 600), color=(255, 0, 0, 128))


class TestImageOptimizerInit:
    """Test suite for ImageOptimizer initialization."""

    def test_init_with_pil_available(self, optimizer):
        """Test initialization when PIL is available."""
        assert optimizer is not None

    @patch("toonverter.multimodal.image_tool.PIL_AVAILABLE", False)
    def test_init_without_pil_logs_warning(self, caplog):
        """Test that warning is logged when PIL is not available."""
        with (
            patch("toonverter.multimodal.image_tool.Image", None),
            patch("toonverter.multimodal.image_tool.ImageOps", None),
        ):
            ImageOptimizer()
            assert "Pillow not installed" in caplog.text


class TestProcessImage:
    """Test suite for process_image method."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_from_pil_object(self, optimizer, mock_image, default_options):
        """Test processing a PIL Image object directly."""
        result = optimizer.process_image(mock_image, default_options)

        assert isinstance(result, ToonImage)
        assert result.mime_type == "image/jpeg"
        assert result.detail == ImageDetail.AUTO
        assert result.token_cost > 0
        assert not result.is_url
        assert len(result.data) > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_from_bytes(self, optimizer, mock_image, default_options):
        """Test processing image from bytes."""
        buffer = io.BytesIO()
        mock_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = optimizer.process_image(image_bytes, default_options)

        assert isinstance(result, ToonImage)
        assert result.mime_type == "image/jpeg"
        assert not result.is_url

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_from_url(self, optimizer, default_options):
        """Test processing image from URL returns ToonImage directly."""
        url = "https://example.com/image.jpg"

        result = optimizer.process_image(url, default_options)

        assert isinstance(result, ToonImage)
        assert result.data == url
        assert result.is_url
        assert result.token_cost == 85

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_with_rgba(self, optimizer, mock_rgba_image, default_options):
        """Test processing RGBA image converts to RGB."""
        result = optimizer.process_image(mock_rgba_image, default_options)

        assert isinstance(result, ToonImage)
        assert result.mime_type == "image/jpeg"
        assert not result.is_url

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_resizes_large_image(self, optimizer, default_options):
        """Test that large images are resized."""
        large_image = Image.new("RGB", (2000, 1500), color="blue")

        result = optimizer.process_image(large_image, default_options)

        assert isinstance(result, ToonImage)
        # Token cost should reflect resized dimensions
        assert result.token_cost > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_with_custom_options(self, optimizer, mock_image):
        """Test processing with custom optimization options."""
        options = ImageOptimizeOptions(
            max_dimension=512, detail=ImageDetail.LOW, format="PNG", quality=70
        )

        result = optimizer.process_image(mock_image, options)

        assert isinstance(result, ToonImage)
        assert result.mime_type == "image/png"
        assert result.detail == ImageDetail.LOW

    @patch("toonverter.multimodal.image_tool.PIL_AVAILABLE", False)
    def test_process_image_without_pil_raises_error(self, default_options):
        """Test that processing without PIL raises ImportError."""
        with (
            patch("toonverter.multimodal.image_tool.Image", None),
            patch("toonverter.multimodal.image_tool.ImageOps", None),
        ):
            optimizer = ImageOptimizer()
            with pytest.raises(ImportError, match="Pillow library required"):
                optimizer.process_image("fake_image.jpg", default_options)

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_with_nonexistent_file(self, optimizer, default_options):
        """Test processing nonexistent file raises ValueError."""
        with pytest.raises(ValueError, match="Image file not found"):
            optimizer.process_image("/nonexistent/file.jpg", default_options)

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_process_image_with_invalid_source(self, optimizer, default_options):
        """Test processing invalid source raises ValueError."""
        with pytest.raises(ValueError, match="Invalid image source"):
            optimizer.process_image(12345, default_options)


class TestLoadImage:
    """Test suite for _load_image method."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_from_http_url(self, optimizer):
        """Test loading image from HTTP URL."""
        url = "http://example.com/image.jpg"
        result = optimizer._load_image(url)

        assert isinstance(result, ToonImage)
        assert result.is_url
        assert result.data == url

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_from_https_url(self, optimizer):
        """Test loading image from HTTPS URL."""
        url = "https://example.com/image.jpg"
        result = optimizer._load_image(url)

        assert isinstance(result, ToonImage)
        assert result.is_url
        assert result.data == url

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_from_bytes(self, optimizer, mock_image):
        """Test loading image from bytes."""
        buffer = io.BytesIO()
        mock_image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        result = optimizer._load_image(image_bytes)

        assert isinstance(result, Image.Image)
        assert result.size == (800, 600)

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_from_pil_object(self, optimizer, mock_image):
        """Test loading image from PIL object."""
        result = optimizer._load_image(mock_image)

        assert isinstance(result, Image.Image)
        assert result is mock_image

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_from_path_object(self, optimizer, tmp_path, mock_image):
        """Test loading image from Path object."""
        img_path = tmp_path / "test.png"
        mock_image.save(img_path)

        result = optimizer._load_image(img_path)

        assert isinstance(result, Image.Image)
        result.close()  # Close to avoid ResourceWarning

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_load_image_invalid_bytes(self, optimizer):
        """Test loading invalid bytes raises ValueError."""
        invalid_bytes = b"not an image"

        with pytest.raises(ValueError, match="Invalid image source"):
            optimizer._load_image(invalid_bytes)


class TestFlattenAlphaToWhite:
    """Test suite for _flatten_alpha_to_white method."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_flatten_rgba_image(self, optimizer):
        """Test flattening RGBA image to RGB with white background."""
        rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))

        result = optimizer._flatten_alpha_to_white(rgba_img)

        assert result.mode == "RGB"
        assert result.size == (100, 100)

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_flatten_palette_image_with_transparency(self, optimizer):
        """Test flattening palette image with transparency."""
        p_img = Image.new("P", (100, 100))
        p_img.info["transparency"] = 0

        result = optimizer._flatten_alpha_to_white(p_img)

        assert result.mode == "RGB"

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_flatten_la_image(self, optimizer):
        """Test flattening LA (grayscale with alpha) image."""
        la_img = Image.new("LA", (100, 100), color=(128, 128))

        result = optimizer._flatten_alpha_to_white(la_img)

        assert result.mode == "RGB"


class TestResizeImage:
    """Test suite for _resize_image method."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_resize_image_width_larger(self, optimizer):
        """Test resizing when width is larger than height."""
        img = Image.new("RGB", (2000, 1000), color="red")

        result = optimizer._resize_image(img, 1024)

        assert result.size[0] == 1024
        assert result.size[1] == 512

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_resize_image_height_larger(self, optimizer):
        """Test resizing when height is larger than width."""
        img = Image.new("RGB", (1000, 2000), color="blue")

        result = optimizer._resize_image(img, 1024)

        assert result.size[0] == 512
        assert result.size[1] == 1024

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_resize_image_no_resize_needed(self, optimizer):
        """Test that small images are not resized."""
        img = Image.new("RGB", (500, 300), color="green")

        result = optimizer._resize_image(img, 1024)

        assert result.size == (500, 300)
        assert result is img

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_resize_image_exact_dimension(self, optimizer):
        """Test resizing when image is exactly max dimension."""
        img = Image.new("RGB", (1024, 1024), color="yellow")

        result = optimizer._resize_image(img, 1024)

        assert result.size == (1024, 1024)
        assert result is img


class TestCompressToTarget:
    """Test suite for _compress_to_target method."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_jpeg_format(self, optimizer, mock_image):
        """Test compression to JPEG format."""
        options = ImageOptimizeOptions(format="JPEG", quality=85)

        b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/jpeg"
        assert len(b64_data) > 0
        # Verify it's valid base64
        base64.b64decode(b64_data)

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_png_format(self, optimizer, mock_image):
        """Test compression to PNG format."""
        options = ImageOptimizeOptions(format="PNG", quality=85)

        b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/png"
        assert len(b64_data) > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_webp_format(self, optimizer, mock_image):
        """Test compression to WEBP format."""
        options = ImageOptimizeOptions(format="WEBP", quality=85)

        b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/webp"
        assert len(b64_data) > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_with_size_limit(self, optimizer, mock_image):
        """Test compression with max_size_kb limit."""
        options = ImageOptimizeOptions(format="JPEG", quality=85, max_size_kb=10)

        b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/jpeg"
        # Verify size is under or near limit (might be slightly over in final attempt)
        decoded = base64.b64decode(b64_data)
        assert len(decoded) <= 15 * 1024  # Allow some tolerance

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_without_size_limit(self, optimizer, mock_image):
        """Test compression without size limit."""
        options = ImageOptimizeOptions(format="JPEG", quality=95, max_size_kb=None)

        b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/jpeg"
        assert len(b64_data) > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_compress_with_invalid_format_fallback(self, optimizer, mock_image):
        """Test that invalid format falls back to JPEG."""
        options = ImageOptimizeOptions(format="INVALID", quality=85)

        _b64_data, mime = optimizer._compress_to_target(mock_image, options)

        assert mime == "image/jpeg"


class TestEstimateVisionTokens:
    """Test suite for _estimate_vision_tokens method."""

    def test_estimate_tokens_low_detail(self, optimizer):
        """Test token estimation for low detail."""
        tokens = optimizer._estimate_vision_tokens((1000, 1000), ImageDetail.LOW)
        assert tokens == 85

    def test_estimate_tokens_small_image(self, optimizer):
        """Test token estimation for small image."""
        tokens = optimizer._estimate_vision_tokens((512, 512), ImageDetail.AUTO)
        # Should be base cost + 1 tile (170 + 85)
        assert tokens == 255

    def test_estimate_tokens_large_image(self, optimizer):
        """Test token estimation for large image."""
        tokens = optimizer._estimate_vision_tokens((2048, 2048), ImageDetail.HIGH)
        # Large image should have multiple tiles
        assert tokens > 255

    def test_estimate_tokens_wide_image(self, optimizer):
        """Test token estimation for wide aspect ratio."""
        tokens = optimizer._estimate_vision_tokens((2048, 512), ImageDetail.AUTO)
        assert tokens > 85

    def test_estimate_tokens_tall_image(self, optimizer):
        """Test token estimation for tall aspect ratio."""
        tokens = optimizer._estimate_vision_tokens((512, 2048), ImageDetail.AUTO)
        assert tokens > 85

    def test_estimate_tokens_oversized_image(self, optimizer):
        """Test token estimation for image larger than 2048x2048."""
        tokens = optimizer._estimate_vision_tokens((4000, 3000), ImageDetail.AUTO)
        # Should scale down and calculate tiles
        assert tokens > 0

    def test_estimate_tokens_exact_tile_boundary(self, optimizer):
        """Test token estimation at exact tile boundary."""
        tokens = optimizer._estimate_vision_tokens((1024, 1024), ImageDetail.AUTO)
        # Should be base + multiple tiles
        assert tokens > 255


class TestIntegration:
    """Integration tests for complete workflows."""

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_full_workflow_with_file(self, optimizer, tmp_path):
        """Test complete workflow from file to ToonImage."""
        # Create test image file
        img = Image.new("RGB", (1200, 800), color="purple")
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        options = ImageOptimizeOptions(
            max_dimension=800, detail=ImageDetail.HIGH, format="JPEG", quality=80
        )

        result = optimizer.process_image(str(img_path), options)

        assert isinstance(result, ToonImage)
        assert result.detail == ImageDetail.HIGH
        assert not result.is_url
        assert result.token_cost > 0

    @pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL not available")
    def test_full_workflow_with_transparency(self, optimizer):
        """Test complete workflow with RGBA image."""
        rgba_img = Image.new("RGBA", (600, 400), color=(0, 255, 0, 200))

        options = ImageOptimizeOptions(max_dimension=512, detail=ImageDetail.AUTO, format="JPEG")

        result = optimizer.process_image(rgba_img, options)

        assert isinstance(result, ToonImage)
        assert result.mime_type == "image/jpeg"
        assert not result.is_url
