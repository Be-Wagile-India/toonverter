"""Instructor Integration for toonverter.

Provides efficient TOON serialization for Instructor response models and validation results.
Perfect for structured LLM output workflows, response caching, and schema documentation.

Key benefits:
- 40-60% token savings for response caching
- Preserves Pydantic model structure and validation
- Efficient storage for response collections
- Seamless integration with Instructor workflows

Install dependencies:
    pip install toonverter[instructor]

Basic usage:
    from toonverter.integrations.instructor_integration import response_to_toon, toon_to_response

    # Convert response to TOON
    toon_str = response_to_toon(response_model)

    # Convert back to response
    response = toon_to_response(toon_str, ResponseModel)
"""

from collections.abc import Iterator
from typing import Any

from toonverter.core.exceptions import ConversionError
from toonverter.core.spec import ToonDecodeOptions, ToonEncodeOptions
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


try:
    from pydantic import BaseModel, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


def _check_pydantic():
    """Check if Pydantic is available."""
    if not PYDANTIC_AVAILABLE:
        msg = "Pydantic is not installed. Install with: pip install toonverter[instructor]"
        raise ImportError(msg)


# =============================================================================
# RESPONSE MODEL CONVERSION
# =============================================================================


def response_to_toon(
    response: "BaseModel", include_metadata: bool = False, options: ToonEncodeOptions | None = None
) -> str:
    """Convert Instructor response model (Pydantic) to TOON format.

    Args:
        response: Pydantic BaseModel instance from Instructor
        include_metadata: Include model metadata (class name, schema)
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        >>> user = User(name="Alice", age=30)
        >>> toon = response_to_toon(user)
        >>> print(toon)
        name: Alice
        age: 30
    """
    _check_pydantic()

    try:
        encoder = ToonEncoder(options)

        if include_metadata:
            data = {"_model": response.__class__.__name__, "_data": response.model_dump()}
        else:
            data = response.model_dump()

        return encoder.encode(data)

    except Exception as e:
        msg = f"Failed to convert response to TOON: {e}"
        raise ConversionError(msg)


def toon_to_response(
    toon_str: str, model_class: type["BaseModel"], options: ToonDecodeOptions | None = None
) -> "BaseModel":
    """Convert TOON format to Instructor response model (Pydantic).

    Args:
        toon_str: TOON formatted string
        model_class: Pydantic model class to instantiate
        options: TOON decoding options

    Returns:
        Pydantic BaseModel instance

    Example:
        >>> toon = "name: Alice\\nage: 30"
        >>> user = toon_to_response(toon, User)
        >>> print(user.name)
        Alice
    """
    _check_pydantic()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        # Extract data if metadata wrapper exists
        if isinstance(data, dict) and "_data" in data:
            data = data["_data"]

        # Validate and instantiate model
        return model_class(**data)

    except ValidationError as e:
        msg = f"Validation failed: {e}"
        raise ConversionError(msg)
    except Exception as e:
        msg = f"Failed to convert TOON to response: {e}"
        raise ConversionError(msg)


# =============================================================================
# BULK OPERATIONS
# =============================================================================


def bulk_responses_to_toon(
    responses: list["BaseModel"],
    include_metadata: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert multiple Instructor responses to TOON array format.

    Args:
        responses: List of Pydantic BaseModel instances
        include_metadata: Include model metadata
        options: TOON encoding options

    Returns:
        TOON formatted string with array of responses

    Example:
        >>> users = [User(name="Alice", age=30), User(name="Bob", age=25)]
        >>> toon = bulk_responses_to_toon(users)
        >>> print(toon)
        [2]:
          - name: Alice
            age: 30
          - name: Bob
            age: 25
    """
    _check_pydantic()

    try:
        encoder = ToonEncoder(options)

        if include_metadata:
            data_list = [
                {"_model": r.__class__.__name__, "_data": r.model_dump()} for r in responses
            ]
        else:
            data_list = [r.model_dump() for r in responses]

        return encoder.encode(data_list)

    except Exception as e:
        msg = f"Failed to convert responses to TOON: {e}"
        raise ConversionError(msg)


def bulk_toon_to_responses(
    toon_str: str, model_class: type["BaseModel"], options: ToonDecodeOptions | None = None
) -> list["BaseModel"]:
    """Convert TOON array format to multiple Instructor responses.

    Args:
        toon_str: TOON formatted string (array)
        model_class: Pydantic model class to instantiate
        options: TOON decoding options

    Returns:
        List of Pydantic BaseModel instances

    Example:
        >>> toon = "[2]:\\n  - name: Alice\\n    age: 30\\n  - name: Bob\\n    age: 25"
        >>> users = bulk_toon_to_responses(toon, User)
        >>> len(users)
        2
    """
    _check_pydantic()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            msg = "Expected TOON array format"
            raise ConversionError(msg)

        responses = []
        for data in data_list:
            # Extract data if metadata wrapper exists
            if isinstance(data, dict) and "_data" in data:
                data = data["_data"]
            responses.append(model_class(**data))

        return responses

    except ValidationError as e:
        msg = f"Validation failed: {e}"
        raise ConversionError(msg)
    except Exception as e:
        msg = f"Failed to convert TOON to responses: {e}"
        raise ConversionError(msg)


def stream_responses_to_toon(
    responses: list["BaseModel"],
    chunk_size: int = 100,
    include_metadata: bool = False,
    options: ToonEncodeOptions | None = None,
) -> Iterator[str]:
    """Stream large response collections to TOON in chunks.

    Memory-efficient for processing large datasets.

    Args:
        responses: List of Pydantic BaseModel instances
        chunk_size: Number of responses per chunk
        include_metadata: Include model metadata
        options: TOON encoding options

    Yields:
        TOON formatted strings (one per chunk)

    Example:
        >>> responses = [User(name=f"User{i}", age=20+i) for i in range(1000)]
        >>> for chunk_toon in stream_responses_to_toon(responses, chunk_size=100):
        ...     save_chunk(chunk_toon)  # Process 100 responses at a time
    """
    _check_pydantic()

    try:
        encoder = ToonEncoder(options)

        for i in range(0, len(responses), chunk_size):
            chunk = responses[i : i + chunk_size]

            if include_metadata:
                data_list = [
                    {"_model": r.__class__.__name__, "_data": r.model_dump()} for r in chunk
                ]
            else:
                data_list = [r.model_dump() for r in chunk]

            yield encoder.encode(data_list)

    except Exception as e:
        msg = f"Failed to stream responses to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# SCHEMA OPERATIONS
# =============================================================================


def schema_to_toon(model_class: type["BaseModel"], options: ToonEncodeOptions | None = None) -> str:
    """Export Pydantic model schema to TOON format.

    Useful for documentation and schema sharing.

    Args:
        model_class: Pydantic model class
        options: TOON encoding options

    Returns:
        TOON formatted string with schema

    Example:
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int
        ...     email: str
        >>> toon = schema_to_toon(User)
    """
    _check_pydantic()

    try:
        encoder = ToonEncoder(options)
        schema = model_class.model_json_schema()
        return encoder.encode(schema)

    except Exception as e:
        msg = f"Failed to convert schema to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# VALIDATION RESULTS
# =============================================================================


def validation_results_to_toon(
    results: list[dict[str, Any]], options: ToonEncodeOptions | None = None
) -> str:
    """Convert validation results to TOON format.

    Useful for storing validation errors and debugging.

    Args:
        results: List of validation result dictionaries
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> results = [
        ...     {"field": "age", "error": "must be positive", "value": -5},
        ...     {"field": "email", "error": "invalid format", "value": "not-an-email"}
        ... ]
        >>> toon = validation_results_to_toon(results)
    """
    try:
        encoder = ToonEncoder(options)
        return encoder.encode(results)

    except Exception as e:
        msg = f"Failed to convert validation results to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# INSTRUCTOR-SPECIFIC OPERATIONS
# =============================================================================


def extraction_batch_to_toon(
    extractions: list["BaseModel"],
    source_metadata: dict[str, Any] | None = None,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert batch extraction results to TOON format.

    Optimized for Instructor's batch extraction workflows.

    Args:
        extractions: List of extracted Pydantic models
        source_metadata: Optional metadata about the source
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> extractions = [
        ...     Entity(name="Apple", type="company"),
        ...     Entity(name="Google", type="company")
        ... ]
        >>> toon = extraction_batch_to_toon(
        ...     extractions,
        ...     source_metadata={"document": "tech_news.txt", "date": "2024-01-15"}
        ... )
    """
    _check_pydantic()

    try:
        encoder = ToonEncoder(options)

        data = {"extractions": [ex.model_dump() for ex in extractions], "count": len(extractions)}

        if source_metadata:
            data["metadata"] = source_metadata

        return encoder.encode(data)

    except Exception as e:
        msg = f"Failed to convert extraction batch to TOON: {e}"
        raise ConversionError(msg)


def toon_to_extraction_batch(
    toon_str: str, model_class: type["BaseModel"], options: ToonDecodeOptions | None = None
) -> dict[str, Any]:
    """Convert TOON format to extraction batch results.

    Args:
        toon_str: TOON formatted string
        model_class: Pydantic model class for extractions
        options: TOON decoding options

    Returns:
        Dictionary with 'extractions', 'count', and optional 'metadata'

    Example:
        >>> result = toon_to_extraction_batch(toon, Entity)
        >>> print(f"Extracted {result['count']} entities")
        >>> for entity in result['extractions']:
        ...     print(entity.name)
    """
    _check_pydantic()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if not isinstance(data, dict) or "extractions" not in data:
            msg = "Expected extraction batch format"
            raise ConversionError(msg)

        # Convert extractions to model instances
        extractions = [model_class(**ex_data) for ex_data in data["extractions"]]

        return {
            "extractions": extractions,
            "count": data.get("count", len(extractions)),
            "metadata": data.get("metadata", {}),
        }

    except ValidationError as e:
        msg = f"Validation failed: {e}"
        raise ConversionError(msg)
    except Exception as e:
        msg = f"Failed to convert TOON to extraction batch: {e}"
        raise ConversionError(msg)


# =============================================================================
# RESPONSE CACHING
# =============================================================================


def cache_response(
    response: "BaseModel",
    cache_key: str,
    ttl: int | None = None,
    options: ToonEncodeOptions | None = None,
) -> dict[str, Any]:
    """Create a cacheable TOON representation of response.

    Args:
        response: Pydantic BaseModel instance
        cache_key: Unique identifier for this response
        ttl: Time-to-live in seconds (optional)
        options: TOON encoding options

    Returns:
        Dictionary with cache metadata and TOON data

    Example:
        >>> user = User(name="Alice", age=30)
        >>> cache_entry = cache_response(user, "user:123", ttl=3600)
        >>> # Store cache_entry in Redis/Memcached/etc.
    """
    _check_pydantic()

    try:
        import time

        toon_data = response_to_toon(response, include_metadata=True, options=options)

        cache_entry = {
            "key": cache_key,
            "model": response.__class__.__name__,
            "toon": toon_data,
            "cached_at": int(time.time()),
        }

        if ttl:
            cache_entry["ttl"] = ttl
            cache_entry["expires_at"] = int(time.time()) + ttl

        return cache_entry

    except Exception as e:
        msg = f"Failed to create cache entry: {e}"
        raise ConversionError(msg)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "bulk_responses_to_toon",
    "bulk_toon_to_responses",
    "cache_response",
    "extraction_batch_to_toon",
    "response_to_toon",
    "schema_to_toon",
    "stream_responses_to_toon",
    "toon_to_extraction_batch",
    "toon_to_response",
    "validation_results_to_toon",
]
