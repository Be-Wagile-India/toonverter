Pydantic Integration
================================================================================

Integration guide for Pydantic.

Installation
------------

.. code-block:: bash

   pip install toonverter[pydantic]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import pydantic_to_toon, toon_to_pydantic

   # Convert to TOON
   toon_str = pydantic_to_toon(obj)

   # Convert back
   restored = toon_to_pydantic(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
