# TOON Converter

<p align="left">
  <img src="docs/TDMC.png" alt="LOGO" width="200"/>
</p>

[![PyPI version](https://badge.fury.io/py/toonverter.svg)](https://badge.fury.io/py/toonverter)
[![Downloads](https://img.shields.io/pypi/dm/toonverter)](https://pypi.org/project/toonverter/)
[![Python Support](https://img.shields.io/pypi/pyversions/toonverter.svg)](https://pypi.org/project/toonverter/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![TOON Spec v2.0](https://img.shields.io/badge/TOON%20Spec-v2.0%20✓-success.svg)](https://github.com/toon-format/spec)
[![Tests](https://img.shields.io/badge/tests-563%20passing-success.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-81.03%25-brightgreen.svg)](htmlcov/index.html)

**Token-Optimized Object Notation (TOON) v2.0** - The most comprehensive Python library for TOON format, featuring **100% spec compliance**, 10 framework integrations, and production-ready tools for reducing LLM token usage by 30-60%.

## 💡 Why Use TOON Converter?

### Real Benefits for Your LLM Applications

| Benefit                | Impact | Example |
|------------------------|--------|---------|
| ** Faster Processing** | Smaller payloads = faster responses | 200ms → 80ms average latency |
| ** Better Context**    | More data in same token limit | Fit 10 docs instead of 6 in context |
| ** Works Everywhere**  | 10 framework integrations | LangChain, Pandas, FastAPI, SQLAlchemy, MCP |
| ** Easy to Use**       | 2 lines of code to get started | `import toonverter as toon; toon.encode(data)` |
| ** Production Ready**  | Battle-tested, type-safe | 563 tests, 81% coverage |
| ** Smart Optimization** | Auto-detects tabular data | Arrays → compact table format |
| ** Format Flexibility** | Convert between 6 formats | JSON, YAML, TOML, CSV, XML, TOON |
| ** Built-in Analytics** | Compare formats instantly | See token savings before you commit |
| ** Zero Config**       | Works out of the box | No setup, no config files needed |

## 🚀 Key Features

### Core Capabilities
- **100% TOON v2.0 Spec Compliant**: All 26 specification tests passing
- **30-60% Token Savings**: Verified with benchmarks on real-world data
- **Multi-Format Support**: JSON, YAML, TOML, CSV, XML ↔ TOON
- **Vision Optimization**: Reduce image token costs for multimodal models
- **Semantic Deduplication**: Remove semantically identical content using embeddings
- **Tabular Optimization**: Exceptional efficiency for DataFrame-like structures
- **Token Analysis**: Compare token usage across formats using tiktoken
- **Type Inference**: Automatic type detection and preservation
- **Strict Validation**: Optional strict mode for production safety

### Framework Integrations (10)
- **Pandas**: DataFrame ↔ TOON with tabular optimization
- **Pydantic**: BaseModel serialization with validation
- **LangChain**: Document and Message support for RAG systems
- **FastAPI**: Native TOON response class
- **🗄SQLAlchemy**: ORM model serialization and bulk operations
- **MCP**: Model Context Protocol server with 4 tools
- **LlamaIndex**: Node and Document support
- **Haystack**: Document integration for pipelines
- **DSPy**: Example and prediction support
- **Instructor**: Response model integration


## Installation

### Basic Installation

```bash
pip install toonverter
```

Includes TOON encoding/decoding, JSON/YAML/TOML/CSV/XML support, and token analysis.

### Individual Framework Integrations

```bash
# Data science
pip install toonverter[pandas]      # DataFrame support
pip install toonverter[sqlalchemy]  # ORM serialization

# AI/LLM frameworks
pip install toonverter[langchain]   # Document/Message support
pip install toonverter[llamaindex]  # Node support
pip install toonverter[haystack]    # Pipeline integration
pip install toonverter[dspy]        # Example support
pip install toonverter[instructor]  # Response models

# Web frameworks
pip install toonverter[fastapi]     # TOONResponse class
pip install toonverter[pydantic]    # BaseModel serialization

# Model Context Protocol
pip install toonverter[mcp]         # MCP server with 4 tools
```

### Grouped Integrations

```bash
pip install toonverter[ai]    # LlamaIndex, Haystack, DSPy, Instructor
pip install toonverter[data]  # Pandas, SQLAlchemy
pip install toonverter[web]   # FastAPI, Pydantic
pip install toonverter[llm]   # LangChain, MCP
```

### CLI Tools

```bash
pip install toonverter[cli]  # Command-line interface with rich output
```

### Complete Installation

```bash
pip install toonverter[all]  # All integrations + CLI
```

### Development Installation

```bash
git clone https://github.com/yourusername/toonverter.git
cd toonverter
pip install -e ".[all]"
make install-dev  # Install dev dependencies
```

## Quick Start

### Simple Facade API (90% of users)

```python
import toonverter as toon

# Convert JSON to TOON
data = {"name": "Alice", "age": 30, "city": "NYC"}
toon_str = toon.encode(data)
print(toon_str)
# Output: {name:Alice,age:30,city:NYC}

# Convert TOON back to Python dict
decoded = toon.decode(toon_str)
print(decoded)
# Output: {'name': 'Alice', 'age': 30, 'city': 'NYC'}

# Convert between formats
toon.convert(source='data.json', target='data.toon', from_format='json', to_format='toon')

# Analyze token usage
report = toon.analyze(data, compare_formats=['json', 'toon'])
print(f"Best format: {report.best_format}")
print(f"Token savings: {report.max_savings_percentage:.1f}%")
# Output: Best format: toon, Token savings: 33.3%

# Load and save files
data = toon.load('config.json', format='json')
toon.save(data, 'config.toon', format='toon')

# Check supported formats
print(toon.list_formats())
# Output: ['csv', 'json', 'toml', 'toon', 'xml']
```

### Object-Oriented API (Power Users)

```python
from toonverter import Converter, Encoder, Decoder, Analyzer

# Stateful converter with custom options
converter = Converter(
    from_format='json',
    to_format='toon',
    compact=True,
    sort_keys=True
)
result = converter.convert_file('data.json', 'data.toon')

# Custom encoder configuration
encoder = Encoder(
    format='toon',
    delimiter=',',
    compact=True
)
encoded = encoder.encode(data)

# Token analyzer with specific model
analyzer = Analyzer(model='gpt-4')
report = analyzer.analyze_multi_format(data, formats=['json', 'toon'])
print(report.max_savings_percentage)
```

### Advanced Capabilities

#### Vision Optimization
Reduce image token costs for multimodal models (GPT-4o, Claude 3.5).

```python
from toonverter import optimize_vision

# Optimize image (resize, format, quality) for provider
img_bytes, mime = optimize_vision(
    raw_image_bytes, 
    provider="openai"  # or 'anthropic'
)
```

#### Semantic Deduplication
Remove semantically identical items from lists using embeddings.

```python
from toonverter import deduplicate

# Remove duplicates based on meaning (threshold 0.0-1.0)
clean_data = deduplicate(data, threshold=0.9)
```

#### Schema Tools
Infer structure from data and validate new instances.

```python
from toonverter import infer_schema, validate_schema

# Learn schema from existing data
schema = infer_schema(data)

# Validate new data against schema
errors = validate_schema(new_data, schema)
if not errors:
    print("Valid!")
```

#### Structural Diff
Compare complex objects to find semantic differences.

```python
from toonverter import diff

# Get structural differences
result = diff(old_ver, new_ver)
print(f"Found {len(result.changes)} changes")
```

#### Smart Compression
Apply Smart Dictionary Compression (SDC) for maximum efficiency.

```python
from toonverter import compress, decompress

# Compress large dataset
compressed = compress(large_data)

# Restore original
original = decompress(compressed)
```

### Integration Examples

#### Pandas DataFrame

```python
import pandas as pd
from toonverter.integrations import pandas_to_toon, toon_to_pandas

# Convert DataFrame to TOON (optimized for tabular data)
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [30, 25, 35],
    'city': ['NYC', 'LA', 'SF']
})

toon_str = pandas_to_toon(df)
print(toon_str)
# Output:
# name,age,city
# Alice,30,NYC
# Bob,25,LA
# Charlie,35,SF

# Convert back to DataFrame
restored_df = toon_to_pandas(toon_str)
```

#### Pydantic Models

```python
from pydantic import BaseModel
from toonverter.integrations import pydantic_to_toon, toon_to_pydantic

class User(BaseModel):
    name: str
    age: int
    email: str

user = User(name="Alice", age=30, email="alice@example.com")

# Serialize to TOON
toon_str = pydantic_to_toon(user)

# Deserialize from TOON
restored_user = toon_to_pydantic(toon_str, User)
```

#### LangChain RAG

```python
from langchain_core.documents import Document
from toonverter.integrations import langchain_to_toon, toon_to_langchain

# Convert LangChain documents to TOON for efficient storage
doc = Document(
    page_content="Important information...",
    metadata={"source": "doc1.pdf", "page": 1}
)

toon_str = langchain_to_toon(doc)
# Use in vector database with 30-60% token savings

# Restore document
restored_doc = toon_to_langchain(toon_str)
```

#### FastAPI

```python
from fastapi import FastAPI
from toonverter.integrations import TOONResponse

app = FastAPI()

@app.get("/data", response_class=TOONResponse)
async def get_data():
    return {"users": [...], "count": 100}
    # Automatically serialized as TOON with proper content-type
```

#### SQLAlchemy ORM

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from toonverter.integrations import sqlalchemy_to_toon, toon_to_sqlalchemy

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]

# Serialize ORM instances
product = Product(id=1, name="Widget", price=29.99)
toon_str = sqlalchemy_to_toon(product)

# Bulk operations with query results
products = session.query(Product).all()
toon_str = sqlalchemy_to_toon(products)  # Optimized tabular format
```

#### LlamaIndex RAG

```python
from llama_index.core.schema import Document, TextNode
from toonverter.integrations import llamaindex_to_toon, toon_to_llamaindex

# Convert LlamaIndex nodes for efficient storage
node = TextNode(
    text="Important context...",
    metadata={"source": "doc.pdf"}
)

toon_str = llamaindex_to_toon(node)
restored_node = toon_to_llamaindex(toon_str)
```

#### Haystack Pipelines

```python
from haystack.dataclasses import Document
from toonverter.integrations import haystack_to_toon, toon_to_haystack

# Optimize Haystack documents
doc = Document(
    content="Search content...",
    meta={"title": "Article", "date": "2025-01-15"}
)

toon_str = haystack_to_toon(doc)
restored_doc = toon_to_haystack(toon_str)
```

#### DSPy Examples

```python
from dspy import Example
from toonverter.integrations import dspy_to_toon, toon_to_dspy

# Serialize DSPy training examples
example = Example(
    question="What is TOON?",
    answer="A token-optimized format"
).with_inputs("question")

toon_str = dspy_to_toon(example)
restored = toon_to_dspy(toon_str)
```

#### Instructor Responses

```python
from pydantic import BaseModel
from toonverter.integrations import to_toon_response, from_toon_response

class UserResponse(BaseModel):
    name: str
    age: int
    email: str

# Convert Instructor-structured responses
response = UserResponse(name="Alice", age=30, email="alice@example.com")
toon_str = to_toon_response(response)
```

#### Model Context Protocol (MCP)

```python
# Use as MCP server for Claude Desktop or other MCP clients
# Add to claude_desktop_config.json:
{
  "mcpServers": {
    "toonverter": {
      "command": "python",
      "args": ["-m", "toonverter.integrations.mcp_server"]
    }
  }
}

# Available MCP tools:
# - convert: Convert between formats
# - analyze: Analyze token usage
# - validate: Validate TOON syntax
# - compress: Find most efficient format
```

### CLI Usage

```bash
# Convert files
toonverter convert data.json data.toon --from json --to toon

# Encode to TOON
toonverter encode data.json --output data.toon

# Decode from TOON
toonverter decode data.toon --output data.json --format json

# Analyze token usage
toonverter analyze data.json --compare json toon

# List supported formats
toonverter formats
```

## TOON Format Specification v2.0

TOON (Token-Optimized Object Notation) is designed for maximum token efficiency while maintaining readability.

### Three Root Forms

```toon
# 1. Object (default) - key-value pairs
name: Alice
age: 30
city: NYC

# 2. Array - collection of items
users[3]:
  - Alice
  - Bob
  - Charlie

# 3. Primitive - single value
Hello World
```

### Three Array Forms

```toon
# 1. Inline Array - primitives on one line
tags[3]: python,llm,optimization

# 2. Tabular Array - uniform objects with primitives only
users[3]{name,age,city}:
  Alice,30,NYC
  Bob,25,LA
  Charlie,35,SF

# 3. List Array - complex/mixed structures
items[2]:
  - name: Item1
    price: 19.99
    tags[2]: sale,new
  - name: Item2
    price: 29.99
    nested:
      key: value
```

### String Quoting Rules

Strings need quotes if they:
- Are empty or whitespace-only
- Start/end with whitespace
- Match reserved words (`true`, `false`, `null`)
- Look numeric (`123`, `3.14`, `-42`)
- Contain special chars (`:[]{}|,`)
- Start with hyphen (`-test`)
- Contain the delimiter

```toon
# Quoted strings
name: "true"           # Reserved word
id: "123"              # Looks numeric
path: "test:value"     # Contains colon
text: "  spaced  "     # Has whitespace
empty: ""              # Empty string

# Unquoted strings
simple: hello
snake_case: user_name
kebab-case: test-value
```

### Number Canonical Form

```toon
# Valid numbers
count: 42
price: 19.99
negative: -3.14
zero: 0

# Normalized (not allowed in strict mode)
# 1.0 → 1
# 1e5 → 100000
# -0 → 0
# NaN → null
# Infinity → null
```

### Delimiters

```toon
# Comma (default, no marker)
a: 1,b: 2,c: 3

# Tab (marked with {TAB})
{TAB}
a: 1\tb: 2\tc: 3

# Pipe (marked with {PIPE})
{PIPE}
a: 1|b: 2|c: 3
```

### Escape Sequences

Only 5 escape sequences are allowed:
- `\\` - Backslash
- `\"` - Double quote
- `\n` - Newline
- `\r` - Carriage return
- `\t` - Tab

### Token Savings Examples

| Format | Tokens | Savings |
|--------|--------|---------|
| JSON   | 24     | 0%      |
| YAML   | 20     | 16%     |
| TOON   | 16     | 33%     |

*Actual savings vary by data structure. Tabular data sees 40-60% savings.*

For full specification details, see [TOON v2.0 Spec](https://github.com/toon-format/spec).

## Advanced Features

### Custom Format Adapters

```python
from toonverter.core.interfaces import FormatAdapter
from toonverter.core.registry import registry

class CustomAdapter(FormatAdapter):
    def encode(self, data, options):
        # Custom encoding logic
        pass

    def decode(self, data_str, options):
        # Custom decoding logic
        pass

# Register adapter
registry.register('custom', CustomAdapter())

# Use it
import toonverter as toon
toon.convert(source='data.custom', target='data.toon', from_format='custom', to_format='toon')
```

### Plugin Development

```python
# my_plugin.py
from toonverter.plugins import Plugin

class MyFormatPlugin(Plugin):
    name = "myformat"
    version = "1.0.0"

    def register(self, registry):
        registry.register('myformat', MyFormatAdapter())

# setup.py entry point
entry_points={
    'toonverter.plugins': [
        'myformat = my_plugin:MyFormatPlugin',
    ]
}
```


## Use Cases

- **RAG Systems**: Reduce vector database storage and improve retrieval
- **LLM Prompts**: Minimize token usage in context windows
- **API Responses**: Efficient data transfer with FastAPI integration
- **Data Pipelines**: Convert between formats in ETL workflows
- **Configuration Files**: Token-efficient config serialization
- **LangChain Applications**: Optimize document storage and retrieval

## Requirements

- Python 3.10+
- Core: `typing-extensions>=4.8.0`, `tiktoken>=0.5.0`, `PyYAML>=6.0`, `tomli>=2.0.0` (Python <3.11)
- Optional integrations: `pandas`, `pydantic`, `langchain`, `fastapi`, `sqlalchemy`, `mcp`, `llama-index`, `haystack-ai`, `dspy-ai`, `instructor`
- Optional CLI: `click`, `rich`

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

Key areas for contribution:
- Additional format adapters
- Performance optimizations
- Documentation improvements
- Bug fixes and features
- Integration examples

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for efficient data serialization in LLM applications
- Built with modern Python packaging standards (PEP 517/518)
- Follows SOLID principles and clean architecture
- Designed for the LLM and AI community


## Quick Links

- **Install**: `pip install toonverter`
- **Import**: `import toonverter as toon`
- **CLI**: `toonverter --help`
- **Test**: `python3 -m pytest tests/`
- **Examples**: See `examples/` directory

---
**Package Name**: `toonverter` | **CLI Command**: `toonverter` | **Import**: `import toonverter`

TheDataMigrationCompany@2025
BWI@2025


