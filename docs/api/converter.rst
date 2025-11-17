Converter API
============================================================

.. autoclass:: toonverter.Converter
   :members:
   :undoc-members:
   :show-inheritance:

The ``Converter`` class provides a stateful converter for format conversion.

Example Usage
-------------

.. code-block:: python

   from toonverter import Converter

   # Create converter
   converter = Converter(from_format='json', to_format='toon')

   # Convert file
   result = converter.convert_file('data.json', 'data.toon')
   print(f"Saved {result.target_tokens} tokens")
