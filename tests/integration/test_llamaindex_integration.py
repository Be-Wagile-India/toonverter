"""Integration tests for LlamaIndex support."""

import pytest


# Skip if llama-index not installed
pytest.importorskip("llama_index")

from toonverter.integrations.llamaindex_integration import llamaindex_to_toon, toon_to_llamaindex


class TestLlamaIndexNodes:
    """Test LlamaIndex Node handling."""

    def test_text_node_to_toon(self):
        """Test converting TextNode to TOON."""
        try:
            from llama_index.core.schema import TextNode

            node = TextNode(text="This is test content", metadata={"source": "test"}, id_="node1")

            toon = llamaindex_to_toon(node)

            assert "test content" in toon
            assert "test" in toon
        except ImportError:
            pytest.skip("LlamaIndex TextNode not available")

    def test_node_roundtrip(self):
        """Test Node roundtrip."""
        try:
            from llama_index.core.schema import TextNode

            node_original = TextNode(text="Content", metadata={"key": "value"}, id_="test_node")

            toon = llamaindex_to_toon(node_original)
            node_result = toon_to_llamaindex(toon)

            assert node_result.text == "Content"
            assert node_result.metadata["key"] == "value"
        except ImportError:
            pytest.skip("LlamaIndex not available")

    def test_multiple_nodes(self):
        """Test list of Nodes."""
        try:
            from llama_index.core.schema import TextNode

            nodes = [
                TextNode(text="Node 1", id_="1"),
                TextNode(text="Node 2", id_="2"),
                TextNode(text="Node 3", id_="3"),
            ]

            toon = llamaindex_to_toon(nodes)

            assert "Node 1" in toon
            assert "Node 2" in toon
            assert "Node 3" in toon
        except ImportError:
            pytest.skip("LlamaIndex not available")
