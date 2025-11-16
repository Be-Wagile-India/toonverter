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

   # Create document
   doc = Document(
       page_content="Important information about AI",
       metadata={"source": "doc.pdf", "page": 1}
   )

   # Convert to TOON
   toon_str = langchain_to_toon(doc)
   # Output:
   # page_content: Important information about AI
   # metadata:
   #   source: doc.pdf
   #   page: 1

   # Convert back
   restored_doc = toon_to_langchain(toon_str)

Message Conversion
------------------

.. code-block:: python

   from langchain.schema import HumanMessage, AIMessage
   from toonverter.integrations import langchain_to_toon, toon_to_langchain

   messages = [
       HumanMessage(content="What is TOON?"),
       AIMessage(content="TOON is a token-optimized format")
   ]

   # Convert messages
   for msg in messages:
       toon_str = langchain_to_toon(msg)

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
