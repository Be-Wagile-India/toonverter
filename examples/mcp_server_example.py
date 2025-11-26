"""MCP Server Example and Documentation.

This example shows how to set up and use the toonverter MCP server
with Claude Desktop and other MCP clients.

Install dependencies:
    pip install toonverter[mcp]
"""

# =============================================================================
# SETUP INSTRUCTIONS
# =============================================================================

SETUP_INSTRUCTIONS = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                   TOONVERTER MCP SERVER SETUP                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

## What is MCP?

Model Context Protocol (MCP) is an open protocol from Anthropic that enables
AI applications like Claude Desktop to connect to external tools and data sources.

Toonverter's MCP server exposes format conversion and token optimization tools
that Claude can use to help you work more efficiently with data.

## Installation

1. Install toonverter with MCP support:

   pip install toonverter[mcp]

2. Find your Claude Desktop config file:

   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json
   - Linux: ~/.config/Claude/claude_desktop_config.json

3. Add toonverter to your config:

   {
     "mcpServers": {
       "toonverter": {
         "command": "python",
         "args": ["-m", "toonverter.integrations.mcp_server"]
       }
     }
   }

4. Restart Claude Desktop

5. Verify installation:
   - Click the 🔌 icon in Claude Desktop
   - You should see "toonverter" listed
   - You should see 6 tools available

## Available Tools

Toonverter provides 6 MCP tools:

1. **toonverter_convert**
   - Convert between formats (JSON, YAML, TOML, CSV, XML, TOON)
   - Example: "Convert this JSON to TOON format: {...}"

2. **toonverter_encode**
   - Encode data to TOON for token optimization
   - Example: "Encode this data to TOON: {...}"

3. **toonverter_decode**
   - Decode TOON back to JSON
   - Example: "Decode this TOON data: name: Alice\\nage: 30"

4. **toonverter_analyze**
   - Analyze token usage across formats
   - Example: "Compare token usage for this data in JSON vs TOON"

5. **toonverter_validate**
   - Validate TOON format compliance
   - Example: "Validate this TOON format: [3]: 1,2,3"

6. **toonverter_compress**
   - Optimize data for minimum token usage
   - Example: "Compress this JSON for minimum tokens: {...}"

## Usage Examples

### Example 1: Basic Conversion

User: "I have this JSON data. Can you convert it to TOON format to save tokens?"

{
  "users": [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
  ]
}

Claude will use: toonverter_convert
Result: TOON format with 40-50% token savings

---

### Example 2: Token Analysis

User: "How many tokens will this data use in different formats?"

{"name": "Alice", "age": 30, "email": "alice@example.com"}

Claude will use: toonverter_analyze
Result: Comparison showing token counts for JSON, YAML, TOON

---

### Example 3: Optimize API Response

User: "I need to send this database result to an LLM. Optimize it for minimum tokens."

[
  {"id": 1, "name": "Product A", "price": 99.99},
  {"id": 2, "name": "Product B", "price": 149.99},
  ...
]

Claude will use: toonverter_compress
Result: TOON format with compression stats and token savings

---

### Example 4: Validate Format

User: "Is this valid TOON format?"

users[2]{name,age}:
  Alice,30
  Bob,25

Claude will use: toonverter_validate
Result: Validation report with spec compliance check

## Benefits

✅ **40-60% token savings** - Reduce LLM API costs
✅ **Format flexibility** - Convert between 6+ formats
✅ **Built into Claude** - No copy-paste needed
✅ **Automatic optimization** - Claude chooses best tool
✅ **Spec compliant** - Follows TOON v2.0 specification

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check config file path is correct
2. Verify JSON syntax is valid
3. Ensure Python is in PATH
4. Check MCP is installed: `pip show mcp`
5. Restart Claude Desktop

### Tool calls failing

1. Check toonverter is installed: `pip show toonverter`
2. Try running server manually: `python -m toonverter.integrations.mcp_server`
3. Check error logs in Claude Desktop

### Permission errors

1. Ensure Python has execute permissions
2. Try using full path to Python: `"command": "/usr/bin/python3"`

## Advanced Configuration

### Custom Python Environment

{
  "mcpServers": {
    "toonverter": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "toonverter.integrations.mcp_server"],
      "env": {
        "PYTHONPATH": "/custom/path"
      }
    }
  }
}

### Multiple Instances

You can run multiple toonverter servers with different configs:

{
  "mcpServers": {
    "toonverter-strict": {
      "command": "python",
      "args": ["-m", "toonverter.integrations.mcp_server"],
      "env": {"TOON_STRICT_MODE": "true"}
    },
    "toonverter-lenient": {
      "command": "python",
      "args": ["-m", "toonverter.integrations.mcp_server"],
      "env": {"TOON_STRICT_MODE": "false"}
    }
  }
}

## Learn More

- TOON Specification: https://github.com/toon-format/spec
- MCP Documentation: https://modelcontextprotocol.io
- Toonverter GitHub: [your-repo-url]
- Report Issues: [your-issues-url]
"""


# =============================================================================
# USAGE DEMONSTRATIONS
# =============================================================================


def print_setup_guide():
    """Print setup instructions."""
    print(SETUP_INSTRUCTIONS)


def example_prompts():
    """Example prompts for Claude Desktop."""
    examples = {
        "Basic Conversion": [
            'Convert this JSON to TOON format: {"name": "Alice", "age": 30}',
            "Convert this YAML to JSON: name: Bob\\nage: 25",
            "Transform this CSV to TOON: name,age\\nAlice,30\\nBob,25",
        ],
        "Token Optimization": [
            "Compress this data for minimum tokens: {large_json_data}",
            "How much can I save by using TOON instead of JSON for this?",
            "Optimize this API response for LLM context: [...]",
        ],
        "Format Analysis": [
            "Compare token usage for this data in JSON, YAML, and TOON",
            "Which format uses fewer tokens for database results?",
            "Analyze the token efficiency of this data structure",
        ],
        "Validation": [
            "Is this valid TOON format? [3]: 1,2,3",
            "Validate this TOON data against the v2.0 spec",
            "Check if this TOON is properly formatted",
        ],
        "Complex Workflows": [
            "Take this JSON, convert to TOON, analyze savings, then validate",
            "Compare all supported formats and recommend the most efficient",
            "Convert this database export to the most token-efficient format",
        ],
    }

    print("\n" + "=" * 80)
    print(" EXAMPLE PROMPTS FOR CLAUDE DESKTOP")
    print("=" * 80 + "\n")

    for category, prompts in examples.items():
        print(f"### {category}\n")
        for i, prompt in enumerate(prompts, 1):
            print(f'{i}. "{prompt}"')
        print()


# =============================================================================
# TESTING THE SERVER
# =============================================================================


async def test_mcp_server():
    """Test the MCP server locally."""
    import json
    from toonverter.integrations.mcp_server import ToonverterMCPServer

    print("\n" + "=" * 80)
    print(" TESTING TOONVERTER MCP SERVER")
    print("=" * 80 + "\n")

    server = ToonverterMCPServer()

    # Test 1: Encode
    print("Test 1: Encode to TOON")
    print("-" * 40)
    test_data = json.dumps({"name": "Alice", "age": 30, "active": True})
    result = await server._encode(test_data)
    print(result)
    print()

    # Test 2: Analyze
    print("Test 2: Analyze Token Usage")
    print("-" * 40)
    result = await server._analyze(test_data, ["json", "toon"])
    print(result)
    print()

    # Test 3: Validate
    print("Test 3: Validate TOON Format")
    print("-" * 40)
    toon_data = "name: Alice\nage: 30\nactive: true"
    result = await server._validate(toon_data, strict=True)
    print(result)
    print()

    # Test 4: Compress
    print("Test 4: Compress Data")
    print("-" * 40)
    large_data = json.dumps(
        {
            "users": [
                {"name": f"User{i}", "email": f"user{i}@example.com", "age": 20 + i}
                for i in range(5)
            ]
        }
    )
    result = await server._compress(large_data)
    print(result)
    print()

    print("=" * 80)
    print("✅ All tests completed successfully!")
    print("=" * 80 + "\n")


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main function."""
    import asyncio

    # Print setup guide
    print_setup_guide()

    # Show example prompts
    example_prompts()

    # Run tests
    print("\n" + "=" * 80)
    print(" Running server tests...")
    print("=" * 80 + "\n")

    try:
        asyncio.run(test_mcp_server())
    except ImportError as e:
        print(f"⚠️  Cannot run tests: {e}")
        print("Install MCP: pip install toonverter[mcp]")


if __name__ == "__main__":
    main()
