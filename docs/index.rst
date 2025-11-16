TOON Converter Documentation
============================

.. image:: https://badge.fury.io/py/toonverter.svg
   :target: https://badge.fury.io/py/toonverter
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/toonverter.svg
   :target: https://pypi.org/project/toonverter/
   :alt: Python Support

.. image:: https://img.shields.io/badge/TOON%20Spec-v2.0%20✓-success.svg
   :target: https://github.com/toon-format/spec
   :alt: TOON Spec v2.0

.. image:: https://img.shields.io/badge/tests-50%2B%20passing-success.svg
   :target: https://github.com/Be-Wagile-India/toonverter/tree/main/tests
   :alt: Tests

.. image:: https://img.shields.io/badge/coverage-95%25%2B-success.svg
   :alt: Coverage

**Token-Optimized Object Notation (TOON) v2.0** - The most comprehensive Python library for TOON format,
featuring **100% spec compliance**, 10 framework integrations, and production-ready tools for reducing
LLM token usage by 30-60%.

Features
--------

Core Capabilities
^^^^^^^^^^^^^^^^^

* 🎯 **100% TOON v2.0 Spec Compliant**: All 26 specification tests passing
* 📉 **30-60% Token Savings**: Verified with benchmarks on real-world data
* 🔄 **Multi-Format Support**: JSON, YAML, TOML, CSV, XML ↔ TOON
* 📊 **Tabular Optimization**: Exceptional efficiency for DataFrame-like structures
* 🧮 **Token Analysis**: Compare token usage across formats using tiktoken
* 🔍 **Type Inference**: Automatic type detection and preservation
* ✅ **Strict Validation**: Optional strict mode for production safety

Framework Integrations (10)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* 🐼 **Pandas**: DataFrame ↔ TOON with tabular optimization
* 📦 **Pydantic**: BaseModel serialization with validation
* 🦜 **LangChain**: Document and Message support for RAG systems
* ⚡ **FastAPI**: Native TOON response class
* 🗄️ **SQLAlchemy**: ORM model serialization and bulk operations
* 🔌 **MCP**: Model Context Protocol server with 4 tools
* 🦙 **LlamaIndex**: Node and Document support
* 🌾 **Haystack**: Document integration for pipelines
* 🎯 **DSPy**: Example and prediction support
* 🎓 **Instructor**: Response model integration

Production Features
^^^^^^^^^^^^^^^^^^^^

* 📝 **50+ Test Files**: Comprehensive unit, integration, and performance tests
* 🎨 **Type-Safe**: 100% type hints with mypy strict mode
* ⚡ **High Performance**: <100ms for typical datasets, streaming for large files
* 🔧 **Extensible**: Plugin architecture for custom formats
* 📚 **Well-Documented**: Extensive docs and examples
* 🛡️ **Battle-Tested**: SOLID principles, clean architecture

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
   :maxdepth: 2
   :caption: API Reference

   api/facade
   api/encoder
   api/decoder
   api/converter
   api/analyzer
   api/formats
   api/integrations

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
