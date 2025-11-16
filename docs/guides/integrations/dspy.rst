Dspy Integration
================================================================================

Integration guide for Dspy.

Installation
------------

.. code-block:: bash

   pip install toonverter[dspy]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import dspy_to_toon, toon_to_dspy

   # Convert to TOON
   toon_str = dspy_to_toon(obj)

   # Convert back
   restored = toon_to_dspy(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
