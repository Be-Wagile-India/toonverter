Tiktoken Counter API
============================================================

.. autoclass:: toonverter.analysis.token_counter.TiktokenCounter
   :members:
   :undoc-members:
   :show-inheritance:

The ``TiktokenCounter`` class provides model-specific token usage counting,
implementing the :py:class:`toonverter.core.interfaces.TokenCounter` interface using the ``tiktoken`` library.

Example Usage
-------------

.. code-block:: python

   from toonverter.analysis.token_counter import TiktokenCounter

   # Create counter for a specific model
   counter = TiktokenCounter(model_name='gpt-3.5-turbo')

   text = "This is a simple sentence."
   
   # Count tokens
   token_count = counter.count_tokens(text)
   print(f"Text: '{text}'")
   print(f"Tokens: {token_count}")
   
   # Detailed analysis (used for debugging/reporting)
   report = counter.analyze(text, _format_name='text')
   print(f"Analysis: {report}")

