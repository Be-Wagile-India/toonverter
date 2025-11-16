Getting Started
===============

Welcome to TOON Converter! This guide will help you get up and running with the library.

What is TOON?
-------------

TOON (Token-Optimized Object Notation) is a data serialization format designed specifically to reduce
token usage in Large Language Model (LLM) applications. It achieves 30-60% token savings compared to
JSON while maintaining readability and type safety.

Why Use TOON Converter?
------------------------

100% Spec Compliance
^^^^^^^^^^^^^^^^^^^^

TOON Converter is the only Python library with **100% TOON v2.0 specification compliance**. All 26
official specification tests pass, ensuring correct behavior across all edge cases.

.. code-block:: text

   ✅ All three root forms (Object, Array, Primitive)
   ✅ All three array forms (Inline, Tabular, List)
   ✅ Number canonical form (no exponents, no trailing zeros)
   ✅ String quoting rules (10+ edge cases)
   ✅ All delimiters (Comma, Tab, Pipe)
   ✅ Escape sequences (5 types)

Comprehensive Integrations
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Built-in support for 10 popular frameworks:

* **Data Science**: Pandas, SQLAlchemy
* **AI/LLM**: LangChain, LlamaIndex, Haystack, DSPy, Instructor
* **Web**: FastAPI, Pydantic
* **Protocols**: Model Context Protocol (MCP)

Production Ready
^^^^^^^^^^^^^^^^

* 50+ test files with 95%+ coverage
* 100% type hints with mypy strict mode
* High performance (<100ms for typical datasets)
* Comprehensive documentation and examples

Token Savings Examples
----------------------

Simple Object
^^^^^^^^^^^^^

.. code-block:: python

   data = {"name": "Alice", "age": 30, "city": "NYC"}

   # JSON: 42 characters
   # {"name":"Alice","age":30,"city":"NYC"}

   # TOON: 28 characters (33% savings)
   # name: Alice
   # age: 30
   # city: NYC

Tabular Data
^^^^^^^^^^^^

.. code-block:: python

   data = {
       "users": [
           {"name": "Alice", "age": 30},
           {"name": "Bob", "age": 25},
           {"name": "Charlie", "age": 35}
       ]
   }

   # JSON: ~120 characters
   # TOON: ~60 characters (50% savings)
   # users[3]{name,age}:
   #   Alice,30
   #   Bob,25
   #   Charlie,35

Use Cases
---------

RAG Systems
^^^^^^^^^^^

Reduce vector database storage and improve retrieval efficiency:

.. code-block:: python

   from langchain.schema import Document
   from toonverter.integrations import langchain_to_toon

   doc = Document(
       page_content="Important context...",
       metadata={"source": "doc.pdf", "page": 1}
   )

   toon_str = langchain_to_toon(doc)
   # Store in vector DB with 30-60% less space

LLM Prompts
^^^^^^^^^^^

Minimize token usage in context windows:

.. code-block:: python

   import toonverter as toon

   # Large dataset for LLM prompt
   data = get_large_dataset()

   # Convert to TOON for minimal tokens
   toon_str = toon.encode(data)
   prompt = f"Analyze this data:\\n{toon_str}"

API Responses
^^^^^^^^^^^^^

Efficient data transfer with FastAPI:

.. code-block:: python

   from fastapi import FastAPI
   from toonverter.integrations import TOONResponse

   app = FastAPI()

   @app.get("/data", response_class=TOONResponse)
   async def get_data():
       return {"users": [...], "count": 100}

Data Pipelines
^^^^^^^^^^^^^^

Convert between formats in ETL workflows:

.. code-block:: python

   import toonverter as toon

   # Load from various formats
   data = toon.load('input.json', format='json')

   # Process data
   processed = process_data(data)

   # Save in optimal format
   toon.save(processed, 'output.toon', format='toon')

Next Steps
----------

* :doc:`installation` - Install TOON Converter with your preferred integrations
* :doc:`quick_start` - Learn the basic API in 5 minutes
* :doc:`toon_format` - Understand the TOON format specification
* :doc:`../examples/basic_usage` - See practical examples

Questions or Issues?
--------------------

* `GitHub Issues <https://github.com/Be-Wagile-India/toonverter/issues>`_
* `Discussions <https://github.com/Be-Wagile-India/toonverter/discussions>`_
