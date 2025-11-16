Mcp Integration
================================================================================

Integration guide for Mcp.

Installation
------------

.. code-block:: bash

   pip install toonverter[mcp]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import mcp_to_toon, toon_to_mcp

   # Convert to TOON
   toon_str = mcp_to_toon(obj)

   # Convert back
   restored = toon_to_mcp(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
