"""Integration tests for LlamaIndex support."""

import pytest

# Skip if llama-index not installed
pytest.importorskip("llama_index")

from toonverter.integrations.llamaindex_integration import to_toon_node, from_toon_node


class TestLlamaIndexNodes:
    """Test LlamaIndex Node handling."""

    def test_text_node_to_toon(self):
        """Test converting TextNode to TOON."""
        try:
            from llama_index.core.schema import TextNode

            node = TextNode(
                text="This is test content",
                metadata={"source": "test"},
                id_="node1"
            )

            toon = to_toon_node(node)

            assert 'test content' in toon
            assert 'test' in toon
        except ImportError:
            pytest.skip("LlamaIndex TextNode not available")

    def test_node_roundtrip(self):
        """Test Node roundtrip."""
        try:
            from llama_index.core.schema import TextNode

            node_original = TextNode(
                text="Content",
                metadata={"key": "value"},
                id_="test_node"
            )

            toon = to_toon_node(node_original)
            node_result = from_toon_node(toon)

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
                TextNode(text="Node 3", id_="3")
            ]

            toon = to_toon_node(nodes)

            assert 'Node 1' in toon and 'Node 2' in toon and 'Node 3' in toon
        except ImportError:
            pytest.skip("LlamaIndex not available")
