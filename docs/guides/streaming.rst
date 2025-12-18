Memory-Efficient Streaming
==========================

TOON Converter provides advanced streaming capabilities for processing massive datasets that exceed available RAM.

True O(1) Memory Decoding
-------------------------

Traditional decoders (including the standard ``toon.decode()``) buffer the entire input string and then build a complete Python object tree. For gigabyte-scale files, this leads to massive memory spikes.

The ``StreamDecoder`` uses an **event-based architecture** (SAX-style) to traverse the TOON document incrementally.

Basic Usage: items()
--------------------

The recommended way to stream a large root array is using the ``items()`` method. It reconstructs top-level items one-by-one, yielding them as they are finished.

.. code-block:: python

   import toonverter as toon
   
   decoder = toon.StreamDecoder()
   
   # stream can be any iterator of strings (e.g., lines from a file)
   with open("massive_data.toon", "r") as f:
       for item in decoder.items(f):
           process(item)  # Only one item is in memory at a time

Event-Based Traversal
---------------------

For cases where even a single item is too large for memory (e.g., a single array with millions of fields), you can use the ``events=True`` mode to get raw parsing events.

.. code-block:: python

   from toonverter.decoders.event_parser import ParserEvent
   
   # Yields fine-grained events instead of full objects
   for event, value in decoder.items(f, events=True):
       if event == ParserEvent.START_ARRAY:
           print(f"Starting array of length: {value}")
       elif event == ParserEvent.KEY:
           print(f"Found field: {value}")
       elif event == ParserEvent.VALUE:
           print(f"Value: {value}")

Available Events
^^^^^^^^^^^^^^^^

The ``ParserEvent`` enum includes:
* ``START_DOCUMENT`` / ``END_DOCUMENT``
* ``START_OBJECT`` / ``END_OBJECT``
* ``START_ARRAY`` / ``END_ARRAY``
* ``KEY`` (for object fields)
* ``VALUE`` (for primitives)

Supported Structures
--------------------

* **Root Arrays**: Fully supported for item-by-item streaming using ``[N]:`` or ``[*]:`` headers.
* **Indefinite Arrays**: Streaming works perfectly with the new indefinite ``[*]`` syntax for infinite generators.
* **Nested Objects**: Large nested objects are traversed incrementally in event mode.

Performance Comparison
----------------------

On a dataset with 200,000 fields in a single item:
* **Standard Decoding**: Spikes by ~135 MiB (buffers tokens).
* **Streaming items()**: Near-constant memory footprint (~0.3 MiB overhead).

Indefinite Arrays [*]
---------------------

You can also encode infinite generators using the streaming encoder. This is useful for long-running processes or log streams.

.. code-block:: python

   import itertools
   import sys
   from toonverter.encoders.stream_encoder import StreamList, ToonStreamEncoder
   
   # An infinite count generator
   infinite_gen = itertools.count(start=1)
   
   # Use length=None to signify indefinite length
   stream_data = StreamList(iterator=infinite_gen, length=None)
   
   encoder = ToonStreamEncoder()
   for chunk in encoder.iterencode(stream_data):
       sys.stdout.write(chunk)
       # Output: [*]:
       #         - 1
       #         - 2
       #         - 3
       #         ...

LLM Context Window Optimization
-------------------------------

When using TOON for LLM context windows, streaming allows you to:
1. **Partial Processing**: Start processing the first items of a massive response before the LLM has finished generating the entire document.
2. **Filtering on the Fly**: Drop irrelevant items during decoding to save RAM.
3. **Infinite Feedback**: Stream long-running agent logs directly into the context window without intermediate buffering.
