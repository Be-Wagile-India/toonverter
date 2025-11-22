Context Optimization Utilities
==============================

.. automodule:: toonverter.utils.context_helpers
   :members: count_tokens, optimize_context_window, get_priority_key
   :undoc-members:
   :show-inheritance:
   :no-index:

The ``context_helpers`` module provides utility functions for token counting and context window management strategies.

Example Usage
-------------

.. code-block:: python

   from toonverter.utils.context_helpers import count_tokens, optimize_context_window

   # Count tokens for arbitrary data
   data = {"role": "user", "content": "Hello world"}
   count = count_tokens(data)
   print(f"Token count: {count}")

   # Optimize a raw list of records
   records = [
       {"content": "old message", "timestamp": 100, "token_count": 50},
       {"content": "new message", "timestamp": 200, "token_count": 50}
   ]
   
   # Trim list to fit within 60 tokens based on recency
   optimized = optimize_context_window(records, max_tokens=60, policy="recency")
   print(f"Kept {len(optimized)} record(s)")