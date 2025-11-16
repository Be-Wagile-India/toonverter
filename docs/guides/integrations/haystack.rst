Haystack Integration
================================================================================

Integration guide for Haystack.

Installation
------------

.. code-block:: bash

   pip install toonverter[haystack]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import haystack_to_toon, toon_to_haystack

   # Convert to TOON
   toon_str = haystack_to_toon(obj)

   # Convert back
   restored = toon_to_haystack(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
