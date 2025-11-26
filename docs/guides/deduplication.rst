Semantic Deduplication
======================

TOON Converter includes a powerful **Semantic Deduplication** engine. Unlike traditional deduplication which looks for exact matches, this feature uses embedding models (via ``sentence-transformers``) to identify items that are *semantically* identical or highly similar.

This is particularly useful for:
* Cleaning datasets before RAG ingestion
* Reducing context window usage by removing redundant information
* Normalizing user inputs

Installation
------------

To use semantic features, you need to install the optional dependencies:

.. code-block:: bash

   pip install "toonverter[semantic]"
   # Or directly:
   pip install sentence-transformers scikit-learn

CLI Usage
---------

The ``deduplicate`` command processes a file and removes semantic duplicates from lists found within the data structure.

.. code-block:: bash

   # Basic usage
   toon deduplicate input.json -o cleaned.json

   # Customize model and threshold
   toon deduplicate input.json \
       --model all-MiniLM-L6-v2 \
       --threshold 0.85 \
       -o cleaned.json

Arguments:
* ``input_file``: Path to source data file (JSON, TOON, YAML, etc.)
* ``--output, -o``: Path to save result. If omitted, prints to stdout.
* ``--model``: SentenceTransformer model name (default: ``all-MiniLM-L6-v2``)
* ``--threshold``: Cosine similarity threshold (0.0 - 1.0). Higher means stricter matching. Default: ``0.9``.
* ``--language-key``: If objects have a specific language field, you can specify it.

Python API
----------

You can use the ``deduplicate`` function directly in your Python code:

.. code-block:: python

   import toonverter as toon

   data = {
       "items": [
           "Apple",
           "Banana", 
           "Fuji Apple",  # Might be deduplicated against "Apple" depending on threshold
           "Orange"
       ]
   }

   # Deduplicate
   cleaned = toon.deduplicate(data, threshold=0.8)

Advanced Usage: Custom Text Extraction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For complex objects, you might want to control exactly what text is used for embedding comparison. You can use the ``SemanticDeduplicator`` class directly:

.. code-block:: python

   from toonverter.analysis.deduplication import SemanticDeduplicator

   def my_text_extractor(item):
       # Only compare based on title and description
       return f"{item.get('title', '')} {item.get('description', '')}"

   deduper = SemanticDeduplicator(text_extraction_func=my_text_extractor)
   cleaned_data = deduper.optimize(data)

Performance
-----------

* **Exact Match**: The system always performs an O(N) hash-based exact deduplication first.
* **Semantic**: This is O(N^2) within each list. For very large lists (>10k items), this can be slow. It is recommended for document chunks, tag lists, or moderate-sized datasets.
