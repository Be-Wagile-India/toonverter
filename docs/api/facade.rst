Facade API
============================================================

The Facade API provides simple functions for common tasks - the recommended API for 90% of users.

.. automodule:: toonverter
   :members: encode, decode, convert, analyze, load, save, list_formats, is_supported
   :undoc-members:

Core Functions
--------------

These functions provide a simple interface to toonverter's functionality:

* ``encode(data, to_format='toon')`` - Encode data to a format
* ``decode(data_str, from_format='toon')`` - Decode data from a format
* ``convert(source, target, from_format, to_format)`` - Convert files between formats
* ``analyze(data, compare_formats)`` - Analyze token usage across formats
* ``load(path, format)`` - Load data from file
* ``save(data, path, format)`` - Save data to file
* ``list_formats()`` - List all supported formats
* ``is_supported(format)`` - Check if a format is supported

Example Usage
-------------

.. code-block:: python

   import toonverter as toon

   # Encode to TOON
   data = {"name": "Alice", "age": 30}
   toon_str = toon.encode(data)

   # Decode from TOON
   decoded = toon.decode(toon_str)

   # Convert files
   toon.convert('data.json', 'data.toon', 'json', 'toon')

   # Analyze token usage
   report = toon.analyze(data, compare_formats=['json', 'toon'])
   print(f"Best: {report.best_format}, Savings: {report.max_savings_percentage:.1f}%")

   # Save and load
   toon.save(data, 'output.toon', format='toon')
   loaded = toon.load('output.toon', format='toon')

   # Check format support
   print(toon.list_formats())  # ['csv', 'json', 'toml', 'toon', 'xml', 'yaml']
   print(toon.is_supported('toon'))  # True
