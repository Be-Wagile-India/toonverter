Analyzer API
============================================================

.. autoclass:: toonverter.Analyzer
   :members:
   :undoc-members:
   :show-inheritance:

The ``Analyzer`` class provides token usage analysis across formats.

Example Usage
-------------

.. code-block:: python

   from toonverter import Analyzer

   # Create analyzer
   analyzer = Analyzer(model='gpt-4')

   # Analyze data
   data = {"users": [{"name": "Alice", "age": 30}]}
   report = analyzer.analyze_multi_format(data, formats=['json', 'toon'])
   print(f"Best format: {report.best_format}")
   print(f"Savings: {report.max_savings_percentage:.1f}%")
