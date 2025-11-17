Decoder API
============================================================

.. autoclass:: toonverter.Decoder
   :members:
   :undoc-members:
   :show-inheritance:

The ``Decoder`` class provides a stateful decoder for advanced use cases.

Example Usage
-------------

.. code-block:: python

   from toonverter import Decoder

   # Create decoder
   decoder = Decoder(format='toon')

   # Decode TOON string
   toon_str = "name: Alice\nage: 30"
   data = decoder.decode(toon_str)
   print(data)
