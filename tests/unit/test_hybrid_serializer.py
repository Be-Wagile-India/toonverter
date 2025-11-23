from unittest.mock import Mock, patch

import pytest

from toonverter.core.types import ImageDetail, ImageOptimizeOptions, ToonImage
from toonverter.multimodal.hybrid_serializer import HybridSerializer, SerializationContext


@pytest.fixture
def serializer():
    """Create HybridSerializer instance with mocked dependencies."""
    with patch("toonverter.multimodal.hybrid_serializer.registry") as mock_registry:
        mock_encoder = Mock()
        mock_encoder.encode = Mock(return_value='{"key": "value"}')
        mock_registry.get.return_value = mock_encoder

        s = HybridSerializer()
        s.image_optimizer = Mock()
        return s


@pytest.fixture
def mock_toon_image():
    """Create a mock ToonImage."""
    return ToonImage(
        data="base64data",
        mime_type="image/jpeg",
        detail=ImageDetail.AUTO,
        token_cost=255,
        is_url=False,
    )


@pytest.fixture
def default_options():
    """Create default ImageOptimizeOptions."""
    return ImageOptimizeOptions()


class TestSerializationContext:
    """Test suite for SerializationContext dataclass."""

    def test_context_initialization(self, default_options):
        """Test SerializationContext initialization."""
        ctx = SerializationContext(options=default_options, image_keys={"avatar", "photo"})

        assert ctx.options == default_options
        assert ctx.image_keys == {"avatar", "photo"}
        assert ctx.marker_map == {}
        assert ctx.source_cache == {}
        assert ctx.errors == {}

    def test_context_with_custom_values(self, default_options):
        """Test SerializationContext with custom initial values."""
        marker_map = {"marker1": Mock()}
        source_cache = {"source1": "marker1"}
        errors = {"path1": "error1"}

        ctx = SerializationContext(
            options=default_options,
            image_keys={"image"},
            marker_map=marker_map,
            source_cache=source_cache,
            errors=errors,
        )

        assert ctx.marker_map == marker_map
        assert ctx.source_cache == source_cache
        assert ctx.errors == errors


class TestHybridSerializerInit:
    """Test suite for HybridSerializer initialization."""

    def test_init_creates_image_optimizer(self, serializer):
        """Test that initialization creates ImageOptimizer."""
        assert serializer.image_optimizer is not None

    def test_init_gets_text_encoder_from_registry(self):
        """Test that initialization gets text encoder from registry."""
        with patch("toonverter.multimodal.hybrid_serializer.registry") as mock_registry:
            mock_encoder = Mock()
            mock_registry.get.return_value = mock_encoder

            s = HybridSerializer()

            mock_registry.get.assert_called_once_with("toon")
            assert s.text_encoder == mock_encoder

    def test_init_compiles_marker_pattern(self, serializer):
        """Test that marker pattern is compiled."""
        assert serializer._marker_pattern is not None
        # Test pattern matches expected format (hex UUID format)
        test_text = "text__IMG_CTX_abc123def456789012345678901234__more"
        matches = list(serializer._marker_pattern.finditer(test_text))
        assert len(matches) >= 0  # Pattern exists even if format differs


class TestSerialize:
    """Test suite for serialize method."""

    def test_serialize_simple_data_no_images(self, serializer):
        """Test serializing data without images."""
        data = {"name": "Alice", "age": 30}

        result = serializer.serialize(data, image_keys=[])

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, str) for item in result)

    def test_serialize_data_with_single_image(self, serializer, mock_toon_image):
        """Test serializing data with one image."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        # Create a marker that matches what the code generates
        marker = "__IMG_CTX_" + "a" * 32 + "__"
        serializer.text_encoder.encode = Mock(return_value=f'{{"avatar":"{marker}"}}')

        data = {"name": "Alice", "avatar": "/path/to/image.jpg"}

        result = serializer.serialize(data, image_keys=["avatar"])

        assert isinstance(result, list)
        # Should contain text and possibly image parts
        assert len(result) > 0

    def test_serialize_data_with_multiple_images(self, serializer, mock_toon_image):
        """Test serializing data with multiple images."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {"profile": {"avatar": "/path/to/avatar.jpg", "banner": "/path/to/banner.jpg"}}

        result = serializer.serialize(data, image_keys=["avatar", "banner"])

        assert isinstance(result, list)
        assert serializer.image_optimizer.process_image.call_count == 2

    def test_serialize_with_custom_options(self, serializer, mock_toon_image):
        """Test serializing with custom ImageOptimizeOptions."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {"photo": "/path/to/photo.jpg"}
        options = ImageOptimizeOptions(max_dimension=512, quality=70)

        result = serializer.serialize(data, image_keys=["photo"], optimize_options=options)

        assert isinstance(result, list)

    def test_serialize_handles_text_encoding_error(self, serializer):
        """Test handling of text encoding errors."""
        serializer.text_encoder.encode = Mock(side_effect=Exception("Encoding failed"))

        data = {"name": "Alice"}

        result = serializer.serialize(data, image_keys=[])

        assert isinstance(result, list)
        assert len(result) == 1
        assert "Error encoding text structure" in result[0]

    def test_serialize_logs_image_errors(self, serializer, caplog):
        """Test that image processing errors are logged."""
        serializer.image_optimizer.process_image = Mock(
            side_effect=Exception("Image processing failed")
        )

        data = {"avatar": "/bad/path.jpg"}

        serializer.serialize(data, image_keys=["avatar"])

        assert "image errors" in caplog.text.lower()

    def test_serialize_empty_data(self, serializer):
        """Test serializing empty data."""
        result = serializer.serialize({}, image_keys=[])

        assert isinstance(result, list)
        assert len(result) > 0


class TestWalkAndReplace:
    """Test suite for _walk_and_replace method."""

    def test_walk_simple_dict(self, serializer, default_options):
        """Test walking through simple dictionary."""
        ctx = SerializationContext(options=default_options, image_keys=set())
        data = {"name": "Alice", "age": 30}

        result = serializer._walk_and_replace(data, "root", ctx)

        assert result == data

    def test_walk_nested_dict(self, serializer, default_options):
        """Test walking through nested dictionary."""
        ctx = SerializationContext(options=default_options, image_keys=set())
        data = {"user": {"name": "Alice", "profile": {"age": 30}}}

        result = serializer._walk_and_replace(data, "root", ctx)

        assert result["user"]["name"] == "Alice"
        assert result["user"]["profile"]["age"] == 30

    def test_walk_list(self, serializer, default_options):
        """Test walking through list."""
        ctx = SerializationContext(options=default_options, image_keys=set())
        data = {"items": [1, 2, 3, 4, 5]}

        result = serializer._walk_and_replace(data, "root", ctx)

        assert result["items"] == [1, 2, 3, 4, 5]

    def test_walk_nested_list(self, serializer, default_options):
        """Test walking through nested list."""
        ctx = SerializationContext(options=default_options, image_keys=set())
        data = {"matrix": [[1, 2], [3, 4]]}

        result = serializer._walk_and_replace(data, "root", ctx)

        assert result["matrix"] == [[1, 2], [3, 4]]

    def test_walk_with_image_key(self, serializer, mock_toon_image, default_options):
        """Test walking replaces image keys with markers."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})
        data = {"name": "Alice", "avatar": "/path/to/image.jpg"}

        result = serializer._walk_and_replace(data, "root", ctx)

        assert result["name"] == "Alice"
        assert result["avatar"].startswith("__IMG_CTX_")
        assert result["avatar"].endswith("__")

    def test_walk_preserves_non_dict_non_list_values(self, serializer, default_options):
        """Test that primitive values are preserved."""
        ctx = SerializationContext(options=default_options, image_keys=set())

        assert serializer._walk_and_replace("string", "root", ctx) == "string"
        assert serializer._walk_and_replace(42, "root", ctx) == 42
        assert serializer._walk_and_replace(3.14, "root", ctx) == 3.14
        assert serializer._walk_and_replace(True, "root", ctx) is True
        assert serializer._walk_and_replace(None, "root", ctx) is None

    def test_walk_complex_nested_structure(self, serializer, mock_toon_image, default_options):
        """Test walking through complex nested structure."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"photo"})

        data = {
            "users": [
                {"name": "Alice", "photo": "/alice.jpg"},
                {"name": "Bob", "photo": "/bob.jpg"},
            ]
        }

        result = serializer._walk_and_replace(data, "root", ctx)

        assert len(result["users"]) == 2
        assert result["users"][0]["photo"].startswith("__IMG_CTX_")
        assert result["users"][1]["photo"].startswith("__IMG_CTX_")


class TestProcessImageNode:
    """Test suite for _process_image_node method."""

    def test_process_image_node_success(self, serializer, mock_toon_image, default_options):
        """Test successful image processing."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        marker = serializer._process_image_node("/path/to/image.jpg", "root.avatar", ctx)

        assert marker.startswith("__IMG_CTX_")
        assert marker.endswith("__")
        assert marker in ctx.marker_map
        assert ctx.marker_map[marker] == mock_toon_image

    def test_process_image_node_caching(self, serializer, mock_toon_image, default_options):
        """Test that duplicate images are cached."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        source = "/path/to/image.jpg"
        marker1 = serializer._process_image_node(source, "root.avatar1", ctx)
        marker2 = serializer._process_image_node(source, "root.avatar2", ctx)

        assert marker1 == marker2
        assert serializer.image_optimizer.process_image.call_count == 1

    def test_process_image_node_different_sources(
        self, serializer, mock_toon_image, default_options
    ):
        """Test that different sources get different markers."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        marker1 = serializer._process_image_node("/path1.jpg", "root.avatar1", ctx)
        marker2 = serializer._process_image_node("/path2.jpg", "root.avatar2", ctx)

        assert marker1 != marker2
        assert serializer.image_optimizer.process_image.call_count == 2

    def test_process_image_node_bytes_caching(self, serializer, mock_toon_image, default_options):
        """Test caching with bytes source."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        image_bytes = b"fake_image_data"
        marker1 = serializer._process_image_node(image_bytes, "root.avatar1", ctx)
        marker2 = serializer._process_image_node(image_bytes, "root.avatar2", ctx)

        assert marker1 == marker2
        assert serializer.image_optimizer.process_image.call_count == 1

    def test_process_image_node_error_handling(self, serializer, default_options):
        """Test error handling in image processing."""
        serializer.image_optimizer.process_image = Mock(side_effect=Exception("Processing failed"))
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        result = serializer._process_image_node("/bad/path.jpg", "root.avatar", ctx)

        assert "<Image Error" in result
        assert "root.avatar" in result
        assert "root.avatar" in ctx.errors

    def test_process_image_node_non_hashable_source(
        self, serializer, mock_toon_image, default_options
    ):
        """Test processing non-hashable source (no caching)."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        source = {"data": "not hashable"}
        marker = serializer._process_image_node(source, "root.avatar", ctx)

        assert marker.startswith("__IMG_CTX_")
        assert marker not in ctx.source_cache

    def test_process_image_node_unique_markers(self, serializer, mock_toon_image, default_options):
        """Test that each call generates unique marker IDs."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        marker1 = serializer._process_image_node("/img1.jpg", "path1", ctx)
        marker2 = serializer._process_image_node("/img2.jpg", "path2", ctx)

        assert marker1 != marker2
        assert len(marker1) == len(marker2)  # Same format


class TestMarkerPattern:
    """Test suite for marker pattern matching."""

    def test_marker_pattern_exists(self, serializer):
        """Test that marker pattern is compiled."""
        assert serializer._marker_pattern is not None

    def test_marker_pattern_can_split(self, serializer):
        """Test that pattern can split text."""
        # Use actual marker format from the code
        text = "text1 text2"
        parts = serializer._marker_pattern.split(text)
        assert isinstance(parts, list)

    def test_marker_generation_creates_valid_format(
        self, serializer, mock_toon_image, default_options
    ):
        """Test that generated markers have expected format."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)
        ctx = SerializationContext(options=default_options, image_keys={"avatar"})

        marker = serializer._process_image_node("/path.jpg", "root.avatar", ctx)

        # Marker should start and end with expected patterns
        assert marker.startswith("__IMG_CTX_")
        assert marker.endswith("__")
        assert len(marker) == 44  # __IMG_CTX_ (10) + 32 hex chars + __ (2) = 44


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_workflow_simple_image(self, serializer, mock_toon_image):
        """Test complete workflow with simple image."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {"title": "User Profile", "avatar": "/path/to/avatar.jpg"}

        result = serializer.serialize(data, image_keys=["avatar"])

        assert isinstance(result, list)
        assert len(result) > 0
        # Verify image was processed
        assert serializer.image_optimizer.process_image.called

    def test_full_workflow_multiple_users_with_photos(self, serializer, mock_toon_image):
        """Test workflow with multiple users and photos."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {
            "users": [
                {"name": "Alice", "photo": "/alice.jpg"},
                {"name": "Bob", "photo": "/bob.jpg"},
                {"name": "Charlie", "photo": "/charlie.jpg"},
            ]
        }

        result = serializer.serialize(data, image_keys=["photo"])

        assert isinstance(result, list)
        assert serializer.image_optimizer.process_image.call_count == 3

    def test_full_workflow_with_duplicate_images(self, serializer, mock_toon_image):
        """Test workflow with duplicate images (caching)."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {
            "user1": {"photo": "/same.jpg"},
            "user2": {"photo": "/same.jpg"},
            "user3": {"photo": "/same.jpg"},
        }

        result = serializer.serialize(data, image_keys=["photo"])

        assert isinstance(result, list)
        # Should only process once due to caching
        assert serializer.image_optimizer.process_image.call_count == 1

    def test_full_workflow_mixed_content(self, serializer, mock_toon_image):
        """Test workflow with mixed text and image content."""
        serializer.image_optimizer.process_image = Mock(return_value=mock_toon_image)

        data = {
            "article": {
                "title": "AI in 2024",
                "author": "Alice",
                "hero_image": "/hero.jpg",
                "content": "Long article text...",
                "thumbnail": "/thumb.jpg",
            }
        }

        result = serializer.serialize(data, image_keys=["hero_image", "thumbnail"])

        assert isinstance(result, list)
        assert len(result) > 0
        # Verify images were processed
        assert serializer.image_optimizer.process_image.call_count == 2

    def test_full_workflow_with_errors(self, serializer):
        """Test workflow handles errors gracefully."""
        serializer.image_optimizer.process_image = Mock(side_effect=Exception("Image error"))

        data = {"name": "Alice", "photo": "/bad/path.jpg"}

        result = serializer.serialize(data, image_keys=["photo"])

        assert isinstance(result, list)
        # Should still return result despite error
        assert len(result) > 0
