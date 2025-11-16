Sqlalchemy Integration
================================================================================

Integration guide for Sqlalchemy.

Installation
------------

.. code-block:: bash

   pip install toonverter[sqlalchemy]

Basic Usage
-----------

See integration tests and examples for detailed usage.

.. code-block:: python

   from toonverter.integrations import sqlalchemy_to_toon, toon_to_sqlalchemy

   # Convert to TOON
   toon_str = sqlalchemy_to_toon(obj)

   # Convert back
   restored = toon_to_sqlalchemy(toon_str)

See Also
--------

* :doc: - Basic usage
* :ref: - API reference
