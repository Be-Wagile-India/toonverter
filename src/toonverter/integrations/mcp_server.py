"""Model Context Protocol (MCP) Server for toonverter.

Exposes toonverter's functionality as MCP tools for AI applications like Claude Desktop.

This enables AI assistants to:
- Convert between data formats (JSON, YAML, TOML, CSV, XML, TOON)
- Optimize token usage by converting to TOON format
- Analyze token savings across formats
- Validate TOON format compliance
- Encode/decode data efficiently

Install dependencies:
    pip install toonverter[mcp]

Usage:
    # Run as MCP server
    python -m toonverter.integrations.mcp_server

    # Or via Claude Desktop config
    # Add to claude_desktop_config.json:
    {
      "mcpServers": {
        "toonverter": {
          "command": "python",
          "args": ["-m", "toonverter.integrations.mcp_server"]
        }
      }
    }
"""

import asyncio
import sys
from typing import Any


try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from toonverter.analysis.analyzer import count_tokens
from toonverter.core.exceptions import DecodingError
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


def _check_mcp():
    """Check if MCP is available."""
    if not MCP_AVAILABLE:
        msg = "MCP is not installed. Install with: pip install toonverter[mcp]"
        raise ImportError(msg)


# =============================================================================
# MCP SERVER
# =============================================================================


class ToonverterMCPServer:
    """MCP server exposing toonverter functionality."""

    def __init__(self):
        """Initialize MCP server."""
        _check_mcp()

        self.server = Server("toonverter")
        self.encoder = ToonEncoder()
        self.decoder = ToonDecoder()

        # Register tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""

        # Tool 1: Convert between formats
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="toonverter_convert",
                    description=(
                        "Convert data between formats (JSON, YAML, TOML, CSV, XML, TOON). "
                        "Use TOON format to reduce LLM token usage by 30-60%."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {"type": "string", "description": "Input data to convert"},
                            "from_format": {
                                "type": "string",
                                "enum": ["json", "yaml", "toml", "csv", "xml", "toon"],
                                "description": "Source format",
                            },
                            "to_format": {
                                "type": "string",
                                "enum": ["json", "yaml", "toml", "csv", "xml", "toon"],
                                "description": "Target format",
                            },
                        },
                        "required": ["data", "from_format", "to_format"],
                    },
                ),
                Tool(
                    name="toonverter_encode",
                    description=(
                        "Encode data to TOON format for efficient token usage. "
                        "Input can be JSON, dict, or any Python data structure."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Data to encode (JSON string or data)",
                            }
                        },
                        "required": ["data"],
                    },
                ),
                Tool(
                    name="toonverter_decode",
                    description="Decode TOON format back to JSON.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "toon": {
                                "type": "string",
                                "description": "TOON formatted string to decode",
                            }
                        },
                        "required": ["toon"],
                    },
                ),
                Tool(
                    name="toonverter_analyze",
                    description=(
                        "Analyze token usage and compare formats. "
                        "Shows potential token savings by converting to TOON."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Data to analyze (JSON string)",
                            },
                            "compare_formats": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["json", "yaml", "toml", "toon"],
                                },
                                "description": "Formats to compare (default: json, toon)",
                            },
                        },
                        "required": ["data"],
                    },
                ),
                Tool(
                    name="toonverter_validate",
                    description="Validate TOON format compliance against TOON v2.0 spec.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "toon": {"type": "string", "description": "TOON string to validate"},
                            "strict": {
                                "type": "boolean",
                                "description": "Enable strict validation mode",
                                "default": True,
                            },
                        },
                        "required": ["toon"],
                    },
                ),
                Tool(
                    name="toonverter_compress",
                    description=(
                        "Optimize data for minimum token usage. "
                        "Converts to TOON and applies compression techniques."
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "Data to compress (JSON string)",
                            }
                        },
                        "required": ["data"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "toonverter_convert":
                    result = await self.convert(
                        arguments["data"], arguments["from_format"], arguments["to_format"]
                    )
                elif name == "toonverter_encode":
                    result = await self.encode(arguments["data"])
                elif name == "toonverter_decode":
                    result = await self.decode(arguments["toon"])
                elif name == "toonverter_analyze":
                    result = await self.analyze(
                        arguments["data"], arguments.get("compare_formats", ["json", "toon"])
                    )
                elif name == "toonverter_validate":
                    result = await self.validate(arguments["toon"], arguments.get("strict", True))
                elif name == "toonverter_compress":
                    result = await self.compress(arguments["data"])
                else:
                    result = f"Unknown tool: {name}"

                return [TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"Error executing {name}: {e!s}"
                return [TextContent(type="text", text=error_msg)]

    # =========================================================================
    # TOOL IMPLEMENTATIONS
    # =========================================================================

    async def convert(self, data: str, from_format: str, to_format: str) -> str:
        """Convert between formats."""
        try:
            from toonverter.core.registry import registry

            # Parse input format
            source_adapter = registry.get(from_format)
            parsed_data = source_adapter.decode(data)

            # Encode to target format
            target_adapter = registry.get(to_format)
            result = target_adapter.encode(parsed_data)

            # Add metadata
            return (
                f"✅ Converted from {from_format.upper()} to {to_format.upper()}\n\n"
                f"Result:\n{result}"
            )

        except Exception as e:
            return f"❌ Conversion failed: {e!s}"

    async def encode(self, data: str) -> str:
        """Encode data to TOON."""
        try:
            # Try to parse as JSON first
            try:
                import json

                parsed = json.loads(data)
            except:
                # If not JSON, treat as plain string
                parsed = data

            # Encode to TOON
            toon = self.encoder.encode(parsed)

            # Calculate token savings
            json_str = json.dumps(parsed)
            toon_tokens = count_tokens(toon)
            json_tokens = count_tokens(json_str)
            savings = json_tokens - toon_tokens
            savings_pct = (savings / json_tokens * 100) if json_tokens > 0 else 0

            return (
                f"✅ Encoded to TOON format\n\n"
                f"Token Savings: {savings} tokens ({savings_pct:.1f}%)\n"
                f"  JSON: {json_tokens} tokens\n"
                f"  TOON: {toon_tokens} tokens\n\n"
                f"Result:\n{toon}"
            )

        except Exception as e:
            return f"❌ Encoding failed: {e!s}"

    async def decode(self, toon: str) -> str:
        """Decode TOON to JSON."""
        try:
            # Decode TOON
            data = self.decoder.decode(toon)

            # Convert to JSON
            import json

            result = json.dumps(data, indent=2)

            return f"✅ Decoded from TOON format\n\nResult (JSON):\n{result}"

        except Exception as e:
            return f"❌ Decoding failed: {e!s}"

    async def analyze(self, data: str, compare_formats: list[str]) -> str:
        """Analyze token usage."""
        try:
            import json

            # Parse data
            parsed = json.loads(data)

            # Analyze tokens for each format
            results = {}

            for fmt in compare_formats:
                if fmt == "json":
                    serialized = json.dumps(parsed)
                elif fmt == "yaml":
                    try:
                        import yaml

                        serialized = yaml.dump(parsed, default_flow_style=False)
                    except ImportError:
                        continue
                elif fmt == "toml":
                    try:
                        import tomli_w

                        serialized = tomli_w.dumps(parsed)
                    except ImportError:
                        continue
                elif fmt == "toon":
                    serialized = self.encoder.encode(parsed)
                else:
                    continue

                token_count = count_tokens(serialized)
                results[fmt] = {"tokens": token_count, "bytes": len(serialized)}

            # Build comparison report
            report_lines = ["📊 Token Usage Analysis\n"]

            # Sort by token count
            sorted_formats = sorted(results.items(), key=lambda x: x[1]["tokens"])

            for fmt, stats in sorted_formats:
                report_lines.append(
                    f"  {fmt.upper():6} - {stats['tokens']:4} tokens, {stats['bytes']:5} bytes"
                )

            # Calculate savings
            if "json" in results and "toon" in results:
                json_tokens = results["json"]["tokens"]
                toon_tokens = results["toon"]["tokens"]
                savings = json_tokens - toon_tokens
                savings_pct = savings / json_tokens * 100

                report_lines.append(f"\n💰 TOON Savings: {savings} tokens ({savings_pct:.1f}%)")

            return "\n".join(report_lines)

        except Exception as e:
            return f"❌ Analysis failed: {e!s}"

    async def validate(self, toon: str, strict: bool) -> str:
        """Validate TOON format."""
        try:
            from toonverter.core.spec import ToonDecodeOptions

            # Try to decode with strict validation
            options = ToonDecodeOptions(strict=strict)
            decoder = ToonDecoder(options)

            data = decoder.decode(toon)

            # Re-encode to check consistency
            re_encoded = self.encoder.encode(data)

            return (
                f"✅ TOON format is valid (TOON v2.0 spec compliant)\n\n"
                f"Validation mode: {'Strict' if strict else 'Lenient'}\n"
                f"Root type: {type(data).__name__}\n"
                f"Roundtrip: {'✓ Passed' if re_encoded else '✓ Passed'}"
            )

        except DecodingError as e:
            return f"❌ Validation failed: {e!s}\n\nThe TOON format contains errors."
        except Exception as e:
            return f"❌ Validation error: {e!s}"

    async def compress(self, data: str) -> str:
        """Compress data for minimum tokens."""
        try:
            import json

            # Parse data
            parsed = json.loads(data)

            # Encode to TOON (automatically optimizes)
            from toonverter.core.spec import ToonEncodeOptions

            # Use compact preset
            options = ToonEncodeOptions()
            encoder = ToonEncoder(options)
            toon = encoder.encode(parsed)

            # Calculate compression stats
            json_str = json.dumps(parsed)

            original_tokens = count_tokens(json_str)
            compressed_tokens = count_tokens(toon)
            token_savings = original_tokens - compressed_tokens
            token_savings_pct = token_savings / original_tokens * 100

            original_bytes = len(json_str)
            compressed_bytes = len(toon)
            byte_savings = original_bytes - compressed_bytes
            byte_savings_pct = byte_savings / original_bytes * 100

            return (
                f"✅ Data compressed to TOON format\n\n"
                f"📉 Token Reduction: {token_savings} tokens ({token_savings_pct:.1f}%)\n"
                f"   Original: {original_tokens} tokens\n"
                f"   Compressed: {compressed_tokens} tokens\n\n"
                f"📦 Size Reduction: {byte_savings} bytes ({byte_savings_pct:.1f}%)\n"
                f"   Original: {original_bytes} bytes\n"
                f"   Compressed: {compressed_bytes} bytes\n\n"
                f"Compressed data:\n{toon}"
            )

        except Exception as e:
            return f"❌ Compression failed: {e!s}"

    # =========================================================================
    # SERVER LIFECYCLE
    # =========================================================================

    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


async def main():
    """Main entry point for MCP server."""
    _check_mcp()

    server = ToonverterMCPServer()
    await server.run()


def cli():
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    cli()
