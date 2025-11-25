"""Redis integration for TOON Converter.

This module provides utilities to optimize data retrieved from Redis,
particularly for RAG (Retrieval Augmented Generation) scenarios where
metadata overhead is high. It supports Redis JSON and Hash types.
"""

from typing import Any, cast

from toonverter.core import registry
from toonverter.core.spec import ToonEncodeOptions


try:
    from redis import Redis
except ImportError:
    Redis = Any  # type: ignore


class RedisToonWrapper:
    """Wrapper for Redis client to retrieve data in TOON format.

    This class wraps a standard Redis client and adds methods to retrieve
    data directly as TOON-encoded strings, optimizing token usage for
    LLM contexts.
    """

    def __init__(self, client: "Redis") -> None:
        """Initialize wrapper.

        Args:
            client: Standard redis.Redis client instance
        """
        self.client = client
        self.adapter = registry.get("toon")

    def get_json(self, key: str, **options: Any) -> str | None:
        """Retrieve Redis JSON value as TOON string.

        Args:
            key: Redis key
            **options: Encoding options passed to TOON encoder

        Returns:
            TOON-encoded string or None if key doesn't exist
        """
        data = self.client.json().get(key)
        if data is None:
            return None
        return self._encode(data, **options)

    def mget_json(self, keys: list[str], **options: Any) -> str:
        """Retrieve multiple Redis JSON values as a TOON array.

        This is highly efficient for RAG. If the JSON documents share the
        same schema, TOON will automatically format them as a tabular array,
        saving significant tokens compared to a list of JSON objects.

        Args:
            keys: List of Redis keys
            **options: Encoding options passed to TOON encoder

        Returns:
            TOON-encoded string representing the list of documents
        """
        # Fetch all JSONs in one go (pipeline could be used, but json().mget is standard)
        # Note: redis-py's json().mget might vary by version, usage path:
        # r.json().mget(keys) usually returns a list of objects.
        try:
            data = self.client.json().mget(keys, ".")
        except AttributeError:
            # Fallback for older clients or different implementations
            pipe = self.client.pipeline()
            for key in keys:
                pipe.json().get(key)
            data = pipe.execute()

        # Filter out None values for missing keys
        valid_data = [item for item in data if item is not None]

        if not valid_data:
            return "[]"

        return self._encode(valid_data, **options)

    def hgetall(self, key: str, **options: Any) -> str | None:
        """Retrieve Redis Hash as TOON object.

        Args:
            key: Redis key
            **options: Encoding options

        Returns:
            TOON-encoded string or None
        """
        data = self.client.hgetall(key)
        if not data:
            return None

        # Redis hashes return byte strings by default if decode_responses=False
        # We need to ensure they are decoded for the encoder
        decoded_data = self._decode_hash(cast("dict[Any, Any]", data))
        return self._encode(decoded_data, **options)

    def search_results(
        self, results: list[Any], fields: list[str] | None = None, **options: Any
    ) -> str:
        """Optimize a list of search results (e.g. from RedisVL).

        Args:
            results: List of result objects (dicts or objects with __dict__)
            fields: Optional list of fields to include (projection)
            **options: Encoding options

        Returns:
            TOON-encoded tabular string
        """
        processed = []
        for res in results:
            # Handle different result types (dict or object)
            item = res if isinstance(res, dict) else res.__dict__

            if fields:
                item = {k: v for k, v in item.items() if k in fields}

            processed.append(item)

        if not processed:
            return "[]"

        # Force tabular preset if not specified, as search results are usually uniform
        if "indent" not in options:
            options["indent"] = 0  # Compact

        return self._encode(processed, **options)

    def _encode(self, data: Any, **options: Any) -> str:
        """Helper to encode data with options."""
        # We construct ToonEncodeOptions manually to support advanced features
        # if passed in kwargs, or let the adapter handle it.
        # Using the registry's encode method logic directly via adapter.

        # Convert generic kwargs to ToonEncodeOptions if needed
        # For now, passing generic EncodeOptions is standard in the library
        from toonverter.core.types import EncodeOptions
        from toonverter.encoders.toon_encoder import _convert_options

        encode_opts = EncodeOptions(**options)
        toon_opts = _convert_options(encode_opts)

        return self.adapter.encode(data, cast("Any", toon_opts))

    def _decode_hash(self, data: dict[Any, Any]) -> dict[str, Any]:
        """Ensure hash keys/values are strings."""
        decoded = {}
        for k, v in data.items():
            key = k.decode("utf-8") if isinstance(k, bytes) else str(k)
            value = v.decode("utf-8") if isinstance(v, bytes) else v
            decoded[key] = value
        return decoded
