Installation
============

TOON Converter supports Python 3.10+ and can be installed via pip with various optional dependencies
depending on your needs.

Basic Installation
------------------

Install the core library with basic format support (JSON, YAML, TOML, CSV, XML):

.. code-block:: bash

   pip install toonverter

This includes:

* TOON encoding and decoding
* JSON, YAML, TOML, CSV, XML support
* Token analysis with tiktoken
* Basic Python API

Individual Framework Integrations
----------------------------------

Install specific framework integrations as needed:

Data Science
^^^^^^^^^^^^

.. code-block:: bash

   # Pandas DataFrame support
   pip install toonverter[pandas]

   # SQLAlchemy ORM serialization
   pip install toonverter[sqlalchemy]

AI/LLM Frameworks
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # LangChain Document/Message support
   pip install toonverter[langchain]

   # LlamaIndex Node support
   pip install toonverter[llamaindex]

   # Haystack Pipeline integration
   pip install toonverter[haystack]

   # DSPy Example support
   pip install toonverter[dspy]

   # Instructor Response models
   pip install toonverter[instructor]

Web Frameworks
^^^^^^^^^^^^^^

.. code-block:: bash

   # FastAPI TOONResponse class
   pip install toonverter[fastapi]

   # Pydantic BaseModel serialization
   pip install toonverter[pydantic]

Protocols
^^^^^^^^^

.. code-block:: bash

   # Model Context Protocol server with 4 tools
   pip install toonverter[mcp]

Grouped Integrations
--------------------

Install multiple related frameworks at once:

.. code-block:: bash

   # All AI/LLM frameworks
   pip install toonverter[ai]
   # Includes: LlamaIndex, Haystack, DSPy, Instructor

   # All data science tools
   pip install toonverter[data]
   # Includes: Pandas, SQLAlchemy

   # All web frameworks
   pip install toonverter[web]
   # Includes: FastAPI, Pydantic

   # All LLM tools
   pip install toonverter[llm]
   # Includes: LangChain, MCP

CLI Tools
---------

Install command-line interface with rich output:

.. code-block:: bash

   pip install toonverter[cli]

Complete Installation
---------------------

Install all integrations and CLI tools:

.. code-block:: bash

   pip install toonverter[all]

Development Installation
------------------------

For contributors or those who want to modify the library:

Clone the Repository
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   git clone https://github.com/Be-Wagile-India/toonverter.git
   cd toonverter

Install in Editable Mode
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Install with all features
   pip install -e ".[all]"

   # Install development dependencies
   make install-dev

This installs:

* All optional dependencies
* Development tools (pytest, mypy, ruff, etc.)
* Pre-commit hooks
* Documentation tools (Sphinx)

Verify Installation
-------------------

Verify the installation is working:

.. code-block:: python

   import toonverter as toon

   # Check version
   print(toon.__version__)

   # Test basic encoding
   data = {"test": "value"}
   encoded = toon.encode(data)
   decoded = toon.decode(encoded)
   assert decoded == data

   print("✅ Installation successful!")

Check Installed Features
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   # List supported formats
   print("Formats:", toon.list_formats())

   # Check for integrations
   try:
       from toonverter.integrations import pandas_to_toon
       print("✅ Pandas integration available")
   except ImportError:
       print("❌ Pandas integration not installed")

Requirements
------------

Core Dependencies
^^^^^^^^^^^^^^^^^

These are automatically installed with the base package:

* ``typing-extensions >= 4.8.0`` - Type hints support
* ``tiktoken >= 0.5.0`` - Token counting
* ``PyYAML >= 6.0`` - YAML format support
* ``tomli >= 2.0.0`` - TOML support (Python < 3.11)

Optional Dependencies
^^^^^^^^^^^^^^^^^^^^^

Install as needed via extras:

* **pandas** >= 2.0.0
* **pydantic** >= 2.0.0
* **langchain** >= 0.1.0
* **fastapi** >= 0.100.0
* **sqlalchemy** >= 2.0.0
* **mcp** >= 0.9.0
* **llama-index** >= 0.10.0
* **haystack-ai** >= 2.0.0
* **dspy-ai** >= 2.4.0
* **instructor** >= 1.0.0
* **click** >= 8.1.0 (CLI)
* **rich** >= 13.0.0 (CLI)

Development Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^

For contributors:

* **pytest** >= 7.4.0
* **mypy** >= 1.7.0
* **ruff** >= 0.1.0
* **sphinx** >= 7.2.0
* **pre-commit** >= 3.5.0

Platform Support
----------------

TOON Converter is tested on:

* **Operating Systems**: Linux, macOS, Windows
* **Python Versions**: 3.10, 3.11, 3.12
* **Architectures**: x86_64, ARM64

Troubleshooting
---------------

Import Errors
^^^^^^^^^^^^^

If you encounter import errors for integrations:

.. code-block:: bash

   # Install the specific integration
   pip install toonverter[pandas]

   # Or install all integrations
   pip install toonverter[all]

Type Checking Issues
^^^^^^^^^^^^^^^^^^^^

If using mypy, install type stubs:

.. code-block:: bash

   pip install types-PyYAML types-toml

Version Conflicts
^^^^^^^^^^^^^^^^^

If you encounter version conflicts with other packages, try creating a clean virtual environment:

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install toonverter[all]

Next Steps
----------

* :doc:`quick_start` - Learn the basic API
* :doc:`../examples/basic_usage` - See practical examples
* :doc:`../guides/integrations/pandas` - Framework-specific guides
