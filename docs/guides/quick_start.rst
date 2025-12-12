Quick Start
===========

This guide covers the essential features of TOON Converter in 5 minutes.

Simple Facade API
-----------------

The facade API (``import toonverter as toon``) provides simple functions for 90% of use cases.

Encoding and Decoding
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   # Encode Python dict to TOON
   data = {"name": "Alice", "age": 30, "city": "NYC"}
   toon_str = toon.encode(data)
   print(toon_str)
   # Output:
   # name: Alice
   # age: 30
   # city: NYC

   # Decode TOON back to Python
   decoded = toon.decode(toon_str)
   print(decoded)
   # Output: {'name': 'Alice', 'age': 30, 'city': 'NYC'}

Working with Files
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   # Load data from any format
   data = toon.load('data.json', format='json')

   # Save as TOON
   toon.save(data, 'data.toon', format='toon')

   # Convert between formats directly
   toon.convert(
       source='data.json',
       target='data.toon',
       from_format='json',
       to_format='toon'
   )

Token Analysis
^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   data = {"name": "Alice", "age": 30, "city": "NYC"}

   # Analyze token usage across formats
   report = toon.analyze(data, compare_formats=['json', 'toon'])

   print(f"Best format: {report.best_format}")
   print(f"Token savings: {report.max_savings_percentage:.1f}%")
   # Output:
   # Best format: toon
   # Token savings: 33.3%

Listing Formats
^^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   # Check available formats
   print(toon.list_formats())
   # Output: ['csv', 'json', 'toml', 'toon', 'xml', 'yaml']

High-Performance Batch Processing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For processing millions of files, use the Rust-accelerated batch functions. These functions utilize parallel processing and memory-mapped I/O for maximum performance.

.. code-block:: python

   import toonverter as toon

   # Batch convert JSON to TOON (in-memory)
   # Returns list of (path, content, is_error)
   results = toon.convert_json_batch(["file1.json", "file2.json"])

   # Batch convert directory to TOON (streaming to disk)
   # Writes .toon files to ./output directory, avoiding memory issues
   toon.convert_json_directory("./data", recursive=True, output_dir="./output")

Object-Oriented API
-------------------

For more control, use the object-oriented API with configurable options.

Custom Encoder
^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Encoder

   encoder = Encoder(
       format='toon',
       delimiter=',',
       compact=True,
       sort_keys=True
   )

   data = {"name": "Alice", "age": 30}
   encoded = encoder.encode(data)

Custom Decoder
^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Decoder

   decoder = Decoder(
       format='toon',
       strict=True,  # Enable strict validation
       infer_types=True
   )

   toon_str = "name: Alice\\nage: 30"
   decoded = decoder.decode(toon_str)

Stateful Converter
^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Converter

   # Create converter with default options
   converter = Converter(
       from_format='json',
       to_format='toon',
       compact=True
   )

   # Convert multiple files with same settings
   converter.convert_file('data1.json', 'data1.toon')
   converter.convert_file('data2.json', 'data2.toon')

Token Analyzer
^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter import Analyzer

   analyzer = Analyzer(model='gpt-4')  # Specify tokenizer model

   data = {"users": [...]}  # Your data

   # Analyze multiple formats
   report = analyzer.analyze_multi_format(
       data,
       formats=['json', 'yaml', 'toon']
   )

   print(f"JSON tokens: {report.format_results['json'].token_count}")
   print(f"TOON tokens: {report.format_results['toon'].token_count}")
   print(f"Savings: {report.max_savings_percentage:.1f}%")

Working with Different Data Types
----------------------------------

Nested Objects
^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   data = {
       "user": {
           "name": "Alice",
           "address": {
               "city": "NYC",
               "zip": "10001"
           }
       }
   }

   toon_str = toon.encode(data)
   # Output:
   # user:
   #   name: Alice
   #   address:
       city: NYC
   #     zip: "10001"

Arrays
^^^^^^

.. code-block:: python

   import toonverter as toon

   # Simple array
   data = {"tags": ["python", "llm", "optimization"]}
   toon_str = toon.encode(data)
   # Output: tags[3]: python,llm,optimization

   # Array of objects (tabular form)
   data = {
       "users": [
           {"name": "Alice", "age": 30},
           {"name": "Bob", "age": 25}
       ]
   }
   toon_str = toon.encode(data)
   # Output:
   # users[2]{name,age}:
   #   Alice,30
   #   Bob,25

Type Preservation
^^^^^^^^^^^^^^^^^

.. code-block:: python

   import toonverter as toon
   from datetime import datetime

   data = {
       "count": 100,
       "price": 19.99,
       "active": True,
       "updated": datetime(2025, 1, 15, 10, 30, 0)
   }

   toon_str = toon.encode(data)
   # Types are preserved in TOON format

   decoded = toon.decode(toon_str)
   assert isinstance(decoded['count'], int)
   assert isinstance(decoded['price'], float)
   assert isinstance(decoded['active'], bool)

Command-Line Interface
----------------------

Install CLI support:

.. code-block:: bash

   pip install toonverter[cli]

Basic Commands
^^^^^^^^^^^^^^

.. code-block:: bash

   # Convert files
   toonverter convert data.json data.toon --from json --to toon

   # Encode to TOON
   toonverter encode data.json --output data.toon

   # Decode from TOON
   toonverter decode data.toon --output data.json --format json

   # Analyze token usage
   toonverter analyze data.json --compare json toon yaml

   # List supported formats
   toonverter formats

Integration Examples
--------------------

Pandas DataFrame
^^^^^^^^^^^^^^^^

.. code-block:: python

   import pandas as pd
   from toonverter.integrations import pandas_to_toon, toon_to_pandas

   df = pd.DataFrame({
       'name': ['Alice', 'Bob', 'Charlie'],
       'age': [30, 25, 35]
   })

   # Convert to TOON (uses optimal tabular format)
   toon_str = pandas_to_toon(df)

   # Convert back
   restored_df = toon_to_pandas(toon_str)

Pydantic Models
^^^^^^^^^^^^^^^

.. code-block:: python

   from pydantic import BaseModel
   from toonverter.integrations import pydantic_to_toon, toon_to_pydantic

   class User(BaseModel):
       name: str
       age: int

   user = User(name="Alice", age=30)

   # Serialize to TOON
   toon_str = pydantic_to_toon(user)

   # Deserialize from TOON
   restored = toon_to_pydantic(toon_str, User)

LangChain Documents
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from langchain.schema import Document
   from toonverter.integrations import langchain_to_toon, toon_to_langchain

   doc = Document(
       page_content="Important information",
       metadata={"source": "doc.pdf"}
   )

   # Convert for efficient storage
   toon_str = langchain_to_toon(doc)

   # Restore
   restored_doc = toon_to_langchain(toon_str)

FastAPI Responses
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from fastapi import FastAPI
   from toonverter.integrations import TOONResponse

   app = FastAPI()

   @app.get("/users", response_class=TOONResponse)
   async def get_users():
       return {"users": [...], "count": 100}
       # Automatically serialized as TOON

Best Practices
--------------

1. **Use Tabular Format for Uniform Data**

   .. code-block:: python

      # This will automatically use tabular format (most efficient)
      data = {
          "items": [
              {"id": 1, "name": "Item1"},
              {"id": 2, "name": "Item2"}
          ]
      }

2. **Enable Strict Mode for Production**

   .. code-block:: python

      from toonverter import Decoder

      decoder = Decoder(strict=True)  # Catch validation errors

3. **Analyze Before Deploying**

   .. code-block:: python

      import toonverter as toon

      # Test with real data
      report = toon.analyze(your_data, compare_formats=['json', 'toon'])
      if report.max_savings_percentage > 30:
          print("TOON is worth it!")

4. **Use Type Hints**

   .. code-block:: python

      from typing import Any
      import toonverter as toon

      def process_data(data: dict[str, Any]) -> str:
          return toon.encode(data)

Next Steps
----------

* :doc:`toon_format` - Learn the TOON format in detail
* :doc:`configuration` - Configure encoding/decoding options
* :doc:`../examples/basic_usage` - See more examples
* :doc:`../api/facade` - Full API reference
