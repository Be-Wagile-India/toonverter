Message Data Model
==================

.. autoclass:: toonverter.core.message.Message
   :members:
   :undoc-members:
   :show-inheritance:
   :no-index:

The ``Message`` class represents a single immutable message turn in a conversation, automatically calculating its own token count upon initialization.

Example Usage
-------------

.. code-block:: python

   from toonverter.core.message import Message

   # Create a message
   msg = Message(role="user", content="Explain quantum computing", priority=10)

   # Access metadata and token count
   print(f"Role: {msg.role}")
   print(f"Tokens: {msg.token_count}")

   # Convert to dictionary for storage
   data = msg.to_dict()
   print(data)