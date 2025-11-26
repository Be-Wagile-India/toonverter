Schema Tools
============

TOON Converter provides a robust suite of tools for working with data schemas. These tools help you understand, validate, and evolve your data structures.

Schema Inference
----------------

The **Inferrer** analyzes your data and generates a formal schema definition (similar to JSON Schema or TOON Schema).

CLI Usage
^^^^^^^^^

.. code-block:: bash

   toon infer data.json -o schema.json

Python API
^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   data = {"name": "Alice", "age": 30}
   schema = toon.infer_schema(data)
   print(schema.to_dict())

Schema Validation
-----------------

The **Validator** ensures your data conforms to a schema.

CLI Usage
^^^^^^^^^

.. code-block:: bash

   toon validate data.json --schema schema.json

   # Strict mode (fails on unknown fields)
   toon validate data.json --schema schema.json --strict

Python API
^^^^^^^^^^

.. code-block:: python

   import toonverter as toon

   errors = toon.validate_schema(data, schema)
   if errors:
       print("Validation failed:", errors)

Schema Merging
--------------

As data evolves, you often need to combine schemas from different sources. The **Merge** tool combines multiple schemas into a unified one, widening types where necessary (e.g., if one file has an Integer and another has a Float, the merged schema will specify Float).

CLI Usage
^^^^^^^^^

.. code-block:: bash

   toon schema-merge file1_schema.json file2_schema.json -o unified_schema.json

   # Merge many files
   toon schema-merge schemas/*.json -o master_schema.json

Python API
^^^^^^^^^^

.. code-block:: python

   from toonverter.schema import SchemaField

   s1 = toon.infer_schema(data1)
   s2 = toon.infer_schema(data2)

   merged = s1.merge(s2)
