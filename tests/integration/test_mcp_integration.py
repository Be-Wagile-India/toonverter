"""Integration tests for MCP server."""

import pytest


# Skip if mcp not installed
pytest.importorskip("mcp")


from toonverter.integrations.mcp_server import ToonMCPServer


class TestMCPServer:
    """Test MCP server functionality."""

    @pytest.fixture
    def server(self):
        """Create test MCP server."""
        return ToonMCPServer()

    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server is not None
        assert hasattr(server, "convert")
        assert hasattr(server, "analyze")

    @pytest.mark.asyncio
    async def test_convert_tool(self, server):
        """Test convert tool."""
        data = '{"name": "Alice", "age": 30}'
        result = await server.convert(data, from_format="json", to_format="toon")

        assert isinstance(result, str)
        assert "Alice" in result
        assert "30" in result

    @pytest.mark.asyncio
    async def test_analyze_tool(self, server):
        """Test analyze tool."""
        toon = "name: Alice\nage: 30"
        result = await server.analyze(toon)

        assert "token_count" in result or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_validate_tool(self, server):
        """Test validate tool."""
        toon = "name: Alice\nage: 30"
        result = await server.validate(toon)

        assert result is True or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_compress_tool(self, server):
        """Test compress tool."""
        data = '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}'
        result = await server.compress(data)

        assert isinstance(result, str)
        # Should be smaller than original JSON
        assert len(result) < len(data)
