Instructor Integration
================================================================================

Integration guide for Instructor.

Installation
------------

.. code-block:: bash

   pip install toonverter[instructor]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import instructor_to_toon, toon_to_instructor

   # Convert to TOON
   toon_str = instructor_to_toon(obj)

   # Convert back
   restored = toon_to_instructor(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
