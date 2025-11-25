Redis Integration
=================

``toonverter`` provides an integration for Redis, specifically designed to optimize data retrieval
for Large Language Models (LLMs) by encoding Redis JSON and Hash data into the compact TOON format.
This is particularly useful in RAG (Retrieval Augmented Generation) pipelines where reducing
token count of retrieved metadata is crucial for cost and performance.

.. autoclass:: toonverter.integrations.RedisToonWrapper
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Quick Start
-----------

Here's how to use the ``RedisToonWrapper`` to retrieve and optimize data from Redis:

.. code-block:: python

   import redis
   from toonverter.integrations import RedisToonWrapper

   # 1. Initialize Redis client and ToonRedisWrapper
   #    Make sure your Redis server is running (e.g., via Docker: docker run -p 6379:6379 redislabs/rejson)
   r = redis.Redis(decode_responses=True) # decode_responses=True for string results
   wrapper = RedisToonWrapper(r)

   # 2. Store some JSON data in Redis
   r.json().set("doc:1", "$", {"title": "AI in 2024", "author": "Alice", "text": "AI is evolving fast..."})
   r.json().set("doc:2", "$", {"title": "Quantum Computing", "author": "Bob", "text": "Quantum computers promise..."})
   r.json().set("user:1", "$", {"name": "Alice", "email": "alice@example.com", "preferences": {"theme": "dark"}})

   # 3. Retrieve a single JSON document as TOON
   toon_doc1 = wrapper.get_json("doc:1")
   print(f"\nTOON for doc:1:\n{toon_doc1}")

   # 4. Retrieve multiple JSON documents as a compact TOON array
   #    This leverages TOON's tabular format for efficiency if schemas match.
   toon_docs_batch = wrapper.mget_json(["doc:1", "doc:2"])
   print(f"\nTOON for doc:1, doc:2 (batch):\n{toon_docs_batch}")

   # 5. Store and retrieve a Redis Hash as TOON
   r.hset("config:app", mapping={
       "version": "1.0",
       "env": "production",
       "debug": "false",
   })
   toon_hash_config = wrapper.hgetall("config:app")
   print(f"\nTOON for config:app (hash):\n{toon_hash_config}")

   # 6. Optimize search results (e.g., from a vector database search)
   #    Imagine these are results from RedisVL or another vector search library
   search_results_raw = [
       {"id": "doc:1", "score": 0.98, "vector_id": "vec1", "content": "AI is evolving fast..."},
       {"id": "doc:2", "score": 0.95, "vector_id": "vec2", "content": "Quantum computers promise..."},
       {"id": "doc:3", "score": 0.75, "vector_id": "vec3", "content": "Another irrelevant doc..."},
   ]
   # We only want to send relevant fields to the LLM to save tokens
   optimized_results_toon = wrapper.search_results(
       search_results_raw, fields=["id", "score", "content"], indent=0 # Force compact
   )
   print(f"\nOptimized search results (TOON):\n{optimized_results_toon}")

   # Example of LLM prompt integration
   llm_prompt = f"""Analyze the following retrieved documents (TOON format):
   {optimized_results_toon}

   Based on this, answer the user's query: "What are the main trends in AI?"""
   print(f"\nLLM Prompt Snippet:\n{llm_prompt[:200]}...")

   # Cleanup
   r.delete("doc:1", "doc:2", "user:1", "config:app")

API Reference
-------------

