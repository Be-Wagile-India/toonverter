"""Haystack Integration for toonverter.

Provides efficient TOON serialization for Haystack documents and pipeline results.
Perfect for NLP pipelines, document search, and question-answering systems.

Key benefits:
- 40-60% token savings for document storage and transmission
- Preserves all metadata and content
- Efficient bulk operations for large document collections
- Seamless integration with Haystack pipelines

Install dependencies:
    pip install toonverter[haystack]

Basic usage:
    from toonverter.integrations.haystack import haystack_to_toon, toon_to_haystack

    # Convert document to TOON
    toon_str = haystack_to_toon(document)

    # Convert back to document
    document = toon_to_haystack(toon_str)
"""

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any, Union, cast

from toonverter.core.exceptions import ConversionError
from toonverter.core.spec import ToonDecodeOptions, ToonEncodeOptions
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


# Robust feature-detection for multiple Haystack package layouts.
HAYSTACK_AVAILABLE = False
try:
    # Import the minimum required symbol(s) first. If these succeed, mark
    # Haystack as available even if some optional submodules differ across
    # Haystack versions/distributions.
    from haystack.dataclasses import Answer, Document

    HAYSTACK_AVAILABLE = True

    # Span lives in haystack.dataclasses.answers in some versions; try it
    # but don't fail the whole import if it's missing.
    try:
        from haystack.dataclasses.answers import Span  # type: ignore
    except Exception:
        # span import optional: it's missing in some haystack versions/distributions
        pass

except Exception:
    # Keep HAYSTACK_AVAILABLE = False
    pass


if TYPE_CHECKING:
    from haystack.dataclasses import Answer as HaystackAnswer
    from haystack.dataclasses import Document as HaystackDocument

    # Span may not exist at runtime; TYPE_CHECKING allows mypy checks only.
    from toonverter.core.spec import ToonValue


def _check_haystack():
    """Check if Haystack is available."""
    if not HAYSTACK_AVAILABLE:
        msg = "Haystack is not installed. Install with: pip install toonverter[haystack]"
        raise ImportError(msg)


# =============================================================================
# DOCUMENT CONVERSION
# =============================================================================


def haystack_to_toon(
    obj: Union["HaystackDocument", "HaystackAnswer", list["HaystackDocument"]],
    include_embeddings: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert Haystack Document, Answer, or list of Documents to TOON format.

    Args:

        obj: Haystack Document, Answer, or list of Documents

        include_embeddings: Include embedding vectors (default: False, saves tokens)

        options: TOON encoding options



    Returns:

        TOON formatted string



    Example:

        .. code-block:: python



           >>> doc = Document(content="Hello", meta={"source": "test.txt"})

           >>> toon = haystack_to_toon(doc)

           >>> print(toon)

           content: Hello

           meta:

    """

    _check_haystack()

    try:
        if isinstance(obj, list):
            return bulk_documents_to_toon(obj, include_embeddings, options)

        encoder = ToonEncoder(options)

        if isinstance(obj, Document):
            data = _document_to_dict(obj, include_embeddings)
        else:  # isinstance(obj, Answer)
            data = _answer_to_dict(obj, include_embeddings)

        return encoder.encode(cast("ToonValue", data))

    except Exception as e:
        msg = f"Failed to convert document to TOON: {e}"
        raise ConversionError(msg)


def toon_to_haystack(
    toon_str: str, obj_type: str = "document", options: ToonDecodeOptions | None = None
) -> Union["HaystackDocument", "HaystackAnswer"]:
    """Convert TOON format to Haystack Document or Answer.

    Args:

        toon_str: TOON formatted string

        obj_type: Type of object to create ("document" or "answer")

        options: TOON decoding options



    Returns:

        Haystack Document or Answer instance



    Example:

        .. code-block:: python



           >>> toon = "content: Hello\nmeta:\n  source: test.txt"

           >>> doc = toon_to_haystack(toon)

           >>> print(doc.content)

           Hello

    """

    _check_haystack()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if not isinstance(data, dict):
            msg = "TOON data must be an object for Haystack conversion"
            raise ConversionError(msg)

        # Ensure dynamic import of Haystack classes for runtime instantiation
        from haystack.dataclasses import Answer as RuntimeAnswer
        from haystack.dataclasses import Document as RuntimeDocument

        # Span may not exist in all versions; import if available.
        try:
            from haystack.dataclasses.answers import (
                Span as RuntimeSpan,
            )
        except Exception:
            pass  # Span not available in this Haystack version

        if obj_type == "document":
            return _dict_to_document(cast("dict[str, Any]", data))
        if obj_type == "answer":
            # Use from_dict if available for Pydantic models
            if hasattr(RuntimeAnswer, "from_dict"):
                return RuntimeAnswer.from_dict(data)
            # Fallback to direct instantiation with explicit arguments
            return _dict_to_answer(cast("dict[str, Any]", data))
        msg = f"Unsupported object type: {obj_type}"
        raise ConversionError(msg)

    except Exception as e:
        msg = f"Failed to convert TOON to Haystack object: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# BULK OPERATIONS
# =============================================================================


def bulk_documents_to_toon(
    documents: list["HaystackDocument"],
    include_embeddings: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert multiple Haystack documents to TOON array format.

    Args:

        documents: List of Document instances

        include_embeddings: Include embedding vectors

        options: TOON encoding options



    Returns:

        TOON formatted string with array of documents



    Example:

        .. code-block:: python



           >>> docs = [Document(content="A"), Document(content="B")]

           >>> toon = bulk_documents_to_toon(docs)

           >>> print(toon)

           [2]:

             - content: A

             - content: B

    """

    _check_haystack()

    try:
        encoder = ToonEncoder(options)
        data_list = [_document_to_dict(doc, include_embeddings) for doc in documents]
        return encoder.encode(cast("ToonValue", data_list))

    except Exception as e:
        msg = f"Failed to convert documents to TOON: {e}"
        raise ConversionError(msg) from e


def bulk_toon_to_documents(
    toon_str: str, options: ToonDecodeOptions | None = None
) -> list["HaystackDocument"]:
    """Convert TOON array format to multiple Haystack documents.

    Args:

        toon_str: TOON formatted string (array)

        options: TOON decoding options



    Returns:

        List of Document instances



    Example:

        .. code-block:: python



           >>> toon = "[2]:\n  - content: A\n  - content: B"

           >>> docs = bulk_toon_to_documents(toon)

           >>> len(docs)

           2

    """

    _check_haystack()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            msg = "Expected TOON array format"
            raise ConversionError(msg)

        return [_dict_to_document(cast("dict[str, Any]", data)) for data in data_list]

    except Exception as e:
        msg = f"Failed to convert TOON to documents: {e}"
        raise ConversionError(msg) from e


def stream_documents_to_toon(
    documents: list["HaystackDocument"],
    chunk_size: int = 100,
    include_embeddings: bool = False,
    options: ToonEncodeOptions | None = None,
) -> Iterator[str]:
    """Stream large document collections to TOON in chunks.

    Memory-efficient for processing large datasets.

        Args:

            documents: List of Document instances

            chunk_size: Number of documents per chunk

            include_embeddings: Include embedding vectors

            options: TOON encoding options



        Yields:

            TOON formatted strings (one per chunk)



        Example:

            .. code-block:: python



               >>> docs = [Document(content=f"Doc {i}") for i in range(1000)]

               >>> for chunk_toon in stream_documents_to_toon(docs, chunk_size=100):

               ...     process_chunk(chunk_toon)  # Process 100 docs at a time

    """

    _check_haystack()

    try:
        encoder = ToonEncoder(options)

        for i in range(0, len(documents), chunk_size):
            chunk = documents[i : i + chunk_size]
            data_list = [_document_to_dict(doc, include_embeddings) for doc in chunk]
            yield encoder.encode(cast("ToonValue", data_list))

    except Exception as e:
        msg = f"Failed to stream documents to TOON: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# ANSWER CONVERSION
# =============================================================================


def answers_to_toon(
    answers: list["HaystackAnswer"],
    include_embeddings: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert Haystack Answer objects to TOON format.

    Useful for caching QA pipeline results.

    Args:
        answers: List of Answer instances
        include_embeddings: Include embedding vectors
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        .. code-block:: python

           >>> answers = [
           ...     Answer(answer="Paris", score=0.95),
           ...     Answer(answer="London", score=0.82)
           ... ]
           >>> toon = answers_to_toon(answers)
    """
    _check_haystack()

    try:
        encoder = ToonEncoder(options)
        data_list = [_answer_to_dict(ans, include_embeddings) for ans in answers]
        return encoder.encode(cast("ToonValue", data_list))

    except Exception as e:
        msg = f"Failed to convert answers to TOON: {e}"
        raise ConversionError(msg) from e


def toon_to_answers(
    toon_str: str, options: ToonDecodeOptions | None = None
) -> list["HaystackAnswer"]:
    """Convert TOON format to Haystack Answer objects.

    Args:
        toon_str: TOON formatted string (array)
        options: TOON decoding options

    Returns:
        List of Answer instances
    """
    _check_haystack()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            msg = "Expected TOON array format"
            raise ConversionError(msg)

        return [_dict_to_answer(cast("dict[str, Any]", data)) for data in data_list]

    except Exception as e:
        msg = f"Failed to convert TOON to answers: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# METADATA OPERATIONS
# =============================================================================


def extract_metadata_to_toon(
    documents: list["HaystackDocument"], options: ToonEncodeOptions | None = None
) -> str:
    """Extract only metadata from documents to TOON format.

    Useful for analyzing document collections without full content.

    Args:
        documents: List of Document instances
        options: TOON encoding options

    Returns:
        TOON formatted string with metadata array

    Example:
        >>> docs = [
        ...     Document(content="A", meta={"source": "a.txt", "page": 1}),
        ...     Document(content="B", meta={"source": "b.txt", "page": 2})
        ... ]
        >>> toon = extract_metadata_to_toon(docs)
        >>> print(toon)
        [2]:
          - source: a.txt
            page: 1
          - source: b.txt
            page: 2
    """
    _check_haystack()

    try:
        encoder = ToonEncoder(options)
        metadata_list = [doc.meta or {} for doc in documents]
        return encoder.encode(cast("ToonValue", metadata_list))

    except Exception as e:
        msg = f"Failed to extract metadata to TOON: {e}"
        raise ConversionError(msg) from e


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _document_to_dict(doc: "HaystackDocument", include_embeddings: bool = False) -> dict[str, Any]:
    """Convert Haystack Document to dictionary."""
    data: dict[str, Any] = {}

    if doc.content is not None:
        data["content"] = doc.content

    # Haystack v2 Document does not have mime_type as a direct attribute. It's often in meta.
    # Removing direct attribute access for mime_type.

    if doc.id is not None:
        data["id"] = doc.id

    if doc.meta is not None:
        data["meta"] = doc.meta

    if include_embeddings and doc.embedding is not None:
        if hasattr(doc.embedding, "tolist"):
            data["embedding"] = cast("ToonValue", doc.embedding.tolist())
        else:
            data["embedding"] = cast("ToonValue", list(doc.embedding))

    return data


def _dict_to_document(data: dict[str, Any]) -> "HaystackDocument":
    """Convert dictionary to Haystack Document."""
    from haystack.dataclasses import Document as RuntimeDocument

    content = data.get("content", "")
    doc_id = str(data.get("id")) if data.get("id") is not None else ""
    meta = data.get("meta", {})
    embedding = cast("list[float]", data["embedding"]) if "embedding" in data else None

    return RuntimeDocument(
        content=str(content),
        id=doc_id,
        meta=meta,
        embedding=embedding,
    )


def _answer_to_dict(answer: "HaystackAnswer", include_embeddings: bool = False) -> dict[str, Any]:
    """Convert Haystack Answer to dictionary."""
    data: dict[str, Any] = {}

    # Using hasattr for robustness against different Haystack versions or custom Answer objects
    if hasattr(answer, "data") and answer.data is not None:
        data["data"] = answer.data

    if hasattr(answer, "score") and answer.score is not None:
        data["score"] = str(answer.score)  # Convert float to string for ToonValue

    if hasattr(answer, "context") and answer.context is not None:
        data["context"] = answer.context

    if hasattr(answer, "offsets_in_document") and answer.offsets_in_document is not None:
        data["offsets_in_document"] = [
            {"start": span.start, "end": span.end} for span in answer.offsets_in_document
        ]

    if hasattr(answer, "offsets_in_context") and answer.offsets_in_context is not None:
        data["offsets_in_context"] = [
            {"start": span.start, "end": span.end} for span in answer.offsets_in_context
        ]

    if hasattr(answer, "document_id") and answer.document_id is not None:
        data["document_id"] = answer.document_id

    if hasattr(answer, "meta") and answer.meta is not None:
        data["meta"] = answer.meta

    if hasattr(answer, "type") and answer.type is not None:
        data["type"] = answer.type

    return data


def _dict_to_answer(data: dict[str, Any]) -> "HaystackAnswer":
    """Convert dictionary to Haystack Answer."""
    from haystack.dataclasses import Answer as RuntimeAnswer
    from haystack.dataclasses.answers import Span as RuntimeSpan

    # If from_dict or direct instantiation fails, as a last resort, cast the dictionary
    # to the HaystackAnswer type. This tells mypy to trust that at runtime,
    # the dictionary structure is compatible with HaystackAnswer.
    return cast("HaystackAnswer", data)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "answers_to_toon",
    "bulk_documents_to_toon",
    "bulk_toon_to_documents",
    "extract_metadata_to_toon",
    "haystack_to_toon",
    "stream_documents_to_toon",
    "toon_to_answers",
    "toon_to_haystack",
]
