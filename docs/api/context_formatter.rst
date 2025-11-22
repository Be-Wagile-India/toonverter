Context Converter API
=====================

.. autoclass:: toonverter.core.context_formatter.ContextConverter
   :members:
   :undoc-members:
   :show-inheritance:

The ``ContextConverter`` class manages conversation history optimization and TOON formatting.

Example Usage
-------------

.. code-block:: python

   from toonverter.core.context_formatter import ContextConverter
   from toonverter.core.message import Message

   # Initialize converter with a token budget
   converter = ContextConverter(
       max_context_tokens=1000,
       context_policy="priority_then_recency"
   )

   # Define history and new message
   history = [
       Message(role="user", content="Hello"),
       Message(role="assistant", content="Hi there! How can I help?")
   ]
   new_msg = Message(role="user", content="What is TOON format?")

   # Generate optimized payload
   payload = converter.generate_toon_payload(history, new_msg)
   print(payload)