TOON Converter Documentation
============================

.. image:: https://badge.fury.io/py/toonverter.svg
   :target: https://badge.fury.io/py/toonverter
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/dm/toonverter
   :target: https://pypi.org/project/toonverter/
   :alt: Downloads

.. image:: https://img.shields.io/pypi/pyversions/toonverter.svg
   :target: https://pypi.org/project/toonverter/
   :alt: Python Support

.. image:: https://img.shields.io/badge/TOON%20Spec-v2.0%20✓-success.svg
   :target: https://github.com/toon-format/spec
   :alt: TOON Spec v2.0

.. image:: https://img.shields.io/badge/tests-563%20passing-success.svg
   :target: https://github.com/Be-Wagile-India/toonverter/tree/main/tests
   :alt: Tests

.. image:: https://img.shields.io/badge/coverage-81.03%25-brightgreen.svg
   :target: htmlcov/index.html
   :alt: Coverage

**Token-Optimized Object Notation (TOON) v2.0** - The most comprehensive Python library for TOON format,
featuring **100% spec compliance**, 10 framework integrations, and production-ready tools for reducing
LLM token usage by 30-60%.

Why Use TOON Converter?
------------------------

Real Benefits for Your LLM Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Save Money**
   30-60% token reduction = $1000/mo → $400/mo on API costs

**Faster Processing**
   Smaller payloads = faster responses (200ms → 80ms average latency)

**Better Context**
   More data in same token limit (Fit 10 docs instead of 6 in context)

**Works Everywhere**
   10 framework integrations: LangChain, Pandas, FastAPI, SQLAlchemy, MCP

**Easy to Use**
   2 lines of code to get started: ``import toonverter as toon; toon.encode(data)``

**Production Ready**
   Battle-tested, type-safe (563 tests, 81% coverage)

**Smart Optimization**
   Auto-detects tabular data and uses compact table format

**Format Flexibility**
   Convert between 6 formats: JSON, YAML, TOML, CSV, XML, TOON

**Built-in Analytics**
   Compare formats instantly - see token savings before you commit

**Zero Config**
   Works out of the box - no setup, no config files needed

Features
--------

Core Capabilities
^^^^^^^^^^^^^^^^^

* **100% TOON v2.0 Spec Compliant**: All 26 specification tests passing
* **30-60% Token Savings**: Verified with benchmarks on real-world data
* **Multi-Format Support**: JSON, YAML, TOML, CSV, XML ↔ TOON
* **Tabular Optimization**: Exceptional efficiency for DataFrame-like structures
* **Token Analysis**: Compare token usage across formats using tiktoken
* **Type Inference**: Automatic type detection and preservation
* **Strict Validation**: Optional strict mode for production safety

Framework Integrations (10)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **Pandas**: DataFrame ↔ TOON with tabular optimization
* **Pydantic**: BaseModel serialization with validation
* **LangChain**: Document and Message support for RAG systems
* **FastAPI**: Native TOON response class
* **SQLAlchemy**: ORM model serialization and bulk operations
* **MCP**: Model Context Protocol server with 4 tools
* **LlamaIndex**: Node and Document support
* **Haystack**: Document integration for pipelines
* **DSPy**: Example and prediction support
* **Instructor**: Response model integration


Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   pip install toonverter

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   # Encode Python dict to TOON
   data = {"name": "Alice", "age": 30, "city": "NYC"}
   toon_str = toon.encode(data)
   print(toon_str)
   # Output: name: Alice
   #         age: 30
   #         city: NYC

   # Decode TOON back to Python dict
   decoded = toon.decode(toon_str)
   print(decoded)
   # Output: {'name': 'Alice', 'age': 30, 'city': 'NYC'}

   # Analyze token usage
   report = toon.analyze(data, compare_formats=['json', 'toon'])
   print(f"Token savings: {report.max_savings_percentage:.1f}%")
   # Output: Token savings: 33.3%

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guides/getting_started
   guides/installation
   guides/quick_start
   guides/toon_format
   guides/configuration

.. toctree::
   :maxdepth: 2
   :caption: Integration Guides

   guides/integrations/pandas
   guides/integrations/pydantic
   guides/integrations/langchain
   guides/integrations/fastapi
   guides/integrations/sqlalchemy
   guides/integrations/mcp
   guides/integrations/llamaindex
   guides/integrations/haystack
   guides/integrations/dspy
   guides/integrations/instructor

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_usage
   examples/tabular_data
   examples/nested_structures
   examples/token_analysis
   examples/cli_usage
   examples/custom_adapters

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/facade
   api/encoder
   api/decoder
   api/converter
   api/analyzer
   api/formats
   api/integrations
   api/async_api
   api/async_io
   api/streaming
   api/diff
   api/analysis_token_counter
   api/rag_chunking_api
   api/schema_helpers

.. toctree::
   :maxdepth: 2
   :caption: Context Converter

   api/context_helpers
   api/message
   api/context_formatter

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/architecture
   development/testing
   development/changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
