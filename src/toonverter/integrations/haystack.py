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

from typing import Any, Dict, List, Optional, Iterator, Union
from ..encoders.toon_encoder import ToonEncoder
from ..decoders.toon_decoder import ToonDecoder
from ..core.spec import ToonEncodeOptions, ToonDecodeOptions
from ..core.exceptions import ConversionError

try:
    from haystack import Document
    from haystack.schema import Answer, Label, Span

    HAYSTACK_AVAILABLE = True
except ImportError:
    HAYSTACK_AVAILABLE = False


def _check_haystack():
    """Check if Haystack is available."""
    if not HAYSTACK_AVAILABLE:
        raise ImportError(
            "Haystack is not installed. "
            "Install with: pip install toonverter[haystack]"
        )


# =============================================================================
# DOCUMENT CONVERSION
# =============================================================================

def haystack_to_toon(
    obj: Union['Document', 'Answer'],
    include_embeddings: bool = False,
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert Haystack Document or Answer to TOON format.

    Args:
        obj: Haystack Document or Answer instance
        include_embeddings: Include embedding vectors (default: False, saves tokens)
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> doc = Document(content="Hello", meta={"source": "test.txt"})
        >>> toon = haystack_to_toon(doc)
        >>> print(toon)
        content: Hello
        meta:
          source: test.txt
    """
    _check_haystack()

    try:
        encoder = ToonEncoder(options)

        if isinstance(obj, Document):
            data = _document_to_dict(obj, include_embeddings)
        elif isinstance(obj, Answer):
            data = _answer_to_dict(obj, include_embeddings)
        else:
            raise ConversionError(f"Unsupported type: {type(obj)}")

        return encoder.encode(data)

    except Exception as e:
        raise ConversionError(f"Failed to convert Haystack object to TOON: {e}")


def toon_to_haystack(
    toon_str: str,
    obj_type: str = "document",
    options: Optional[ToonDecodeOptions] = None
) -> Union['Document', 'Answer']:
    """Convert TOON format to Haystack Document or Answer.

    Args:
        toon_str: TOON formatted string
        obj_type: Type of object to create ("document" or "answer")
        options: TOON decoding options

    Returns:
        Haystack Document or Answer instance

    Example:
        >>> toon = "content: Hello\\nmeta:\\n  source: test.txt"
        >>> doc = toon_to_haystack(toon)
        >>> print(doc.content)
        Hello
    """
    _check_haystack()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)

        if obj_type == "document":
            return _dict_to_document(data)
        elif obj_type == "answer":
            return _dict_to_answer(data)
        else:
            raise ConversionError(f"Unsupported object type: {obj_type}")

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to Haystack object: {e}")


# =============================================================================
# BULK OPERATIONS
# =============================================================================

def bulk_documents_to_toon(
    documents: List['Document'],
    include_embeddings: bool = False,
    options: Optional[ToonEncodeOptions] = None
) -> str:
    """Convert multiple Haystack documents to TOON array format.

    Args:
        documents: List of Document instances
        include_embeddings: Include embedding vectors
        options: TOON encoding options

    Returns:
        TOON formatted string with array of documents

    Example:
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
        return encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to convert documents to TOON: {e}")


def bulk_toon_to_documents(
    toon_str: str,
    options: Optional[ToonDecodeOptions] = None
) -> List['Document']:
    """Convert TOON array format to multiple Haystack documents.

    Args:
        toon_str: TOON formatted string (array)
        options: TOON decoding options

    Returns:
        List of Document instances

    Example:
        >>> toon = "[2]:\\n  - content: A\\n  - content: B"
        >>> docs = bulk_toon_to_documents(toon)
        >>> len(docs)
        2
    """
    _check_haystack()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            raise ConversionError("Expected TOON array format")

        return [_dict_to_document(data) for data in data_list]

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to documents: {e}")


def stream_documents_to_toon(
    documents: List['Document'],
    chunk_size: int = 100,
    include_embeddings: bool = False,
    options: Optional[ToonEncodeOptions] = None
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
        >>> docs = [Document(content=f"Doc {i}") for i in range(1000)]
        >>> for chunk_toon in stream_documents_to_toon(docs, chunk_size=100):
        ...     process_chunk(chunk_toon)  # Process 100 docs at a time
    """
    _check_haystack()

    try:
        encoder = ToonEncoder(options)

        for i in range(0, len(documents), chunk_size):
            chunk = documents[i:i + chunk_size]
            data_list = [_document_to_dict(doc, include_embeddings) for doc in chunk]
            yield encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to stream documents to TOON: {e}")


# =============================================================================
# ANSWER CONVERSION
# =============================================================================

def answers_to_toon(
    answers: List['Answer'],
    include_embeddings: bool = False,
    options: Optional[ToonEncodeOptions] = None
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
        return encoder.encode(data_list)

    except Exception as e:
        raise ConversionError(f"Failed to convert answers to TOON: {e}")


def toon_to_answers(
    toon_str: str,
    options: Optional[ToonDecodeOptions] = None
) -> List['Answer']:
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
            raise ConversionError("Expected TOON array format")

        return [_dict_to_answer(data) for data in data_list]

    except Exception as e:
        raise ConversionError(f"Failed to convert TOON to answers: {e}")


# =============================================================================
# METADATA OPERATIONS
# =============================================================================

def extract_metadata_to_toon(
    documents: List['Document'],
    options: Optional[ToonEncodeOptions] = None
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
        return encoder.encode(metadata_list)

    except Exception as e:
        raise ConversionError(f"Failed to extract metadata to TOON: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _document_to_dict(doc: 'Document', include_embeddings: bool = False) -> Dict[str, Any]:
    """Convert Haystack Document to dictionary."""
    data = {}

    # Add content
    if doc.content:
        data['content'] = doc.content

    # Add content type
    if doc.content_type:
        data['content_type'] = doc.content_type

    # Add ID
    if doc.id:
        data['id'] = doc.id

    # Add metadata
    if doc.meta:
        data['meta'] = dict(doc.meta)

    # Add score if present
    if hasattr(doc, 'score') and doc.score is not None:
        data['score'] = doc.score

    # Add embedding if requested
    if include_embeddings and hasattr(doc, 'embedding') and doc.embedding is not None:
        data['embedding'] = doc.embedding.tolist() if hasattr(doc.embedding, 'tolist') else list(doc.embedding)

    return data


def _dict_to_document(data: Dict[str, Any]) -> 'Document':
    """Convert dictionary to Haystack Document."""
    # Extract fields
    content = data.get('content', '')
    content_type = data.get('content_type', 'text')
    doc_id = data.get('id')
    meta = data.get('meta', {})
    score = data.get('score')
    embedding = data.get('embedding')

    # Create document
    doc = Document(
        content=content,
        content_type=content_type,
        id=doc_id,
        meta=meta,
        score=score,
        embedding=embedding
    )

    return doc


def _answer_to_dict(answer: 'Answer', include_embeddings: bool = False) -> Dict[str, Any]:
    """Convert Haystack Answer to dictionary."""
    data = {}

    # Add answer text
    if answer.answer:
        data['answer'] = answer.answer

    # Add type
    if answer.type:
        data['type'] = answer.type

    # Add score
    if answer.score is not None:
        data['score'] = answer.score

    # Add context
    if answer.context:
        data['context'] = answer.context

    # Add offsets
    if answer.offsets_in_document:
        data['offsets_in_document'] = [
            {'start': span.start, 'end': span.end}
            for span in answer.offsets_in_document
        ]

    if answer.offsets_in_context:
        data['offsets_in_context'] = [
            {'start': span.start, 'end': span.end}
            for span in answer.offsets_in_context
        ]

    # Add document ID
    if answer.document_id:
        data['document_id'] = answer.document_id

    # Add metadata
    if answer.meta:
        data['meta'] = dict(answer.meta)

    return data


def _dict_to_answer(data: Dict[str, Any]) -> 'Answer':
    """Convert dictionary to Haystack Answer."""
    # Extract fields
    answer_text = data.get('answer', '')
    answer_type = data.get('type', 'extractive')
    score = data.get('score')
    context = data.get('context')
    document_id = data.get('document_id')
    meta = data.get('meta', {})

    # Convert offsets
    offsets_in_document = None
    if 'offsets_in_document' in data:
        offsets_in_document = [
            Span(start=offset['start'], end=offset['end'])
            for offset in data['offsets_in_document']
        ]

    offsets_in_context = None
    if 'offsets_in_context' in data:
        offsets_in_context = [
            Span(start=offset['start'], end=offset['end'])
            for offset in data['offsets_in_context']
        ]

    # Create answer
    answer = Answer(
        answer=answer_text,
        type=answer_type,
        score=score,
        context=context,
        offsets_in_document=offsets_in_document,
        offsets_in_context=offsets_in_context,
        document_id=document_id,
        meta=meta
    )

    return answer


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "haystack_to_toon",
    "toon_to_haystack",
    "bulk_documents_to_toon",
    "bulk_toon_to_documents",
    "stream_documents_to_toon",
    "answers_to_toon",
    "toon_to_answers",
    "extract_metadata_to_toon",
]
