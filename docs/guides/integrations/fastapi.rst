FastAPI Integration
===================

Native TOON response class for FastAPI endpoints.

Installation
------------

.. code-block:: bash

   pip install toonverter[fastapi]

Basic Usage
-----------

.. code-block:: python

   from fastapi import FastAPI
   from toonverter.integrations import TOONResponse

   app = FastAPI()

   @app.get("/users", response_class=TOONResponse)
   async def get_users():
       return {
           "users": [
               {"name": "Alice", "age": 30},
               {"name": "Bob", "age": 25}
           ],
           "count": 2
       }

Response Automatically
^^^^^^^^^^^^^^^^^^^^^^

The response is automatically serialized as TOON with proper content-type header.

Token Savings
-------------

.. code-block:: python

   # JSON response: ~120 characters
   # TOON response: ~60 characters (50% savings)
   # Perfect for mobile/low-bandwidth clients

Use Cases
---------

- Efficient API responses
- Mobile-first applications
- Token-conscious LLM applications
- High-traffic endpoints

See Also
--------

* :doc:`../quick_start` - Basic usage
* :ref:`api/integrations:FastAPI Integration` - API reference
