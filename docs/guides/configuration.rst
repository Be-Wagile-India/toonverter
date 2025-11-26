Configuration
=============

TOON Converter provides various configuration options to customize encoding, decoding, and conversion behavior.

Encoder Configuration
---------------------

Basic Options
^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Encoder

   encoder = Encoder(
       format='toon',
       delimiter=',',          # Delimiter: ',', '\\t', or '|'
       compact=False,          # Single-line objects when possible
       sort_keys=False,        # Sort object keys alphabetically
       indent_size=2,          # Spaces per indentation level
       use_type_annotations=False,  # Add type annotations
   )

   result = encoder.encode(data)

Delimiter Options
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Encoder
   from toonverter.core.spec import Delimiter

   # Comma (default)
   encoder = Encoder(delimiter=Delimiter.COMMA)

   # Tab
   encoder = Encoder(delimiter=Delimiter.TAB)

   # Pipe
   encoder = Encoder(delimiter=Delimiter.PIPE)

Compact Mode
^^^^^^^^^^^^

.. code-block:: python

   encoder = Encoder(compact=True)

   # Compact: name: Alice,age: 30,city: NYC
   # Normal:  name: Alice
   #          age: 30
   #          city: NYC

Decoder Configuration
---------------------

Basic Options
^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Decoder

   decoder = Decoder(
       format='toon',
       strict=False,           # Enable strict validation
       infer_types=True,       # Automatically infer types
       validate_schema=False,  # Validate against schema
   )

   result = decoder.decode(toon_str)

Strict Mode
^^^^^^^^^^^

Enable strict validation for production use:

.. code-block:: python

   decoder = Decoder(strict=True)

   # Strict mode checks:
   # - Number canonical form
   # - String quoting rules
   # - Proper indentation
   # - Valid escape sequences
   # - No trailing commas
   # - Consistent delimiters

Converter Configuration
-----------------------

.. code-block:: python

   from toonverter import Converter

   converter = Converter(
       from_format='json',
       to_format='toon',
       compact=True,
       sort_keys=True,
       indent_size=2,
   )

   converter.convert_file('input.json', 'output.toon')

Analyzer Configuration
----------------------

.. code-block:: python

   from toonverter import Analyzer

   analyzer = Analyzer(
       model='gpt-4',          # Tokenizer model
       include_stats=True,     # Include detailed stats
   )

   report = analyzer.analyze_multi_format(
       data,
       formats=['json', 'yaml', 'toon']
   )

Tokenizer Models
^^^^^^^^^^^^^^^^

Available tokenizer models:

* ``gpt-4`` (default)
* ``gpt-3.5-turbo``
* ``text-davinci-003``
* ``claude-2``

.. code-block:: python

   analyzer = Analyzer(model='gpt-3.5-turbo')

Global Configuration
--------------------

Set default options for the facade API:

.. code-block:: python

   import toonverter as toon

   # Configure defaults
   toon.config.update(
       strict=False,
       compact=False,
       delimiter=',',
       indent_size=2,
   )

   # Use configured defaults
   encoded = toon.encode(data)

Environment Variables
---------------------

Configure via environment variables:

.. code-block:: bash

   export TOONVERTER_STRICT=true
   export TOONVERTER_DELIMITER=tab
   export TOONVERTER_INDENT_SIZE=4

.. code-block:: python

   import toonverter as toon

   # Uses environment variable settings
   encoded = toon.encode(data)

Integration-Specific Configuration
-----------------------------------

Pandas Integration
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter.integrations import pandas_to_toon

   toon_str = pandas_to_toon(
       df,
       include_index=False,     # Include DataFrame index
       date_format='iso',       # Date format: 'iso', 'unix', 'string'
   )

Pydantic Integration
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter.integrations import pydantic_to_toon

   toon_str = pydantic_to_toon(
       model,
       exclude_none=False,      # Exclude None values
       by_alias=False,          # Use field aliases
   )

SQLAlchemy Integration
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter.integrations import sqlalchemy_to_toon

   toon_str = sqlalchemy_to_toon(
       instance,
       include_relationships=True,  # Include related objects
       lazy_load=False,              # Eager load relationships
   )

LangChain Integration
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter.integrations import langchain_to_toon

   toon_str = langchain_to_toon(
       doc,
       include_metadata=True,    # Include document metadata
       compact_content=False,    # Compact page_content
   )

Custom Format Adapters
----------------------

Register custom format adapters:

.. code-block:: python

   from toonverter.core.interfaces import FormatAdapter
   from toonverter.core.registry import registry

   class CustomAdapter(FormatAdapter):
       def encode(self, data, options):
           # Custom encoding logic
           return custom_encode(data, **options)

       def decode(self, data_str, options):
           # Custom decoding logic
           return custom_decode(data_str, **options)

   # Register adapter
   registry.register('custom', CustomAdapter())

   # Use custom format
   import toonverter as toon
   toon.convert(
       source='data.custom',
       target='data.toon',
       from_format='custom',
       to_format='toon'
   )

Plugin Development
------------------

Create plugins for distribution:

.. code-block:: python

   # my_plugin.py
   from toonverter.plugins import Plugin

   class MyFormatPlugin(Plugin):
       name = "myformat"
       version = "1.0.0"

       def register(self, registry):
           registry.register('myformat', MyFormatAdapter())

.. code-block:: python

   # setup.py
   setup(
       name='toonverter-myformat',
       entry_points={
           'toonverter.plugins': [
               'myformat = my_plugin:MyFormatPlugin',
           ]
       }
   )

Best Practices
--------------

Production Deployments
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Decoder

   # Use strict mode in production
   decoder = Decoder(strict=True)

   try:
       data = decoder.decode(toon_str)
   except ValidationError as e:
       logger.error(f"Invalid TOON: {e}")
       raise

Performance Optimization
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Encoder

   # Reuse encoder instances
   encoder = Encoder(compact=True)

   # Encode multiple datasets
   for dataset in datasets:
       result = encoder.encode(dataset)

Type Safety
^^^^^^^^^^^

.. code-block:: python

   from typing import Any
   import toonverter as toon

   def encode_data(data: dict[str, Any]) -> str:
       return toon.encode(data)

   def decode_data(toon_str: str) -> dict[str, Any]:
       return toon.decode(toon_str)

See Also
--------

* :doc:`../api/encoder` - Encoder API reference
* :doc:`../api/decoder` - Decoder API reference

For more details on token counting and analysis, see the :doc:`../api/analysis` reference.
