Chunker API
============================================================

.. autoclass:: toonverter.rag.chunking.ToonChunker
   :members:
   :undoc-members:
   :show-inheritance:

The ``ToonChunker`` class intelligently splits Python data structures into
token-optimized, semantically coherent TOON strings for Retrieval-Augmented Generation (RAG).

Example Usage
-------------

.. code-block:: python

   from toonverter.rag.chunking import ToonChunker
   
   # Create a chunker instance with a tight limit (for demonstration)
   chunker = ToonChunker(max_tokens=20, context_tokens=2)

   # Complex data structure
   data = {
       "user_profile": {"id": 1, "name": "Alice"},
       "settings": {"theme": "dark", "notifications": True}
   }
   
   # Process and print the chunks
   for i, chunk in enumerate(chunker.chunk(data)):
       print(f"--- CHUNK {i+1} (Tokens: {len(chunk.split())}) ---")
       print(chunk)

