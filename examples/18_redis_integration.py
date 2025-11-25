#!/usr/bin/env python3
"""
Example 18: Redis Integration for RAG Optimization

Demonstrates:
- Retrieving JSON documents from Redis as optimized TOON
- Using bulk retrieval (mget) for tabular optimization
- Handling Redis Hashes
- Optimizing search results from vector databases
"""

try:
    import redis
    from toonverter.integrations import RedisToonWrapper
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Install redis: pip install toonverter[redis]")

import toonverter as toon


def main():
    print("=" * 60)
    print("Example 18: Redis Integration for RAG Optimization")
    print("=" * 60)

    if not REDIS_AVAILABLE:
        print("\nPlease install: pip install toonverter[redis]")
        return

    # Attempt to connect to a local Redis instance
    # If not available, we'll simulate the behavior with a Mock
    try:
        client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        client.ping()
        print("\nConnected to local Redis.")
    except (redis.ConnectionError, NameError):
        print("\nCould not connect to Redis. Using MockRedis for demonstration.")
        
        class MockRedis:
            def __init__(self):
                self._data = {}
                self._hashes = {}
                
            class Json:
                def __init__(self, parent):
                    self.parent = parent
                    
                def get(self, key):
                    return self.parent._data.get(key)
                    
                def mget(self, keys, path="."):
                    return [self.parent._data.get(k) for k in keys]
                
                def set(self, key, path, value):
                    self.parent._data[key] = value

            def json(self):
                return self.Json(self)
                
            def hset(self, key, mapping):
                self._hashes[key] = mapping
                
            def hgetall(self, key):
                return self._hashes.get(key)
                
            def delete(self, *keys):
                for k in keys:
                    self._data.pop(k, None)
                    self._hashes.pop(k, None)

        client = MockRedis()

    # Initialize the TOON wrapper
    wrapper = RedisToonWrapper(client)

    # ---------------------------------------------------------
    # 1. Single Document Retrieval
    # ---------------------------------------------------------
    print("\n--- 1. Single Document Retrieval ---")
    
    doc1 = {
        "title": "TOON Specification",
        "version": "2.0",
        "author": "Danesh Patel",
        "tags": ["format", "optimization", "llm"],
        "content": "TOON is a token-optimized object notation..."
    }
    
    # Store in Redis
    client.json().set("doc:1", "$", doc1)
    
    # Retrieve as TOON
    toon_doc = wrapper.get_json("doc:1")
    print("\nRetrieved 'doc:1' as TOON:")
    print(toon_doc)
    
    # ---------------------------------------------------------
    # 2. Bulk Retrieval (Tabular Optimization)
    # ---------------------------------------------------------
    print("\n--- 2. Bulk Retrieval (Tabular Optimization) ---")
    
    doc2 = {
        "title": "Redis Integration",
        "version": "1.0",
        "author": "Danesh Patel",
        "tags": ["database", "caching"],
        "content": "Redis is an in-memory data store..."
    }
    
    client.json().set("doc:2", "$", doc2)
    
    # Retrieve both documents
    # TOON automatically detects the shared schema and uses tabular format
    toon_batch = wrapper.mget_json(["doc:1", "doc:2"])
    
    print("\nRetrieved 'doc:1' and 'doc:2' as TOON batch:")
    print(toon_batch)
    
    # Analyze savings
    import json
    json_str = json.dumps([doc1, doc2])
    
    print("\nAnalysis:")
    print(f"JSON Length: {len(json_str)} chars")
    print(f"TOON Length: {len(toon_batch)} chars")
    print(f"Character Savings: {((len(json_str) - len(toon_batch)) / len(json_str) * 100):.1f}%")

    # ---------------------------------------------------------
    # 3. Redis Hash Support
    # ---------------------------------------------------------
    print("\n--- 3. Redis Hash Support ---")
    
    user_config = {
        "theme": "dark",
        "notifications": "true",
        "language": "en-US",
        "max_tokens": "1000"
    }
    
    client.hset("user:config", mapping=user_config)
    
    # Retrieve Hash as TOON
    toon_hash = wrapper.hgetall("user:config")
    
    print("\nRetrieved Hash 'user:config' as TOON:")
    print(toon_hash)

    # ---------------------------------------------------------
    # 4. Search Results Optimization
    # ---------------------------------------------------------
    print("\n--- 4. Search Results Optimization ---")
    
    # Simulate search results from a vector database (e.g. RedisVL)
    results = [
        {"id": "doc:1", "score": 0.98, "content": "TOON is..."},
        {"id": "doc:2", "score": 0.95, "content": "Redis is..."},
        {"id": "doc:3", "score": 0.82, "content": "Python is."}
    ]
    
    # Optimize results for LLM context
    # Use 'indent=0' for maximum compactness
    optimized_results = wrapper.search_results(
        results, 
        fields=["id", "score"],  # Only include relevant fields
        indent=0
    )
    
    print("\nOptimized Search Results (Compact Table):")
    print(optimized_results)
    
    # Cleanup
    client.delete("doc:1", "doc:2", "user:config")


if __name__ == "__main__":
    main()
