Llamaindex Integration
================================================================================

Integration guide for Llamaindex.

Installation
------------

.. code-block:: bash

   pip install toonverter[llamaindex]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import llamaindex_to_toon, toon_to_llamaindex

   # Convert to TOON
   toon_str = llamaindex_to_toon(obj)

   # Convert back
   restored = toon_to_llamaindex(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
