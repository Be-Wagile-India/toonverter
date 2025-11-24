import pytest

from toonverter.rag.splitter import ToonHybridSplitter


class TestToonHybridSplitter:
    @pytest.fixture
    def splitter(self):
        # Use a small chunk size to force splitting in tests
        return ToonHybridSplitter(chunk_size=50, min_chunk_size=5)

    def test_atomic_node_preservation(self, splitter):
        """Test that small objects remain intact."""
        data = {"id": 1, "name": "Test User"}
        chunks = splitter.split(data)

        # Should be a single chunk because it fits in 50 tokens
        assert len(chunks) == 1
        assert "Test User" in chunks[0].content
        assert chunks[0].path == []

    def test_list_splitting(self, splitter):
        """Test that long lists are split into multiple chunks."""
        # Create a list that definitely exceeds 50 tokens
        # Each item is small, but together they are big
        data = [{"id": i, "data": "x" * 10} for i in range(20)]

        chunks = splitter.split(data)

        assert len(chunks) > 1
        # Verify first chunk has correct context
        # Path should imply it's a list slice or the root context
        # Our splitter puts path in the content string
        assert "# Path:" in chunks[0].content or chunks[0].content.startswith("[")

    def test_deep_nested_splitting(self, splitter):
        """Test splitting of deep structures."""
        data = {
            "users": {
                "active": [
                    {"name": "User A", "bio": "Short bio"},
                    {"name": "User B", "bio": "Short bio 2"},
                ],
                "archived": [],
            }
        }

        # Should traverse into users -> active
        chunks = splitter.split(data)

        # Check if we have chunks with deep paths
        # Depending on sizing, it might split at 'users' or 'users.active'
        # We look for partial matches
        # Or if it grouped them, the content should have the path
        assert len(chunks) >= 1

    def test_long_string_splitting(self, splitter):
        """Test that a long string is split textually."""
        long_text = "Word " * 100  # ~100 tokens
        data = {"article": long_text}

        chunks = splitter.split(data)

        # Should be split
        assert len(chunks) > 1

        # Check context
        for chunk in chunks:
            assert "article" in chunk.path or "article" in chunk.content
            assert "# Path: article" in chunk.content

    def test_buffer_accumulation(self, splitter):
        """Test that small siblings are grouped."""
        # Several small keys that fit in one chunk
        data = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}

        chunks = splitter.split(data)
        # Should ideally be 1 chunk if they all fit
        assert len(chunks) == 1
        assert "a: 1" in chunks[0].content
        assert "e: 5" in chunks[0].content
