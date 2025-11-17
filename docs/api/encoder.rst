Encoder API
============================================================

.. autoclass:: toonverter.Encoder
   :members:
   :undoc-members:
   :show-inheritance:

The ``Encoder`` class provides a stateful encoder for advanced use cases.

Example Usage
-------------

.. code-block:: python

   from toonverter import Encoder

   # Create encoder with custom options
   encoder = Encoder(format='toon', compact=True)

   # Encode data
   data = {"name": "Alice", "age": 30}
   toon_str = encoder.encode(data)
   print(toon_str)
