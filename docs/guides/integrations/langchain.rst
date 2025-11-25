LangChain Integration
=====================

Optimize LangChain documents and messages for RAG systems with 30-60% token savings.

Installation
------------

.. code-block:: bash

   pip install toonverter[langchain]

Document Conversion
-------------------

.. code-block:: python

   from langchain.schema import Document
   from toonverter.integrations import langchain_to_toon, toon_to_langchain

   # Create documents
   docs = [
       Document(page_content="Info about AI", metadata={"id": 1}),
       Document(page_content="Info about ML", metadata={"id": 2})
   ]

   # Convert single document
   toon_doc = langchain_to_toon(docs[0])

   # Convert list of documents (more efficient)
   toon_docs_str = langchain_to_toon(docs)
   
   # Output (approximate):
   # - page_content: Info about AI
   #   metadata: {id: 1}
   # - page_content: Info about ML
   #   metadata: {id: 2}

   # Convert back
   # Returns a single Document if input was a single item's TOON string
   restored_doc = toon_to_langchain(toon_doc)
   
   # Returns a list of Documents if input was a list's TOON string
   # Note: toon_to_langchain currently returns a single Document or list based on structure,
   # but explicitly checking the type is recommended.

Message Conversion
------------------

.. code-block:: python

   from langchain.schema import HumanMessage, AIMessage
   from toonverter.integrations import messages_to_toon, toon_to_messages

   messages = [
       HumanMessage(content="What is TOON?"),
       AIMessage(content="TOON is a token-optimized format")
   ]

   # Convert list of messages
   # This wraps them in a structure like {"messages": [...]} for safe parsing
   toon_str = messages_to_toon(messages)

   # Convert back to list of Message objects
   restored_msgs = toon_to_messages(toon_str)

Use Cases
---------

Vector Database Storage
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from langchain.vectorstores import Chroma
   from toonverter.integrations import langchain_to_toon

   # Convert documents before storing
   docs = load_documents()
   toon_docs = [langchain_to_toon(doc) for doc in docs]

   # Store with 30-60% less space

RAG Pipeline
^^^^^^^^^^^^

.. code-block:: python

   from langchain.chains import RetrievalQA
   from toonverter.integrations import langchain_to_toon, toon_to_langchain

   # Convert documents for efficient retrieval
   docs_toon = [langchain_to_toon(doc) for doc in docs]

   # Store and retrieve efficiently

Configuration
-------------

.. code-block:: python

   from toonverter.integrations import langchain_to_toon

   toon_str = langchain_to_toon(
       doc,
       include_metadata=True,    # Include metadata
       compact_content=False     # Compact page_content
   )

See Also
--------

* :doc:`../quick_start` - Basic usage
* :ref:`api/integrations:LangChain Integration` - API reference
