Pandas Integration
==================

TOON Converter provides seamless integration with Pandas DataFrames, automatically using the optimal
tabular format for maximum token efficiency.

Installation
------------

.. code-block:: bash

   pip install toonverter[pandas]

Basic Usage
-----------

DataFrame to TOON
^^^^^^^^^^^^^^^^^

.. code-block:: python

   import pandas as pd
   from toonverter.integrations import pandas_to_toon

   df = pd.DataFrame({
       'name': ['Alice', 'Bob', 'Charlie'],
       'age': [30, 25, 35],
       'city': ['NYC', 'LA', 'SF']
   })

   toon_str = pandas_to_toon(df)
   print(toon_str)
   # Output:
   # [3]{name,age,city}:
   #   Alice,30,NYC
   #   Bob,25,LA
   #   Charlie,35,SF

TOON to DataFrame
^^^^^^^^^^^^^^^^^

.. code-block:: python

   from toonverter.integrations import toon_to_pandas

   toon_str = """[3]{name,age,city}:
     Alice,30,NYC
     Bob,25,LA
     Charlie,35,SF"""

   df = toon_to_pandas(toon_str)
   print(df)
   #       name  age city
   # 0    Alice   30  NYC
   # 1      Bob   25   LA
   # 2  Charlie   35   SF

Configuration Options
---------------------

Include Index
^^^^^^^^^^^^^

.. code-block:: python

   # Include DataFrame index in TOON output
   toon_str = pandas_to_toon(df, include_index=True)

   # Restore with index
   df_with_index = toon_to_pandas(toon_str)

Date Formatting
^^^^^^^^^^^^^^^

.. code-block:: python

   # ISO format (default)
   toon_str = pandas_to_toon(df, date_format='iso')

   # Unix timestamp
   toon_str = pandas_to_toon(df, date_format='unix')

   # String format
   toon_str = pandas_to_toon(df, date_format='string')

Token Savings
-------------

.. code-block:: python

   import pandas as pd
   import toonverter as toon

   df = pd.DataFrame({
       'id': range(1000),
       'name': [f'User{i}' for i in range(1000)],
       'value': [i * 10 for i in range(1000)]
   })

   # Analyze savings
   from toonverter.integrations import pandas_to_toon
   import json

   toon_str = pandas_to_toon(df)
   json_str = df.to_json(orient='records')

   report = toon.analyze(df.to_dict('records'), compare_formats=['json', 'toon'])
   print(f"Savings: {report.max_savings_percentage:.1f}%")
   # Typical savings: 45-55% for tabular data

Use Cases
---------

Data Storage
^^^^^^^^^^^^

.. code-block:: python

   # Save DataFrame in TOON format
   df = pd.read_csv('large_data.csv')
   toon_str = pandas_to_toon(df)

   with open('data.toon', 'w') as f:
       f.write(toon_str)

   # Load later
   with open('data.toon', 'r') as f:
       toon_str = f.read()

   df_restored = toon_to_pandas(toon_str)

LLM Context
^^^^^^^^^^^

.. code-block:: python

   # Include DataFrame in LLM prompt with minimal tokens
   df = get_analysis_data()
   toon_str = pandas_to_toon(df)

   prompt = f"""
   Analyze this data:
   {toon_str}

   What trends do you observe?
   """

API Responses
^^^^^^^^^^^^^

.. code-block:: python

   from fastapi import FastAPI
   from toonverter.integrations import pandas_to_toon

   app = FastAPI()

   @app.get("/data")
   async def get_data():
       df = get_dataframe()
       return {"data": pandas_to_toon(df)}

Type Handling
-------------

Numeric Types
^^^^^^^^^^^^^

.. code-block:: python

   df = pd.DataFrame({
       'int_col': [1, 2, 3],
       'float_col': [1.1, 2.2, 3.3],
       'bool_col': [True, False, True]
   })

   toon_str = pandas_to_toon(df)
   # Types are preserved in TOON

DateTime Types
^^^^^^^^^^^^^^

.. code-block:: python

   df = pd.DataFrame({
       'date': pd.date_range('2025-01-01', periods=3),
       'value': [10, 20, 30]
   })

   toon_str = pandas_to_toon(df, date_format='iso')

Categorical Types
^^^^^^^^^^^^^^^^^

.. code-block:: python

   df = pd.DataFrame({
       'category': pd.Categorical(['A', 'B', 'A', 'C']),
       'value': [1, 2, 3, 4]
   })

   toon_str = pandas_to_toon(df)
   # Categories stored as strings

Performance
-----------

.. code-block:: python

   import pandas as pd
   from toonverter.integrations import pandas_to_toon
   import time

   # Large DataFrame
   df = pd.DataFrame({
       'id': range(10000),
       'value': range(10000)
   })

   start = time.time()
   toon_str = pandas_to_toon(df)
   elapsed = time.time() - start

   print(f"Encoded 10,000 rows in {elapsed:.3f}s")
   # Typical: <0.1s

See Also
--------

* :doc:`../quick_start` - Basic usage
* :doc:`../toon_format` - TOON tabular arrays
* :ref:`api/integrations:Pandas Integration` - API reference
