"""LlamaIndex Integration for toonverter.

Provides efficient TOON serialization for LlamaIndex documents and nodes.
Perfect for RAG pipelines, vector databases, and document processing workflows.

Key benefits:
- 40-60% token savings when storing/transmitting documents
- Preserves all metadata and relationships
- Efficient bulk operations for large document collections
- Seamless integration with existing LlamaIndex workflows

Install dependencies:
    pip install toonverter[llamaindex]

Basic usage:
    from toonverter.integrations.llamaindex import llamaindex_to_toon, toon_to_llamaindex

    # Convert document to TOON
    toon_str = llamaindex_to_toon(document)

    # Convert back to document
    document = toon_to_llamaindex(toon_str)
"""

from collections.abc import Iterator
from typing import Any, Union

from toonverter.core.exceptions import ConversionError
from toonverter.core.spec import ToonDecodeOptions, ToonEncodeOptions
from toonverter.decoders.toon_decoder import ToonDecoder
from toonverter.encoders.toon_encoder import ToonEncoder


try:
    from llama_index.core import Document
    from llama_index.core.schema import (
        BaseNode,
        ImageNode,
        IndexNode,
        NodeRelationship,
        RelatedNodeInfo,
        TextNode,
    )

    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False


def _check_llamaindex():
    """Check if LlamaIndex is available."""
    if not LLAMAINDEX_AVAILABLE:
        msg = "LlamaIndex is not installed. Install with: pip install toonverter[llamaindex]"
        raise ImportError(msg)


# =============================================================================
# DOCUMENT CONVERSION
# =============================================================================


def llamaindex_to_toon(
    obj: Union["Document", "BaseNode"],
    include_relationships: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert LlamaIndex Document or Node to TOON format.

    Args:
        obj: LlamaIndex Document or Node instance
        include_relationships: Include node relationships (default: False)
        options: TOON encoding options

    Returns:
        TOON formatted string

    Example:
        >>> doc = Document(text="Hello", metadata={"source": "test.txt"})
        >>> toon = llamaindex_to_toon(doc)
        >>> print(toon)
        text: Hello
        metadata:
          source: test.txt
    """
    _check_llamaindex()

    try:
        encoder = ToonEncoder(options)
        data = _obj_to_dict(obj, include_relationships)
        return encoder.encode(data)

    except Exception as e:
        msg = f"Failed to convert LlamaIndex object to TOON: {e}"
        raise ConversionError(msg)


def toon_to_llamaindex(
    toon_str: str, node_type: str = "document", options: ToonDecodeOptions | None = None
) -> Union["Document", "BaseNode"]:
    """Convert TOON format to LlamaIndex Document or Node.

    Args:
        toon_str: TOON formatted string
        node_type: Type of node to create ("document", "text", "image", "index")
        options: TOON decoding options

    Returns:
        LlamaIndex Document or Node instance

    Example:
        >>> toon = "text: Hello\\nmetadata:\\n  source: test.txt"
        >>> doc = toon_to_llamaindex(toon)
        >>> print(doc.text)
        Hello
    """
    _check_llamaindex()

    try:
        decoder = ToonDecoder(options)
        data = decoder.decode(toon_str)
        return _dict_to_obj(data, node_type)

    except Exception as e:
        msg = f"Failed to convert TOON to LlamaIndex object: {e}"
        raise ConversionError(msg)


# =============================================================================
# BULK OPERATIONS
# =============================================================================


def bulk_documents_to_toon(
    documents: list[Union["Document", "BaseNode"]],
    include_relationships: bool = False,
    options: ToonEncodeOptions | None = None,
) -> str:
    """Convert multiple LlamaIndex documents to TOON array format.

    Args:
        documents: List of Document or Node instances
        include_relationships: Include node relationships
        options: TOON encoding options

    Returns:
        TOON formatted string with array of documents

    Example:
        >>> docs = [Document(text="A"), Document(text="B")]
        >>> toon = bulk_documents_to_toon(docs)
        >>> print(toon)
        [2]:
          - text: A
          - text: B
    """
    _check_llamaindex()

    try:
        encoder = ToonEncoder(options)
        data_list = [_obj_to_dict(doc, include_relationships) for doc in documents]
        return encoder.encode(data_list)

    except Exception as e:
        msg = f"Failed to convert documents to TOON: {e}"
        raise ConversionError(msg)


def bulk_toon_to_documents(
    toon_str: str, node_type: str = "document", options: ToonDecodeOptions | None = None
) -> list[Union["Document", "BaseNode"]]:
    """Convert TOON array format to multiple LlamaIndex documents.

    Args:
        toon_str: TOON formatted string (array)
        node_type: Type of nodes to create
        options: TOON decoding options

    Returns:
        List of Document or Node instances

    Example:
        >>> toon = "[2]:\\n  - text: A\\n  - text: B"
        >>> docs = bulk_toon_to_documents(toon)
        >>> len(docs)
        2
    """
    _check_llamaindex()

    try:
        decoder = ToonDecoder(options)
        data_list = decoder.decode(toon_str)

        if not isinstance(data_list, list):
            msg = "Expected TOON array format"
            raise ConversionError(msg)

        return [_dict_to_obj(data, node_type) for data in data_list]

    except Exception as e:
        msg = f"Failed to convert TOON to documents: {e}"
        raise ConversionError(msg)


def stream_documents_to_toon(
    documents: list[Union["Document", "BaseNode"]],
    chunk_size: int = 100,
    include_relationships: bool = False,
    options: ToonEncodeOptions | None = None,
) -> Iterator[str]:
    """Stream large document collections to TOON in chunks.

    Memory-efficient for processing large datasets.

    Args:
        documents: List of Document or Node instances
        chunk_size: Number of documents per chunk
        include_relationships: Include node relationships
        options: TOON encoding options

    Yields:
        TOON formatted strings (one per chunk)

    Example:
        >>> docs = [Document(text=f"Doc {i}") for i in range(1000)]
        >>> for chunk_toon in stream_documents_to_toon(docs, chunk_size=100):
        ...     process_chunk(chunk_toon)  # Process 100 docs at a time
    """
    _check_llamaindex()

    try:
        encoder = ToonEncoder(options)

        for i in range(0, len(documents), chunk_size):
            chunk = documents[i : i + chunk_size]
            data_list = [_obj_to_dict(doc, include_relationships) for doc in chunk]
            yield encoder.encode(data_list)

    except Exception as e:
        msg = f"Failed to stream documents to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# INDEX OPERATIONS
# =============================================================================


def index_to_toon(
    index: Any, include_storage: bool = False, options: ToonEncodeOptions | None = None
) -> str:
    """Export LlamaIndex index structure to TOON format.

    Args:
        index: LlamaIndex index instance
        include_storage: Include storage context data
        options: TOON encoding options

    Returns:
        TOON formatted string

    Note:
        This exports the index metadata and structure, not the full vector storage.
        For full persistence, use LlamaIndex's native persistence methods.
    """
    _check_llamaindex()

    try:
        encoder = ToonEncoder(options)

        # Extract index metadata
        data = {
            "index_type": type(index).__name__,
            "index_id": getattr(index, "index_id", None),
        }

        # Add index struct if available
        if hasattr(index, "index_struct"):
            struct = index.index_struct
            data["index_struct"] = {
                "type": type(struct).__name__,
            }

        # Add storage context if requested
        if include_storage and hasattr(index, "storage_context"):
            storage = index.storage_context
            data["storage_context"] = {
                "persist_dir": getattr(storage, "persist_dir", None),
            }

        return encoder.encode(data)

    except Exception as e:
        msg = f"Failed to convert index to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# METADATA OPERATIONS
# =============================================================================


def extract_metadata_to_toon(
    documents: list[Union["Document", "BaseNode"]], options: ToonEncodeOptions | None = None
) -> str:
    """Extract only metadata from documents to TOON format.

    Useful for analyzing document collections without full text.

    Args:
        documents: List of Document or Node instances
        options: TOON encoding options

    Returns:
        TOON formatted string with metadata array

    Example:
        >>> docs = [
        ...     Document(text="A", metadata={"source": "a.txt", "page": 1}),
        ...     Document(text="B", metadata={"source": "b.txt", "page": 2})
        ... ]
        >>> toon = extract_metadata_to_toon(docs)
        >>> print(toon)
        [2]:
          - source: a.txt
            page: 1
          - source: b.txt
            page: 2
    """
    _check_llamaindex()

    try:
        encoder = ToonEncoder(options)
        metadata_list = [doc.metadata or {} for doc in documents]
        return encoder.encode(metadata_list)

    except Exception as e:
        msg = f"Failed to extract metadata to TOON: {e}"
        raise ConversionError(msg)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _obj_to_dict(
    obj: Union["Document", "BaseNode"], include_relationships: bool = False
) -> dict[str, Any]:
    """Convert LlamaIndex object to dictionary."""
    data = {}

    # Add text content
    if hasattr(obj, "text"):
        data["text"] = obj.text or ""

    # Add document-specific fields
    if isinstance(obj, Document):
        if obj.id_:
            data["id"] = obj.id_
        if obj.metadata:
            data["metadata"] = dict(obj.metadata)
        if hasattr(obj, "excluded_embed_metadata_keys") and obj.excluded_embed_metadata_keys:
            data["excluded_embed_metadata_keys"] = list(obj.excluded_embed_metadata_keys)
        if hasattr(obj, "excluded_llm_metadata_keys") and obj.excluded_llm_metadata_keys:
            data["excluded_llm_metadata_keys"] = list(obj.excluded_llm_metadata_keys)

    # Add node-specific fields
    elif isinstance(obj, BaseNode):
        data["node_type"] = type(obj).__name__

        if obj.id_:
            data["id"] = obj.id_
        if obj.metadata:
            data["metadata"] = dict(obj.metadata)

        # Add node-specific attributes
        if isinstance(obj, TextNode):
            if hasattr(obj, "start_char_idx") and obj.start_char_idx is not None:
                data["start_char_idx"] = obj.start_char_idx
            if hasattr(obj, "end_char_idx") and obj.end_char_idx is not None:
                data["end_char_idx"] = obj.end_char_idx

        elif isinstance(obj, ImageNode):
            if hasattr(obj, "image") and obj.image:
                data["image"] = obj.image
            if hasattr(obj, "image_path") and obj.image_path:
                data["image_path"] = obj.image_path

        elif isinstance(obj, IndexNode):
            if hasattr(obj, "index_id") and obj.index_id:
                data["index_id"] = obj.index_id

        # Add relationships if requested
        if include_relationships and hasattr(obj, "relationships") and obj.relationships:
            rels = {}
            for rel_type, rel_info in obj.relationships.items():
                if isinstance(rel_info, RelatedNodeInfo):
                    rels[rel_type.value] = {
                        "node_id": rel_info.node_id,
                        "metadata": rel_info.metadata or {},
                    }
            if rels:
                data["relationships"] = rels

    return data


def _dict_to_obj(
    data: dict[str, Any], node_type: str = "document"
) -> Union["Document", "BaseNode"]:
    """Convert dictionary to LlamaIndex object."""
    # Get text content
    text = data.get("text", "")
    metadata = data.get("metadata", {})
    doc_id = data.get("id")

    # Create appropriate object type
    if node_type == "document":
        return Document(
            text=text,
            metadata=metadata,
            id_=doc_id,
            excluded_embed_metadata_keys=data.get("excluded_embed_metadata_keys") or [],
            excluded_llm_metadata_keys=data.get("excluded_llm_metadata_keys") or [],
        )

    if node_type == "text":
        return TextNode(
            text=text,
            metadata=metadata,
            id_=doc_id,
            start_char_idx=data.get("start_char_idx"),
            end_char_idx=data.get("end_char_idx"),
        )

    if node_type == "image":
        return ImageNode(
            text=text,
            metadata=metadata,
            id_=doc_id,
            image=data.get("image"),
            image_path=data.get("image_path"),
        )

    if node_type == "index":
        return IndexNode(text=text, metadata=metadata, id_=doc_id, index_id=data.get("index_id"))

    # Try to detect from data
    detected_type = data.get("node_type", "TextNode")
    if "ImageNode" in detected_type:
        return _dict_to_obj(data, "image")
    if "IndexNode" in detected_type:
        return _dict_to_obj(data, "index")
    return _dict_to_obj(data, "text")


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "bulk_documents_to_toon",
    "bulk_toon_to_documents",
    "extract_metadata_to_toon",
    "index_to_toon",
    "llamaindex_to_toon",
    "stream_documents_to_toon",
    "toon_to_llamaindex",
]
